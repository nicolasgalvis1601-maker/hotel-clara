import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from pymongo import ReturnDocument

from ..database import Document
from ..dependencies import CurrentUser, Database
from ..schemas import ReservationInput

router = APIRouter(prefix="/api/reservations", tags=["Reservas"])

ReservationState = Literal["confirmada", "pendiente", "cancelada", "finalizada"]
MAX_PAGE_SIZE = 100
HTTP_422_UNPROCESSABLE_CONTENT = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


def earliest_local_today() -> date:
    """Fecha de "hoy" en la zona horaria más atrasada (UTC-12).

    El servidor (Render) trabaja en UTC. Desde las 7 p. m. en Colombia ya es el día
    siguiente en UTC, así que comparar con la fecha UTC rechazaba reservas para "hoy".
    """
    return (datetime.now(timezone.utc) - timedelta(hours=12)).date()


def reservation_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "La reserva no existe.")


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def stored_interval(reservation: Document) -> tuple[datetime, datetime] | None:
    """Intervalo de la reserva sin importar su estado (sirve para listar y filtrar)."""
    if reservation.get("modalidad", "noches") == "horario":
        start = reservation.get("inicio")
        end = reservation.get("fin")
        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        if isinstance(end, str):
            end = datetime.fromisoformat(end)
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            return None
        return as_utc(start), as_utc(end)

    entry = reservation.get("entrada")
    departure = reservation.get("salida")
    if isinstance(entry, str):
        entry = date.fromisoformat(entry)
    if isinstance(departure, str):
        departure = date.fromisoformat(departure)
    if not isinstance(entry, date) or not isinstance(departure, date):
        return None
    return (
        datetime.combine(entry, time.min, timezone.utc),
        datetime.combine(departure, time.min, timezone.utc),
    )


def reservation_interval(reservation: Document) -> tuple[datetime, datetime] | None:
    """Intervalo que bloquea disponibilidad. Las reservas canceladas liberan el horario."""
    if reservation.get("estado", "confirmada") == "cancelada":
        return None
    return stored_interval(reservation)


def effective_state(reservation: Document, now: datetime | None = None) -> str:
    """Estado mostrado al usuario: cancelada se respeta; si ya terminó, es finalizada."""
    stored = reservation.get("estado", "confirmada")
    if stored == "cancelada":
        return "cancelada"
    interval = stored_interval(reservation)
    if interval and interval[1] <= (now or datetime.now(timezone.utc)):
        return "finalizada"
    return stored


def requested_interval(payload: ReservationInput) -> tuple[datetime, datetime]:
    if payload.modalidad == "horario":
        assert payload.inicio is not None and payload.fin is not None
        return payload.inicio.astimezone(timezone.utc), payload.fin.astimezone(timezone.utc)
    assert payload.entrada is not None and payload.salida is not None
    return (
        datetime.combine(payload.entrada, time.min, timezone.utc),
        datetime.combine(payload.salida, time.min, timezone.utc),
    )


def ensure_available(
    database: Database, service_id: str, interval: tuple[datetime, datetime], ignore_id: str | None = None
) -> None:
    related_reservations = {"$or": [{"servicioId": service_id}, {"habitacionId": service_id}]}
    for existing in database["reservas"].find(related_reservations):
        if existing.get("id") == ignore_id:
            continue
        existing_interval = reservation_interval(existing)
        if existing_interval and interval[0] < existing_interval[1] and interval[1] > existing_interval[0]:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "El servicio ya está reservado en ese horario. Selecciona otra fecha u hora.",
            )


