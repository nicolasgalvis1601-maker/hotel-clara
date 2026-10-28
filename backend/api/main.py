from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import lifespan
from .dependencies import Database
from .routers import auth, reservations, services, stats, users
from .settings import CORS_ORIGINS, MONGODB_DATABASE

app = FastAPI(
    title="Hotel Clara API",
    description="API para autenticación, administración y reservas de Hotel Clara.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

for module in (auth, stats, users, services, reservations):
    app.include_router(module.router)


@app.get("/health", tags=["Estado"])
def health(database: Database) -> dict[str, str]:
    database.command("ping")
    return {"status": "ok", "database": MONGODB_DATABASE}


PROJECT_ROOT = Path(__file__).resolve().parents[2]
app.mount("/", StaticFiles(directory=PROJECT_ROOT / "frontend", html=True), name="frontend")
