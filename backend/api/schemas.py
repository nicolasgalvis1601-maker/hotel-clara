import base64
import binascii
import re
from datetime import date, datetime
from typing import Annotated, Any, ClassVar, Literal, cast

from pydantic import AfterValidator, AliasChoices, BaseModel, ConfigDict, Field, model_validator

from .settings import MAX_IMAGE_LENGTH, MAX_IMAGE_SIZE_BYTES

EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
IMAGE_PATTERN = re.compile(r"data:image/(png|jpeg|webp);base64,([A-Za-z0-9+/]+={0,2})")


def validate_password(password: str) -> str:
    if (
        len(password) < 8
        or not re.search(r"[a-z]", password)
        or not re.search(r"[A-Z]", password)
        or not re.search(r"\d", password)
        or not re.search(r"[^A-Za-z\d]", password)
    ):
        raise ValueError("La contraseña debe tener al menos 8 caracteres, mayúscula, minúscula, número y símbolo.")
    return password


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Introduce un correo electrónico válido.")
    return email


def required_text(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("Este campo no puede estar vacío.")
    return text


def validate_image(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) > MAX_IMAGE_LENGTH:
        raise ValueError("La imagen debe ocupar como máximo 1 MB.")
    match = IMAGE_PATTERN.fullmatch(value)
    if not match:
        raise ValueError("La imagen debe ser PNG, JPEG o WebP en formato base64.")
    try:
        data = base64.b64decode(match.group(2), validate=True)
    except binascii.Error as error:
        raise ValueError("La imagen base64 no es válida.") from error
    if len(data) > MAX_IMAGE_SIZE_BYTES:
        raise ValueError("La imagen debe ocupar como máximo 1 MB.")
    signature_matches = {
        "png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "jpeg": data.startswith(b"\xff\xd8\xff"),
        "webp": data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    }
    if not signature_matches[match.group(1)]:
        raise ValueError("El contenido de la imagen no coincide con su formato.")
    return value


Name = Annotated[str, Field(max_length=120), AfterValidator(required_text)]
Email = Annotated[str, Field(max_length=254), AfterValidator(normalize_email)]
Password = Annotated[str, Field(max_length=256), AfterValidator(validate_password)]
Phone = Annotated[str, Field(max_length=40)]
Role = Literal["administrador", "usuario"]
UserStatus = Literal["activo", "inactivo", "pendiente"]
Detail = Annotated[str, Field(max_length=1000), AfterValidator(required_text)]
Category = Annotated[str, Field(max_length=80), AfterValidator(required_text)]
Price = Annotated[float, Field(gt=0, le=1_000_000)]
Duration = Annotated[int, Field(ge=1, le=365)]
Capacity = Annotated[int, Field(ge=1, le=4)]
ServiceStatus = Literal["disponible", "inactivo"]
Image = Annotated[str | None, AfterValidator(validate_image)]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateModel(APIModel):
    """Actualización parcial: los campos enviados no pueden ser null salvo los indicados."""

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="before")
    @classmethod
    def reject_null_values(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        values = cast(dict[str, Any], data)
        null_fields = [
            key for key, value in values.items() if value is None and key not in cls.nullable_fields
        ]
        if null_fields:
            raise ValueError(f"Los campos enviados no pueden ser null: {', '.join(null_fields)}.")
        return values


class RegisterInput(APIModel):
    nombre: Name = Field(validation_alias=AliasChoices("nombre", "name"))
    correo: Email = Field(validation_alias=AliasChoices("correo", "email"))
    telefono: Phone = Field(default="", validation_alias=AliasChoices("telefono", "phone"))
    password: Password


class LoginInput(APIModel):
    correo: Email = Field(validation_alias=AliasChoices("correo", "email"))
    password: str = Field(min_length=1, max_length=256)


class AdminBootstrapInput(RegisterInput):
    setup_key: str = Field(min_length=1, max_length=256)


class UserCreateInput(RegisterInput):
    rol: Role = "usuario"
    estado: UserStatus = "activo"


class UserUpdateInput(UpdateModel):
    nombre: Name | None = None
    correo: Email | None = None
    telefono: Phone | None = None
    password: Password | None = None
    rol: Role | None = None
    estado: UserStatus | None = None


class ServiceInput(APIModel):
    nombre: Name
    detalle: Detail
    precio: Price
    duracion: Duration
    capacidad: Capacity
    categoria: Category
    estado: ServiceStatus = "disponible"
    imagen: Image = ""


class ServiceUpdateInput(UpdateModel):
    nullable_fields = frozenset({"imagen"})

    nombre: Name | None = None
    detalle: Detail | None = None
    precio: Price | None = None
    duracion: Duration | None = None
    capacidad: Capacity | None = None
    categoria: Category | None = None
    estado: ServiceStatus | None = None
    imagen: Image = None


class ReservationInput(APIModel):
    servicioId: str = Field(min_length=1, max_length=64)
    modalidad: Literal["noches", "horario"]
    entrada: date | None = None
    salida: date | None = None
    inicio: datetime | None = None
    fin: datetime | None = None
    huespedes: Annotated[int, Field(ge=1, le=4)] = 1
    observaciones: Annotated[str, Field(max_length=1000)] = ""

    @model_validator(mode="after")
    def validate_schedule(self) -> "ReservationInput":
        if self.modalidad == "noches":
            if self.entrada is None or self.salida is None:
                raise ValueError("Indica las fechas de entrada y salida.")
            if self.entrada >= self.salida:
                raise ValueError("La salida debe ser posterior a la entrada.")
            if self.inicio is not None or self.fin is not None:
                raise ValueError("Una reserva por noches no acepta horas.")
        else:
            if self.inicio is None or self.fin is None:
                raise ValueError("Indica la hora de inicio y fin de la cita.")
            if self.inicio.tzinfo is None or self.fin.tzinfo is None:
                raise ValueError("Las horas de la cita deben incluir zona horaria.")
            if self.inicio >= self.fin:
                raise ValueError("La hora de fin debe ser posterior al inicio.")
            if self.entrada is not None or self.salida is not None:
                raise ValueError("Una cita por horario no acepta fechas de alojamiento.")
        if self.observaciones != self.observaciones.strip():
            self.observaciones = self.observaciones.strip()
        return self