def iso(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def public_reservation(document: Document, now: datetime | None = None) -> dict[str, Any]:
    created = document.get("createdAt")
    if isinstance(created, datetime):
        created = as_utc(created)
    cancelled = document.get("canceladaEn")
    if isinstance(cancelled, datetime):
        cancelled = as_utc(cancelled)
    return {
        "id": document["id"],
        "servicioId": document["servicioId"],
        "habitacionId": document["servicioId"],
        "servicio": document["servicio"],
        "habitacion": document["servicio"],
        "correo": document["correo"],
        "modalidad": document.get("modalidad", "noches"),
        "entrada": iso(document.get("entrada")),
        "salida": iso(document.get("salida")),
        "inicio": iso(as_utc(document["inicio"]) if isinstance(document.get("inicio"), datetime) else document.get("inicio")),
        "fin": iso(as_utc(document["fin"]) if isinstance(document.get("fin"), datetime) else document.get("fin")),
        "huespedes": document.get("huespedes", 1),
        "observaciones": document.get("observaciones", ""),
        "total": document["total"],
        "estado": effective_state(document, now),
        "creadaEn": iso(created),
        "canceladaEn": iso(cancelled),
        "canceladaPor": document.get("canceladaPor"),
    }


def build_reservation(
    database: Database, payload: ReservationInput, user: Document, reservation_id: str
) -> Document:
    service = database["servicios"].find_one({"id": payload.servicioId})
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El servicio seleccionado no existe.")
    if service["estado"] != "disponible":
        raise HTTPException(status.HTTP_409_CONFLICT, "El servicio seleccionado está inactivo.")
    if payload.huespedes > service["capacidad"]:
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_CONTENT,
            f"El servicio admite como máximo {service['capacidad']} huésped(es).",
        )
    if payload.modalidad == "noches":
        assert payload.entrada is not None and payload.salida is not None
        nights = (payload.salida - payload.entrada).days
        if payload.entrada < earliest_local_today():
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_CONTENT, "La fecha de entrada no puede ser anterior a hoy."
            )
        if nights < service["duracion"]:
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_CONTENT,
                f"La estancia mínima es de {service['duracion']} noche(s).",
            )
        total = round(service["precio"] * nights, 2)
    else:
        assert payload.inicio is not None
        if payload.inicio.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise HTTPException(
                HTTP_422_UNPROCESSABLE_CONTENT, "La cita debe comenzar en una fecha y hora futuras."
            )
        total = round(service["precio"], 2)

    interval = requested_interval(payload)
    ensure_available(database, payload.servicioId, interval, ignore_id=reservation_id)
    return {
        "id": reservation_id,
        "servicioId": service["id"],
        "servicio": service["nombre"],
        "correo": user["correo"],
        "modalidad": payload.modalidad,
        "entrada": payload.entrada.isoformat() if payload.entrada else None,
        "salida": payload.salida.isoformat() if payload.salida else None,
        "inicio": payload.inicio.astimezone(timezone.utc) if payload.inicio else None,
        "fin": payload.fin.astimezone(timezone.utc) if payload.fin else None,
        "huespedes": payload.huespedes,
        "observaciones": payload.observaciones,
        "total": total,
        "estado": "confirmada",
        "createdAt": datetime.now(timezone.utc),
    }


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or "").lower())
    return "".join(character for character in text if unicodedata.category(character) != "Mn")


def matches_search(document: Document, search: str) -> bool:
    haystack = " ".join(
        normalize_text(document.get(field))
        for field in ("servicio", "id", "correo", "observaciones")
    )
    return all(term in haystack for term in normalize_text(search).split())


def local_dates(document: Document, offset: timedelta) -> tuple[date, date] | None:
    """Días (en la zona horaria del usuario) que ocupa la reserva."""
    if document.get("modalidad", "noches") == "horario":
        interval = stored_interval(document)
        if interval is None:
            return None
        return (interval[0] + offset).date(), (interval[1] + offset).date()
    interval = stored_interval(document)
    if interval is None:
        return None
    return interval[0].date(), interval[1].date()


def matches_dates(document: Document, since: date | None, until: date | None, offset: timedelta) -> bool:
    if since is None and until is None:
        return True
    days = local_dates(document, offset)
    if days is None:
        return False
    first, last = days
    if since is not None and last < since:
        return False
    if until is not None and first > until:
        return False
    return True


def sort_key(document: Document) -> tuple[datetime, str]:
    interval = stored_interval(document)
    start = interval[0] if interval else datetime.max.replace(tzinfo=timezone.utc)
    return start, str(document.get("id", ""))


def get_reservation_for(database: Database, reservation_id: str, user: Document, action: str) -> Document:
    reservation = database["reservas"].find_one({"id": reservation_id})
    if reservation is None:
        raise reservation_not_found()
    if user["rol"] != "administrador" and reservation["correo"] != user["correo"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"No tienes permiso para {action} esta reserva.")
    return reservation


