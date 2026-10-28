from typing import Any

from fastapi import APIRouter

from ..dependencies import CurrentUser, Database

router = APIRouter(prefix="/api", tags=["Estadísticas"])


@router.get("/stats")
def get_stats(user: CurrentUser, database: Database) -> dict[str, Any]:
    is_admin = user["rol"] == "administrador"
    reservation_query: dict[str, Any] = {} if is_admin else {"correo": user["correo"]}
    return {
        "usuarios": database["usuarios"].count_documents({}) if is_admin else None,
        "servicios": database["servicios"].count_documents({"estado": "disponible"}),
        "reservas": database["reservas"].count_documents(reservation_query),
    }
