import re
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..database import Document
from ..dependencies import AdminUser, CurrentUser, Database
from ..schemas import ServiceInput, ServiceUpdateInput
from ..serializers import public_service

router = APIRouter(prefix="/api/services", tags=["Servicios"])


def name_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "Ya existe un servicio con ese nombre.")


def service_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "El servicio no existe.")


@router.get("")
def list_services(
    user: CurrentUser,
    database: Database,
    q: str = Query(default="", max_length=120),
    estado: str | None = Query(default=None, pattern="^(disponible|inactivo)$"),
) -> dict[str, Any]:
    query: Document = {}
    if user["rol"] != "administrador":
        query["estado"] = "disponible"
    elif estado:
        query["estado"] = estado
    if q.strip():
        pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"nombre": pattern}, {"detalle": pattern}, {"categoria": pattern}]
    documents = database["servicios"].find(query).sort("nombre")
    return {"items": [public_service(document) for document in documents]}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_service(payload: ServiceInput, _admin: AdminUser, database: Database) -> dict[str, Any]:
    document = payload.model_dump() | {"id": str(uuid.uuid4()), "nombre_normalizado": payload.nombre.casefold()}
    try:
        database["servicios"].insert_one(document)
    except DuplicateKeyError as error:
        raise name_taken() from error
    return {"servicio": public_service(document)}


@router.put("/{service_id}")
def update_service(
    service_id: str, payload: ServiceUpdateInput, _admin: AdminUser, database: Database
) -> dict[str, Any]:
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Indica al menos un campo para actualizar.")
    if "nombre" in changes:
        changes["nombre_normalizado"] = changes["nombre"].casefold()
    try:
        updated = database["servicios"].find_one_and_update(
            {"id": service_id}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as error:
        raise name_taken() from error
    if updated is None:
        raise service_not_found()
    return {"servicio": public_service(updated)}


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: str, _admin: AdminUser, database: Database) -> None:
    if database["reservas"].count_documents(
        {"$or": [{"servicioId": service_id}, {"habitacionId": service_id}]}, limit=1
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "El servicio tiene reservas asociadas. Desactívalo para conservar el historial.",
        )
    if database["servicios"].delete_one({"id": service_id}).deleted_count == 0:
        raise service_not_found()
