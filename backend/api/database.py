import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

from .settings import JWT_SECRET, MONGODB_DATABASE, MONGODB_URI

Document = dict[str, Any]
MongoDatabase = Database[Document]

logger = logging.getLogger("uvicorn.error")

DEFAULT_SERVICES: tuple[Document, ...] = (
    {
        "id": "std",
        "nombre": "Habitación Estándar",
        "detalle": "Cama queen, escritorio y wifi de alta velocidad.",
        "precio": 890,
        "duracion": 1,
        "capacidad": 2,
        "categoria": "Habitación",
        "estado": "disponible",
        "imagen": "",
        "nombre_normalizado": "habitación estándar",
    },
    {
        "id": "dbl",
        "nombre": "Habitación Doble",
        "detalle": "Dos camas matrimoniales y vista a la ciudad.",
        "precio": 1150,
        "duracion": 1,
        "capacidad": 3,
        "categoria": "Habitación",
        "estado": "disponible",
        "imagen": "",
        "nombre_normalizado": "habitación doble",
    },
    {
        "id": "jr",
        "nombre": "Suite Junior",
        "detalle": "Sala independiente, terraza y desayuno incluido.",
        "precio": 1620,
        "duracion": 1,
        "capacidad": 4,
        "categoria": "Suite",
        "estado": "disponible",
        "imagen": "",
        "nombre_normalizado": "suite junior",
    },
    {
        "id": "ste",
        "nombre": "Suite Premium",
        "detalle": "Jacuzzi, servicio a la habitación 24 h y check-out tardío.",
        "precio": 2340,
        "duracion": 1,
        "capacidad": 4,
        "categoria": "Suite",
        "estado": "disponible",
        "imagen": "",
        "nombre_normalizado": "suite premium",
    },
)


def verificar_conexion(nombre_base_datos: str = MONGODB_DATABASE) -> bool:
    cliente: MongoClient[Document] = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        cliente.server_info()
        print("✅ Conexión exitosa a MongoDB")

        colecciones = cliente[nombre_base_datos].list_collection_names()
        print(f"📂 Colecciones en la base de datos '{nombre_base_datos}': {colecciones}")
        return True
    except ServerSelectionTimeoutError as err:
        print(f"❌ Error al conectar a MongoDB: {err}")
        print("Asegúrate de que el servicio de MongoDB esté encendido.")
        return False
    finally:
        cliente.close()
        print("🔌 Conexión cerrada.")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if len(JWT_SECRET) < 32:
        raise RuntimeError("Configura JWT_SECRET con al menos 32 caracteres en el archivo .env.")

    client: MongoClient[Document] = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        client.admin.command("ping")
        database = client[MONGODB_DATABASE]
        database["usuarios"].create_index("correo", unique=True)
        database["servicios"].create_index("nombre_normalizado", unique=True)
        database["reservas"].create_index("id", unique=True)
        database["reservas"].create_index([("servicioId", 1), ("estado", 1)])
        database["reservas"].create_index("correo")
        settings = database["configuracion"]
        if settings.find_one({"clave": "catalogo_inicial_creado"}) is None:
            if database["servicios"].count_documents({}) == 0:
                database["servicios"].insert_many(DEFAULT_SERVICES)
            settings.insert_one({"clave": "catalogo_inicial_creado"})
    except PyMongoError as error:
        client.close()
        raise RuntimeError(f"No se pudo conectar a MongoDB ({MONGODB_URI}): {error}") from error

    app.state.database = database
    logger.info("✅ Conexión exitosa a MongoDB. Base de datos: %s", MONGODB_DATABASE)
    try:
        yield
    finally:
        client.close()
        logger.info("Conexión con MongoDB cerrada.")


def get_database(request: Request) -> MongoDatabase:
    return request.app.state.database