@router.get("")
def list_reservations(
    user: CurrentUser,
    database: Database,
    q: str | None = Query(default=None, max_length=120, description="Busca por servicio, código, correo u observaciones."),
    estado: ReservationState | None = Query(default=None, description="confirmada, pendiente, cancelada o finalizada."),
    desde: date | None = Query(default=None, description="Reservas que terminan en esta fecha o después."),
    hasta: date | None = Query(default=None, description="Reservas que empiezan en esta fecha o antes."),
    utc_offset: int = Query(default=0, ge=-840, le=840, description="Minutos respecto a UTC del navegador (Bogotá = -300)."),
    skip: int = Query(default=0, ge=0),
    limit: int | None = Query(default=None, ge=1, le=MAX_PAGE_SIZE),
) -> dict[str, Any]:
    if desde and hasta and desde > hasta:
        raise HTTPException(
            HTTP_422_UNPROCESSABLE_CONTENT, "La fecha 'desde' no puede ser posterior a 'hasta'."
        )
    query = {} if user["rol"] == "administrador" else {"correo": user["correo"]}
    now = datetime.now(timezone.utc)
    offset = timedelta(minutes=utc_offset)
    search = (q or "").strip()
    documents = [
        document
        for document in database["reservas"].find(query)
        if (not search or matches_search(document, search))
        and (estado is None or effective_state(document, now) == estado)
        and matches_dates(document, desde, hasta, offset)
    ]
    documents.sort(key=sort_key)
    total = len(documents)
    page = documents[skip : skip + limit] if limit else documents[skip:]
    return {
        "items": [public_reservation(document, now) for document in page],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/availability")
def check_availability(
    user: CurrentUser,
    database: Database,
    servicio_id: str = Query(min_length=1, max_length=64),
    modalidad: Literal["noches", "horario"] = Query(),
    entrada: date | None = None,
    salida: date | None = None,
    inicio: datetime | None = None,
    fin: datetime | None = None,
) -> dict[str, bool]:
    del user
    try:
        payload = ReservationInput.model_validate(
            {
                "servicioId": servicio_id,
                "modalidad": modalidad,
                "entrada": entrada,
                "salida": salida,
                "inicio": inicio,
                "fin": fin,
            }
        )
    except ValidationError as error:
        # Sin esto, un rango de fechas inválido provocaba un error 500.
        raise RequestValidationError(error.errors(include_url=False)) from error
    service = database["servicios"].find_one({"id": servicio_id})
    if service is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El servicio seleccionado no existe.")
    if service["estado"] != "disponible":
        raise HTTPException(status.HTTP_409_CONFLICT, "El servicio seleccionado está inactivo.")
    ensure_available(database, servicio_id, requested_interval(payload))
    return {"disponible": True}


@router.get("/{reservation_id}")
def get_reservation(reservation_id: str, user: CurrentUser, database: Database) -> dict[str, Any]:
    reservation = get_reservation_for(database, reservation_id, user, "consultar")
    return {"reserva": public_reservation(reservation)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationInput, user: CurrentUser, database: Database
) -> dict[str, Any]:
    reservation = build_reservation(database, payload, user, str(uuid4()))
    database["reservas"].insert_one(reservation)
    return {"reserva": public_reservation(reservation)}


@router.put("/{reservation_id}")
def update_reservation(
    reservation_id: str,
    payload: ReservationInput,
    user: CurrentUser,
    database: Database,
) -> dict[str, Any]:
    existing = get_reservation_for(database, reservation_id, user, "editar")
    state = effective_state(existing)
    if state == "cancelada":
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede modificar una reserva cancelada.")
    if state == "finalizada":
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede modificar una reserva finalizada.")
    reservation = build_reservation(database, payload, user, reservation_id)
    reservation["correo"] = existing["correo"]
    reservation["estado"] = existing.get("estado", "confirmada")
    reservation["createdAt"] = existing.get("createdAt", datetime.now(timezone.utc))
    reservation["actualizadaEn"] = datetime.now(timezone.utc)
    updated = database["reservas"].find_one_and_update(
        {"id": reservation_id, "estado": {"$ne": "cancelada"}},
        {"$set": reservation},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva fue cancelada mientras la editabas.")
    return {"reserva": public_reservation(updated)}


@router.patch("/{reservation_id}/cancelar")
def cancel_reservation(reservation_id: str, user: CurrentUser, database: Database) -> dict[str, Any]:
    """Cancelación lógica: conserva la reserva en el historial y libera el horario."""
    existing = get_reservation_for(database, reservation_id, user, "cancelar")
    state = effective_state(existing)
    if state == "cancelada":
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva ya está cancelada.")
    if state == "finalizada":
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede cancelar una reserva finalizada.")
    updated = database["reservas"].find_one_and_update(
        {"id": reservation_id, "estado": {"$ne": "cancelada"}},
        {
            "$set": {
                "estado": "cancelada",
                "canceladaEn": datetime.now(timezone.utc),
                "canceladaPor": user["correo"],
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva ya está cancelada.")
    return {"reserva": public_reservation(updated)}


@router.delete("/{reservation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reservation(reservation_id: str, user: CurrentUser, database: Database) -> None:
    reservation = database["reservas"].find_one({"id": reservation_id})
    if reservation is None:
        raise reservation_not_found()
    if reservation["correo"] != user["correo"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo puedes eliminar tus propias reservas.")
    database["reservas"].delete_one({"id": reservation_id})


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_own_reservations(user: CurrentUser, database: Database) -> None:
    database["reservas"].delete_many({"correo": user["correo"]})
