from __future__ import annotations

import os
import unittest
import uuid
from contextlib import ExitStack
from unittest.mock import patch

from fastapi.testclient import TestClient
from pymongo import MongoClient

from backend.api import database as database_module
from backend.api import main as main_module
from backend.api.main import app
from backend.api.settings import MONGODB_URI


@unittest.skipUnless(
    os.getenv("RUN_MONGO_INTEGRATION") == "1",
    "Activa RUN_MONGO_INTEGRATION=1 para probar MongoDB local.",
)
class MongoApiIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database_name = f"hotel_test_{uuid.uuid4().hex}"
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        self.patches.enter_context(
            patch.object(database_module, "MONGODB_DATABASE", self.database_name)
        )
        self.patches.enter_context(
            patch.object(main_module, "MONGODB_DATABASE", self.database_name)
        )
        self.patches.enter_context(
            patch.object(database_module, "JWT_SECRET", "test-only-secret-at-least-32-characters")
        )
        self.patches.enter_context(
            patch("backend.api.security.JWT_SECRET", "test-only-secret-at-least-32-characters")
        )
        self.patches.enter_context(
            patch("backend.api.routers.auth.ADMIN_SETUP_KEY", "test-bootstrap-key")
        )

        self.mongo = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        self.addCleanup(self.mongo.close)
        self.mongo.admin.command("ping")
        self.addCleanup(self.mongo.drop_database, self.database_name)

        self.client = TestClient(app)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_auth_dashboard_users_services_and_reservations_persist_in_mongodb(self) -> None:
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["database"], self.database_name)

        admin = self.client.post(
            "/api/auth/bootstrap-admin",
            json={
                "nombre": "Admin de integración",
                "correo": "admin@integration.example",
                "password": "StrongPass1!",
                "setup_key": "test-bootstrap-key",
            },
        )
        self.assertEqual(admin.status_code, 201)
        admin_login = self.client.post(
            "/api/auth/login",
            json={"correo": "admin@integration.example", "password": "StrongPass1!"},
        )
        self.assertEqual(admin_login.status_code, 200)
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        registration = self.client.post(
            "/api/auth/register",
            json={
                "nombre": "Cliente de integración",
                "correo": "client@integration.example",
                "password": "StrongPass1!",
            },
        )
        self.assertEqual(registration.status_code, 201)
        self.assertEqual(self.mongo[self.database_name]["usuarios"].count_documents({}), 2)
        client_login = self.client.post(
            "/api/auth/login",
            json={"correo": "client@integration.example", "password": "StrongPass1!"},
        )
        self.assertEqual(client_login.status_code, 200)
        client_headers = {"Authorization": "Bearer " + client_login.json()["access_token"]}

        reservation = self.client.post(
            "/api/reservations",
            headers=client_headers,
            json={
                "servicioId": "std",
                "modalidad": "noches",
                "entrada": "2099-04-10",
                "salida": "2099-04-12",
                "huespedes": 2,
                "observaciones": "Prueba de persistencia",
            },
        )
        self.assertEqual(reservation.status_code, 201)
        reservation_id = reservation.json()["reserva"]["id"]
        self.assertEqual(self.mongo[self.database_name]["reservas"].count_documents({}), 1)
        self.assertEqual(
            self.client.get("/api/reservations", headers=client_headers).json()["items"][0]["id"],
            reservation_id,
        )
        self.assertEqual(
            self.client.put(
                f"/api/reservations/{reservation_id}",
                headers=client_headers,
                json={
                    "servicioId": "std",
                    "modalidad": "noches",
                    "entrada": "2099-04-11",
                    "salida": "2099-04-13",
                    "huespedes": 2,
                    "observaciones": "Estancia editada",
                },
            ).status_code,
            200,
        )
        detail = self.client.get(f"/api/reservations/{reservation_id}", headers=client_headers)
        self.assertEqual(detail.json()["reserva"]["observaciones"], "Estancia editada")

        # HUS-09: la cancelación se guarda en MongoDB, conserva la reserva y libera el horario.
        cancelled = self.client.patch(
            f"/api/reservations/{reservation_id}/cancelar", headers=client_headers
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.json()["reserva"]["estado"], "cancelada")
        stored = self.mongo[self.database_name]["reservas"].find_one({"id": reservation_id})
        self.assertEqual(stored["estado"], "cancelada")
        self.assertIsNotNone(stored["canceladaEn"])
        self.assertEqual(
            self.client.patch(
                f"/api/reservations/{reservation_id}/cancelar", headers=client_headers
            ).status_code,
            409,
        )
        self.assertEqual(
            self.client.get(
                "/api/reservations", headers=client_headers, params={"estado": "cancelada"}
            ).json()["total"],
            1,
        )
        rebooked = self.client.post(
            "/api/reservations",
            headers=admin_headers,
            json={"servicioId": "std", "modalidad": "noches", "entrada": "2099-04-11", "salida": "2099-04-13"},
        )
        self.assertEqual(rebooked.status_code, 201)
        self.assertEqual(
            self.client.delete(
                f"/api/reservations/{rebooked.json()['reserva']['id']}", headers=admin_headers
            ).status_code,
            204,
        )

        self.assertEqual(
            self.client.delete(
                f"/api/reservations/{reservation_id}", headers=client_headers
            ).status_code,
            204,
        )
        self.assertEqual(self.mongo[self.database_name]["reservas"].count_documents({}), 0)

        user = self.client.post(
            "/api/users",
            headers=admin_headers,
            json={
                "nombre": "Usuario CRUD",
                "correo": "crud@integration.example",
                "password": "StrongPass1!",
            },
        )
        self.assertEqual(user.status_code, 201)
        user_id = user.json()["usuario"]["id"]
        self.assertEqual(
            self.client.put(
                f"/api/users/{user_id}",
                headers=admin_headers,
                json={"nombre": "Usuario actualizado"},
            ).json()["usuario"]["nombre"],
            "Usuario actualizado",
        )
        self.assertEqual(
            self.client.delete(f"/api/users/{user_id}", headers=admin_headers).status_code,
            204,
        )

        service = self.client.post(
            "/api/services",
            headers=admin_headers,
            json={
                "nombre": "Suite integración",
                "detalle": "Servicio persistido",
                "precio": 150,
                "duracion": 1,
                "capacidad": 2,
                "categoria": "Suite",
            },
        )
        self.assertEqual(service.status_code, 201)
        service_id = service.json()["servicio"]["id"]
        self.assertEqual(
            self.client.put(
                f"/api/services/{service_id}",
                headers=admin_headers,
                json={"precio": 175},
            ).json()["servicio"]["precio"],
            175,
        )
        self.assertEqual(
            self.client.delete(f"/api/services/{service_id}", headers=admin_headers).status_code,
            204,
        )
        self.assertEqual(self.mongo[self.database_name]["servicios"].count_documents({}), 4)


if __name__ == "__main__":
    unittest.main()
