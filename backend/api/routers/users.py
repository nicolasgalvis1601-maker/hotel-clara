import re
from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query, status
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..database import Document, MongoDatabase
from ..dependencies import AdminUser, Database
from ..schemas import RegisterInput, Role, UserCreateInput, UserStatus, UserUpdateInput
from ..security import PASSWORD_HASHER
from ..serializers import public_user

router = APIRouter(prefix="/api/users", tags=["Usuarios"])

def email_taken() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya está registrado.")


def user_not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "El usuario no existe.")


def insert_user(database: MongoDatabase, payload: RegisterInput, rol: Role, estado: UserStatus = "activo") -> dict[str, Any]:
    document: Document = {
        "nombre": payload.nombre,
        "correo": payload.correo,
        "telefono": payload.telefono,
        "password_hash": PASSWORD_HASHER.hash(payload.password),
        "rol": rol,
        "estado": estado,
        "fechaRegistro": datetime.now(timezone.utc),
    }
    try:
        document["_id"] = database["usuarios"].insert_one(document).inserted_id
    except DuplicateKeyError as error:
        raise email_taken() from error
    return {"usuario": public_user(document)}


def find_user(database: MongoDatabase, user_id: str) -> Document:
    user = database["usuarios"].find_one({"_id": ObjectId(user_id)}) if ObjectId.is_valid(user_id) else None
    if user is None:
        raise user_not_found()
    return user


def is_active_admin(user: Document) -> bool:
    return user["rol"] == "administrador" and user["estado"] == "activo"


def is_last_active_admin(database: MongoDatabase, user: Document) -> bool:
    other_admins: Document = {"rol": "administrador", "estado": "activo", "_id": {"$ne": user["_id"]}}
    return is_active_admin(user) and database["usuarios"].count_documents(other_admins, limit=1) == 0


@router.get("")
def list_users(
    _admin: AdminUser,
    database: Database,
    q: str = Query(default="", max_length=120),
    rol: Role | None = Query(default=None),
    estado: UserStatus | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> dict[str, Any]:
    query: Document = {key: value for key, value in {"rol": rol, "estado": estado}.items() if value}
    if q.strip():
        pattern = {"$regex": re.escape(q.strip()), "$options": "i"}
        query["$or"] = [{"nombre": pattern}, {"correo": pattern}]
    users = database["usuarios"].find(query).sort("fechaRegistro").skip(skip).limit(limit)
    return {
        "items": [public_user(document) for document in users],
        "total": database["usuarios"].count_documents(query),
        "skip": skip,
        "limit": limit,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateInput, _admin: AdminUser, database: Database) -> dict[str, Any]:
    return insert_user(database, payload, payload.rol, payload.estado)


@router.put("/{user_id}")
def update_user(user_id: str, payload: UserUpdateInput, admin: AdminUser, database: Database) -> dict[str, Any]:
    existing = find_user(database, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(422, "Indica al menos un campo para actualizar.")
    if admin["_id"] == existing["_id"] and {"rol", "estado"} & changes.keys():
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes cambiar tu propio rol o estado.")
    if not is_active_admin(existing | changes) and is_last_active_admin(database, existing):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "No se puede desactivar ni cambiar el rol del último administrador activo.",
        )
    if "password" in changes:
        changes["password_hash"] = PASSWORD_HASHER.hash(changes.pop("password"))
    try:
        updated = database["usuarios"].find_one_and_update(
            {"_id": existing["_id"]}, {"$set": changes}, return_document=ReturnDocument.AFTER
        )
    except DuplicateKeyError as error:
        raise email_taken() from error
    if updated is None:
        raise user_not_found()
    return {"usuario": public_user(updated)}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: str, admin: AdminUser, database: Database) -> None:
    target = find_user(database, user_id)
    if admin["_id"] == target["_id"]:
        raise HTTPException(status.HTTP_409_CONFLICT, "No puedes eliminar tu propia cuenta.")
    if database["reservas"].count_documents(
        {"$or": [{"correo": target["correo"]}, {"usuarioId": user_id}]}, limit=1
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "La cuenta tiene reservas asociadas. Desactívala para conservar el historial.",
        )
    if is_last_active_admin(database, target):
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede eliminar al último administrador activo.")
    database["usuarios"].delete_one({"_id": target["_id"]})
