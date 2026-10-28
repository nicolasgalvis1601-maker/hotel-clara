from typing import Any

from .database import Document


def public_user(document: Document) -> dict[str, Any]:
    return {
        "id": str(document["_id"]),
        "nombre": document["nombre"],
        "correo": document["correo"],
        "telefono": document.get("telefono", ""),
        "rol": document["rol"],
        "estado": document["estado"],
        "fechaRegistro": document["fechaRegistro"],
    }


def public_service(document: Document) -> dict[str, Any]:
    return {
        "id": document["id"],
        "nombre": document["nombre"],
        "detalle": document["detalle"],
        "precio": document["precio"],
        "duracion": document["duracion"],
        "capacidad": document["capacidad"],
        "categoria": document["categoria"],
        "estado": document["estado"],
        "imagen": document.get("imagen", ""),
    }
