from __future__ import annotations

import base64
import unittest

from pydantic import ValidationError

from backend.api.settings import MAX_IMAGE_SIZE_BYTES
from backend.api.schemas import (
    RegisterInput,
    ServiceInput,
    ServiceUpdateInput,
    UserUpdateInput,
    normalize_email,
    validate_image,
    validate_password,
)


class SchemaValidationTests(unittest.TestCase):
    def test_email_is_trimmed_and_case_normalized(self) -> None:
        self.assertEqual(normalize_email("  USER@Example.com "), "user@example.com")

    def test_password_policy_accepts_valid_password(self) -> None:
        valid_password = "".join(("Hotel", "Pass", "1", "!"))
        self.assertEqual(validate_password(valid_password), valid_password)

    def test_password_policy_rejects_weak_password(self) -> None:
        with self.assertRaises(ValueError):
            validate_password("weakpass")

    def test_register_accepts_frontend_field_aliases(self) -> None:
        valid_password = "".join(("Hotel", "Pass", "1", "!"))
        registration = RegisterInput(
            name="Hotel Guest",
            email="GUEST@example.com",
            phone="555-0100",
            password=valid_password,
        )
        self.assertEqual(registration.nombre, "Hotel Guest")
        self.assertEqual(registration.correo, "guest@example.com")
        self.assertEqual(registration.telefono, "555-0100")

    def test_user_update_rejects_explicit_null(self) -> None:
        with self.assertRaises(ValidationError):
            UserUpdateInput.model_validate({"correo": None})

    def test_service_update_rejects_explicit_null_price(self) -> None:
        with self.assertRaises(ValidationError):
            ServiceUpdateInput.model_validate({"precio": None})

    def test_service_update_allows_clearing_optional_image(self) -> None:
        update = ServiceUpdateInput.model_validate({"imagen": None})
        self.assertIsNone(update.imagen)

    def test_image_requires_content_matching_declared_mime_type(self) -> None:
        misleading_image = "data:image/png;base64," + base64.b64encode(b"not a png").decode("ascii")
        with self.assertRaises(ValueError):
            validate_image(misleading_image)

    def test_image_accepts_png_signature(self) -> None:
        png_header = b"\x89PNG\r\n\x1a\n"
        image = "data:image/png;base64," + base64.b64encode(png_header).decode("ascii")
        self.assertEqual(validate_image(image), image)

    def test_image_enforces_one_megabyte_decoded_limit(self) -> None:
        image_data = b"\x89PNG\r\n\x1a\n" + b"x" * (MAX_IMAGE_SIZE_BYTES + 1 - 8)
        image = "data:image/png;base64," + base64.b64encode(image_data).decode("ascii")
        with self.assertRaises(ValueError):
            validate_image(image)

    def test_service_rejects_image_with_mismatched_content(self) -> None:
        misleading_image = "data:image/webp;base64," + base64.b64encode(b"not a webp").decode("ascii")
        with self.assertRaises(ValidationError):
            ServiceInput.model_validate(
                {
                    "nombre": "Suite",
                    "detalle": "Habitación amplia",
                    "precio": 100,
                    "duracion": 1,
                    "capacidad": 2,
                    "categoria": "Suite",
                    "imagen": misleading_image,
                }
            )


if __name__ == "__main__":
    unittest.main()
