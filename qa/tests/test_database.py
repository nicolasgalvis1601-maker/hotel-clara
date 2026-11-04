import unittest
from unittest.mock import MagicMock

from pymongo.errors import PyMongoError

from backend.api.database import DEFAULT_SERVICES, MongoDatabase, migrate_catalog_prices


class DefaultServicesTests(unittest.TestCase):
    def test_initial_catalog_has_ten_unique_services(self) -> None:
        self.assertEqual(len(DEFAULT_SERVICES), 10)
        self.assertEqual(len({service["id"] for service in DEFAULT_SERVICES}), 10)
        self.assertEqual(
            len({service["nombre_normalizado"] for service in DEFAULT_SERVICES}),
            10,
        )

    def test_initial_catalog_prices_are_colombian_pesos(self) -> None:
        self.assertEqual(
            {service["id"]: service["precio"] for service in DEFAULT_SERVICES},
            {
                "std": 89000, "dbl": 115000, "jr": 162000, "ste": 234000,
                "ind": 65000, "dlx": 148000, "fam": 178000, "exe": 195000,
                "acc": 105000, "pre": 320000,
            },
        )


class CatalogPriceMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = MagicMock(spec=MongoDatabase)
        self.settings = self.database["configuracion"]
        self.services = MagicMock()
        self.database.__getitem__.side_effect = lambda name: (
            self.settings if name == "configuracion" else self.services
        )
        self.settings.find_one.return_value = None

    def test_migration_only_updates_matching_original_prices(self) -> None:
        documents = [
            dict(DEFAULT_SERVICES[0], precio=890),
            dict(DEFAULT_SERVICES[1], precio=150000),
            dict(DEFAULT_SERVICES[2]),
            dict(DEFAULT_SERVICES[3], id="custom", precio=2340),
            dict(DEFAULT_SERVICES[4], nombre_normalizado="personalizada", precio=650),
        ]

        def update_one(query, update):
            for document in documents:
                if all(document.get(key) == value for key, value in query.items()):
                    document.update(update["$set"])
                    break

        self.services.update_one.side_effect = update_one
        migrate_catalog_prices(self.database)
        self.assertEqual(
            [document["precio"] for document in documents],
            [89000, 150000, 162000, 2340, 650],
        )
        self.assertEqual(self.services.update_one.call_count, 10)
        self.settings.update_one.assert_called_once_with(
            {"clave": "precios_catalogo_cop_v1"},
            {"$set": {"clave": "precios_catalogo_cop_v1"}},
            upsert=True,
        )

    def test_completed_migration_does_not_run_again(self) -> None:
        self.settings.find_one.return_value = {"clave": "precios_catalogo_cop_v1"}
        migrate_catalog_prices(self.database)
        self.services.update_one.assert_not_called()
        self.settings.update_one.assert_not_called()

    def test_failed_migration_is_not_marked_complete(self) -> None:
        self.services.update_one.side_effect = PyMongoError("test migration failure")
        with self.assertRaises(PyMongoError):
            migrate_catalog_prices(self.database)
        self.settings.update_one.assert_not_called()


if __name__ == "__main__":
    unittest.main()
