import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, status

from ..dependencies import CurrentUser, Database
from ..schemas import AdminBootstrapInput, LoginInput, RegisterInput
from ..security import PASSWORD_HASHER, create_access_token
from ..serializers import public_user
from ..settings import ACCESS_TOKEN_MINUTES, ADMIN_SETUP_KEY
from .users import insert_user

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/bootstrap-admin", status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: AdminBootstrapInput, database: Database) -> dict[str, Any]:
    if not ADMIN_SETUP_KEY or not secrets.compare_digest(payload.setup_key, ADMIN_SETUP_KEY):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "La clave de configuración no es válida.")
    if database["usuarios"].count_documents({"rol": "administrador"}, limit=1):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cuenta administradora.")
    return insert_user(database, payload, "administrador")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, database: Database) -> dict[str, Any]:
    return insert_user(database, payload, "usuario")


@router.post("/login")
def login(payload: LoginInput, database: Database) -> dict[str, Any]:
    user = database["usuarios"].find_one({"correo": payload.correo, "estado": "activo"})
    if user is None or not PASSWORD_HASHER.verify(payload.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos.")
    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_MINUTES * 60,
        "usuario": public_user(user),
    }


@router.get("/me")
def get_me(user: CurrentUser) -> dict[str, Any]:
    return {"usuario": public_user(user)}
