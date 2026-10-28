from typing import Annotated

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from .database import Document, MongoDatabase, get_database
from .security import read_token_subject

Database = Annotated[MongoDatabase, Depends(get_database)]
Credentials = Annotated[HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))]


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(credentials: Credentials, database: Database) -> Document:
    if credentials is None:
        raise unauthorized("Se requiere iniciar sesión.")
    try:
        user_id = ObjectId(read_token_subject(credentials.credentials))
    except (InvalidTokenError, InvalidId, KeyError, TypeError) as error:
        raise unauthorized("El token de acceso no es válido o ha expirado.") from error

    user = database["usuarios"].find_one({"_id": user_id})
    if user is None or user["estado"] != "activo":
        raise unauthorized("La cuenta no existe o está inactiva.")
    return user


CurrentUser = Annotated[Document, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> Document:
    if user["rol"] != "administrador":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Se requiere rol de administrador.")
    return user


AdminUser = Annotated[Document, Depends(require_admin)]
