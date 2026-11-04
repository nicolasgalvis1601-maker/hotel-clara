import unittest

from backend.api.database import DEFAULT_SERVICES


class DefaultServicesTests(unittest.TestCase):
    def test_initial_catalog_has_ten_unique_services(self) -> None:
        self.assertEqual(len(DEFAULT_SERVICES), 10)
        self.assertEqual(len({service["id"] for service in DEFAULT_SERVICES}), 10)
        self.assertEqual(
            len({service["nombre_normalizado"] for service in DEFAULT_SERVICES}),
            10,
        )


if __name__ == "__main__":
    unittest.main()
