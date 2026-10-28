# Descomposición de Historias de Usuario en tareas — Sistema de Reservas

> ✅ indica que el requisito está implementado y verificado en el alcance indicado en la tarea. Una marca de frontend local no certifica la API; una marca de backend no implica que la interfaz está conectada a ella.

> Las marcas QA de la interfaz indican pruebas en navegador local. La API se verifica por separado con pruebas HTTP automatizadas y una prueba contra una base MongoDB temporal. Un requisito parcial, una integración pendiente o una prueba fallida queda sin check.

## Estado actual de integración

- El frontend de `frontend/` llama a la API para login/registro, dashboard, usuarios,
  servicios y reservas. El token es lo único de negocio que persiste en el
  navegador; cuentas, catálogo y reservas vienen de FastAPI/MongoDB.
- HUS-06 admite estancias por noches y citas con fecha/hora de inicio y fin.
  La API valida disponibilidad, permisos, servicio activo, capacidad y precio.
- Verificación actual: 26 pruebas HTTP/unitarias ejecutadas (25 aprobadas y 1
  integración omitida en la suite normal); la prueba de integración MongoDB
  temporal se ejecutó por separado y aprobó. Ambas usan datos aislados.
- Se probó la interfaz autenticada contra FastAPI y una base MongoDB temporal:
  registro/login, validaciones y roles de cliente/administrador; dashboard;
  CRUD de usuarios y servicios (incluida la persistencia de una imagen tras
  recargar); reservas por noches y por horario; disponibilidad y rechazo de
  solapamientos; búsqueda, filtros de estado/fecha, detalle, paginación,
  edición, cancelación y eliminación del historial.
- Se comprobó que no hubiera desbordamiento horizontal en acceso, registro,
  dashboard, reservas, usuarios y servicios a 320, 390, 768, 1024 y 1440 px.
  La prueba descubrió y corrigió un `ReferenceError` que impedía crear o editar
  usuarios desde la interfaz; también se añadieron indicadores y atributos
  accesibles para campos obligatorios y se corrigió la ayuda de carga de
  imágenes.
- El despliegue en GitHub Pages, otros navegadores/dispositivos y una auditoría
  completa de accesibilidad siguen sin verificarse. PR y code review quedan
  pendientes.

## Evidencia histórica de frontend local — 7 de octubre de 2026

- Login sin desbordamiento a 768 px ✅. También se verificaron registro, dashboard, reservas y usuarios a 320, 390, 768, 1024 y 1440 px.
- Dashboard con header, menú de cuenta, navegación, estadísticas locales, reservas recientes, estados y acciones rápidas ✅.
- Gestión de usuarios local con creación, edición por el administrador (nombre, correo, contraseña, rol y estado), eliminación confirmada, búsqueda, filtros y paginación de cinco registros ✅. El administrador no puede cambiar su propio rol/estado.
- La versión histórica usaba un administrador local de demostración; esa cuenta
  y contraseña ya no existen en la versión conectada a la API.
- Administrador puede consultar y editar reservas de todos los clientes ✅, conservando el propietario. Eliminar sigue limitado a las reservas propias.
- Clientes solo ven sus reservas y no acceden a Usuarios/Servicios administrativos ✅. Edición y eliminación de reservas ajenas rechazadas en la lógica del navegador.
- Administrador edita usuarios, puede cambiar su correo conservando la asociación de reservas, y crea cuentas desde el panel ✅.
- Usuarios inactivos no pueden iniciar sesión. No se permite autoeliminación ni cambiar el propio rol/estado. Una cuenta con reservas puede desactivarse, pero no eliminarse; editar el correo conserva sus reservas.
- Validación en navegador integrado mediante archivo local: CRUD, permisos visuales, validaciones, correo duplicado, filtros/paginación, persistencia, cuentas antiguas, error de almacenamiento simulado y edición desde el administrador de un usuario junto con sus reservas asociadas. Datos de prueba retirados. Diagnósticos del editor sin errores.
- Recorrido manual de regresión en navegador local: login válido/inválido, registro de dos clientes, reserva de ambas cuentas, aislamiento de datos, edición administrativa de usuarios y reservas, CRUD de servicios, validaciones y responsive en 320/390/768/1024/1440 px. No es ejecución de Playwright.
- No se ejecutó nuevamente la suite ni se probó GitHub Pages: los comandos quedaron bloqueados por la política de red local del sandbox en Windows. No se restauraron los archivos de pruebas eliminados en la copia de trabajo.

**Alcance histórico:** la versión descrita en esta sección era solo UI/UX y
frontend. Sus cuentas y datos en `localStorage` no son la fuente de datos actual.

## Acceso y criterio de los checks

No hay credenciales compartidas ni administrador de demostración. El primer
administrador se crea una vez con `POST /api/auth/bootstrap-admin` usando la
clave local `ADMIN_SETUP_KEY` en `.env`; los clientes se registran desde la
interfaz.

✅ marca únicamente lo implementado o probado en el alcance indicado.
Las pruebas locales de dashboard y CRUD de usuarios no certifican una API.
Las tareas de backend, BD, PR y funciones inexistentes quedan sin check.

## Resultado histórico de pruebas — 7 de octubre de 2026 (anterior a esta actualización)

Se ejecutaron **37 pruebas E2E en Chrome**, tanto con servidor local como contra
la página publicada en GitHub Pages. En cada ejecución: **35 aprobadas, 2 fallidas,
0 omitidas**, código de salida **1**. El resultado global **NO está aprobado**.

| Área comprobada | Resultado |
|---|---|
| Registro, teléfono opcional, campos inválidos, términos y correo duplicado | ✅ |
| Login correcto/incorrecto, bloqueo, expiración, recarga y cierre de sesión | ✅ |
| Crear reserva, total, persistencia, capacidad y prevención de solapamiento | ✅ |
| Consultar reservas propias y estados Próxima / En curso / Finalizada | ✅ |
| Editar habitación y fechas válidas, recalcular precio y descartar cambios | ✅ |
| Rechazar edición con fechas incompletas, orden incorrecto, exceso de huéspedes o habitación ocupada | ✅ |
| Rechazar edición con entrada en el pasado | Falló: permite guardar una fecha anterior a hoy |
| Eliminar con confirmación, abortar y liberar disponibilidad | ✅ (elimina el registro; no lo marca Cancelada) |
| Eliminar todas las reservas propias sin borrar las de otra cuenta | ✅ |
| Recursos, teléfono, teclado, colores de éxito/error y token de paleta informativa | ✅ |
| Login y reservas sin desbordamiento a 320, 390, 1024 y 1440 px | ✅ |
| Login sin desbordamiento a 768 px | Falló: el contenido ocupa 790 px; no se continuó con reservas a ese ancho |

En aquella ejecución, las pruebas estaban en `qa/tests/` y se repetían con `npm test`.
Los archivos de esa suite aparecen eliminados en la copia de trabajo actual.
El reporte
HTML queda en `playwright-report/index.html`, y los resultados JSON, capturas y
trazas de fallos en `test-results/`. Son archivos locales ignorados por Git.

**Límites de aquella ejecución:** no se verificaron otros navegadores, dispositivos físicos ni
conformidad completa de accesibilidad. No existían backend, MongoDB, CRUD
administrativo, buscador/filtros/paginación de reservas, modal de cancelación ni
estado Cancelada persistente. La sesión funciona solo en el navegador, no en un
servidor. Los colores de la paleta declarados en CSS no prueban que exista una
pantalla que utilice cada estado. No se cambiaron funcionalidades para ocultar
los dos fallos.

## Objetivo

Este documento descompone las 9 Historias de Usuario (HUS) del proyecto Full Stack en tareas de UI/UX, Frontend, Backend, Base de Datos, validaciones, pruebas y Git/GitHub.

> **Importante:** La responsabilidad asignada indica quién lidera la tarea durante el Sprint. No significa que solamente esa persona pueda ejecutarla. Los tres aprendices deben participar en el flujo de Git/GitHub.

---

# 1. HUS-01 — Inicio de sesión

**Historia de Usuario**

> Como usuario registrado, quiero iniciar sesión para acceder al sistema según mis permisos.

## Tareas

| ID | Tarea | Área | Responsable sugerido |
|---|---|---|---|
| T01 | Diseñar wireframe de la pantalla de Login ✅ | UI/UX | Frontend |
| T02 | Definir paleta de colores y tipografía ✅ | UI/UX | Frontend |
| T03 | Crear estructura HTML/React de Login ✅ | Frontend | Frontend |
| T04 | Diseñar formulario de usuario/correo y contraseña ✅ | UI/UX | Frontend |
| T05 | Implementar validaciones de campos obligatorios ✅ | Frontend | Frontend |
| T06 | Crear endpoint `POST /api/auth/login` ✅ | Backend | Backend |
| T07 | Validar credenciales en el servidor ✅ | Backend | Backend |
| T08 | Consultar usuario en MongoDB ✅ | Base de datos | Backend |
| T09 | Implementar manejo de sesión/token ✅ | Backend | Backend |
| T10 | Mostrar mensajes de error y éxito ✅ | Frontend | Frontend |
| T11 | Probar login exitoso ✅ | QA | Integración/DevOps |
| T12 | Probar credenciales incorrectas ✅ | QA | Integración/DevOps |
| T13 | Crear Pull Request | Git/GitHub | Todos |
| T14 | Realizar Code Review | Git/GitHub | Todos |

## UI/UX

### Paleta sugerida

| Elemento | Color |
|---|---|
| Azul principal | `#2563EB` ✅ |
| Azul oscuro | `#1E3A8A` ✅ |
| Fondo | `#F8FAFC` ✅ |
| Blanco | `#FFFFFF` ✅ |
| Éxito | `#16A34A` ✅ |
| Error | `#DC2626` ✅ |
| Texto | `#1E293B` ✅ |

### Elementos de pantalla

- Logo ✅
- Nombre de la aplicación ✅
- Campo de correo electrónico ✅
- Campo de contraseña ✅
- Mostrar/ocultar contraseña ✅
- Botón **Iniciar sesión** ✅
- Enlace **Registrarse** ✅
- Enlace **¿Olvidaste tu contraseña?**, si se implementa ✅
- Mensajes de validación ✅
- Mensajes de error ✅
- Diseño responsive ✅ (verificación actual en navegador local, incluido 768 px)

### Boceto conceptual

```text
┌─────────────────────────────────────┐
│              LOGO                   │
│       Sistema de Reservas           │
│                                     │
│       Correo electrónico            │
│       [____________________]        │
│                                     │
│       Contraseña                    │
│       [____________________] 👁      │
│                                     │
│       [     INICIAR SESIÓN     ]    │
│                                     │
│       ¿No tienes cuenta?            │
│          Registrarse                │
└─────────────────────────────────────┘
```

---

# 2. HUS-02 — Registro de usuario

**Historia de Usuario**

> Como visitante, quiero registrarme para poder utilizar el sistema.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar wireframe de Registro ✅ | UI/UX | Frontend |
| T02 | Definir campos del formulario ✅ | UI/UX | Frontend |
| T03 | Crear formulario ✅ | Frontend | Frontend |
| T04 | Validar nombre ✅ | Frontend | Frontend |
| T05 | Validar correo ✅ | Frontend | Frontend |
| T06 | Validar contraseña ✅ | Frontend | Frontend |
| T07 | Crear `POST /api/auth/register` ✅ | Backend | Backend |
| T08 | Verificar que el correo no exista ✅ | Backend | Backend |
| T09 | Crear modelo Usuario ✅ | Backend/BD | Backend |
| T10 | Guardar usuario en MongoDB ✅ | BD | Backend |
| T11 | Implementar protección de contraseña ✅ | Backend | Backend |
| T12 | Mostrar confirmación de registro ✅ | Frontend | Frontend |
| T13 | Probar registro válido ✅ | QA | Integración/DevOps |
| T14 | Probar correo duplicado ✅ | QA | Integración/DevOps |
| T15 | Crear PR y realizar revisión | Git/GitHub | Todos |

## UI/UX

### Elementos de pantalla

- Logo ✅
- Nombre de aplicación ✅
- Nombre completo ✅
- Correo electrónico ✅
- Teléfono ✅
- Contraseña ✅
- Confirmar contraseña ✅
- Botón **Registrarse** ✅
- Enlace **Volver al Login** ✅
- Mensajes de validación ✅
- Indicador de contraseña segura

### Recomendaciones

- Utilizar verde para confirmaciones. ✅
- Utilizar rojo para errores. ✅
- Utilizar azul para acciones principales (solo al pasar el cursor; el fondo normal es oscuro).
- Mantener etiquetas visibles. ✅
- Mostrar mensajes de validación debajo del campo correspondiente. ✅
- Indicar claramente los campos obligatorios.

---

# 3. HUS-03 — Dashboard

**Historia de Usuario**

> Como usuario autenticado, quiero visualizar un panel principal para consultar rápidamente el estado del sistema.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar estructura del Dashboard ✅ | UI/UX | Frontend |
| T02 | Diseñar menú de navegación ✅ | UI/UX | Frontend |
| T03 | Crear Header ✅ | Frontend | Frontend |
| T04 | Crear Sidebar/Navbar ✅ | Frontend | Frontend |
| T05 | Crear tarjetas estadísticas ✅ (datos de la API) | Frontend | Frontend |
| T06 | API: contar usuarios ✅ | Backend | Backend |
| T07 | API: contar servicios disponibles ✅ | Backend | Backend |
| T08 | API: contar reservas totales/propias ✅ (filtradas por rol) | Backend | Backend |
| T09 | Crear endpoint `GET /api/stats` ✅ | Backend | Backend |
| T10 | Integrar Dashboard con API | Frontend | Frontend |
| T11 | Implementar responsive ✅ | UI/UX | Frontend |
| T12 | Probar dashboard responsive y recorrido autenticado de cliente/administrador contra API ✅ | QA | Integración/DevOps |
| T13 | Crear PR | Git | Todos |

## Paleta sugerida

| Elemento | Color |
|---|---|
| Fondo | `#F1F5F9` |
| Navbar | `#1E3A8A` ✅ |
| Principal | `#2563EB` ✅ |
| Éxito | `#16A34A` ✅ |
| Advertencia | `#F59E0B` ✅ |
| Error | `#DC2626` ✅ |
| Texto | `#1E293B` ✅ |

## Elementos de pantalla

- Header ✅
- Logo ✅
- Nombre de usuario ✅
- Menú de usuario ✅
- Sidebar/Navbar ✅
- Dashboard ✅
- Tarjetas estadísticas desde la API
- Usuarios registrados ✅ (administrador)
- Servicios disponibles ✅ (servicios activos; disponibilidad por fechas en reservas)
- Reservas ✅ (propias para usuario; totales para administrador)
- Reservas recientes ✅
- Estados ✅
- Acciones rápidas ✅

---

# 4. HUS-04 — Gestión de usuarios

**Historia de Usuario**

> Como administrador, quiero gestionar usuarios para mantener actualizada la información del sistema.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar pantalla de usuarios ✅ | UI/UX | Frontend |
| T02 | Diseñar tabla de usuarios ✅ | UI/UX | Frontend |
| T03 | Diseñar botón Nuevo Usuario ✅ | UI/UX | Frontend |
| T04 | Crear formulario Usuario ✅ | Frontend | Frontend |
| T05 | Crear `GET /api/users` ✅ | Backend | Backend |
| T06 | Crear `POST /api/users` ✅ | Backend | Backend |
| T07 | Crear `PUT /api/users/:id` ✅ | Backend | Backend |
| T08 | Crear `DELETE /api/users/:id` ✅ | Backend | Backend |
| T09 | Crear modelo Usuario en MongoDB ✅ | BD | Backend |
| T10 | Implementar búsqueda en frontend conectada a `q` de la API | Frontend/Backend | Frontend |
| T11 | Implementar confirmación antes de eliminar ✅ | UI/UX | Frontend |
| T12 | Mostrar estados ✅ | UI/UX | Frontend |
| T13 | Probar CRUD ✅ (interfaz/API local y API con MongoDB temporal) | QA | Integración/DevOps |
| T14 | Resolver errores encontrados | Todos | Todos |

## Elementos de pantalla

- Título **Gestión de usuarios** ✅
- Botón `+ Nuevo usuario` ✅
- Buscador ✅
- Filtros ✅
- Tabla ✅
- Nombre ✅
- Correo ✅
- Rol ✅
- Estado ✅
- Fecha de registro ✅ (nuevos registros; cuentas antiguas sin fecha: No disponible)
- Acción Editar ✅
- Acción Eliminar ✅ (confirmación y protección del historial)
- Paginación ✅

## Colores de estado

| Estado | Color |
|---|---|
| Activo | `#16A34A` ✅ |
| Inactivo | `#DC2626` ✅ |
| Pendiente | `#F59E0B` ✅ (bloquea el inicio de sesión hasta que un administrador active la cuenta) |

El administrador puede crear o cambiar una cuenta a Pendiente; el registro público sigue creando cuentas Activas. No hay aprobación automática.

---

# 5. HUS-05 — Gestión de servicios

**Historia de Usuario**

> Como administrador, quiero gestionar los servicios disponibles para que puedan ser utilizados en las reservas.

**Interfaz:** el catálogo y sus imágenes se leen y guardan mediante la API.
**Backend:** el catálogo CRUD persiste en MongoDB y requiere autorización de
administrador. El precio y duración se configuran por noche; una reserva de
horario cobra el precio del servicio por cita. La capacidad se mantiene entre
1 y 4 huéspedes.

Los servicios inactivos no admiten nuevas reservas. Editar el catálogo no cambia
el nombre ni el total histórico de una reserva; al editar esa reserva se aplican
las condiciones actuales. Un servicio con reservas no se elimina: puede
desactivarse. La eliminación sin reservas requiere confirmación.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar pantalla de servicios ✅ | UI/UX | Frontend |
| T02 | Diseñar tarjetas/listado de servicios ✅ | UI/UX | Frontend |
| T03 | Diseñar formulario de servicio ✅ | UI/UX | Frontend |
| T04 | Crear CRUD de servicios ✅ | Backend | Backend |
| T05 | Crear modelo Servicio en MongoDB ✅ | BD | Backend |
| T06 | Crear endpoint GET ✅ | Backend | Backend |
| T07 | Crear endpoint POST ✅ | Backend | Backend |
| T08 | Crear endpoint PUT ✅ | Backend | Backend |
| T09 | Crear endpoint DELETE ✅ | Backend | Backend |
| T10 | Implementar búsqueda por nombre, descripción y categoría vía API | Frontend | Frontend |
| T11 | Implementar filtro por estado vía API | Frontend | Frontend |
| T12 | Validar precio/duración ✅ en frontend y backend | Frontend/Backend | Backend |
| T13 | Probar CRUD de API con MongoDB temporal e integración UI/API en navegador ✅ | QA | Integración/DevOps |
| T14 | Crear PR | Git | Todos |

### Funcionalidad disponible

- Crear, consultar, editar y eliminar servicios desde la API con rol de administrador.
- Persistir catálogo e imágenes en MongoDB.
- Confirmar eliminación, cancelar y cerrar con Escape ✅.
- Rechazar nombre duplicado, precio/duración/capacidad inválidos e imagen de tipo no permitido en backend.
- Integrar servicios activos con reservas, precio, capacidad y estancia mínima ✅.
- Conservar historial y bloquear eliminación de servicios con reservas ✅.
- Responsive del catálogo a 320, 390, 768, 1024 y 1440 px ✅; formulario a 320 y 768 px ✅.

El CRUD de la API, su persistencia en MongoDB temporal y los recorridos de
creación, edición, filtrado y eliminación en la interfaz se verificaron. También
se comprobó que una imagen PNG se conserva al recargar. GitHub Pages no se
verificó; PR y revisión siguen pendientes.

## Elementos

Cada servicio puede mostrarse como una tarjeta:

```text
┌──────────────────────────┐
│       🖼 Imagen          │
│                          │
│ Corte de cabello        │
│                          │
│ Duración: 45 min        │
│ Precio: $30.000         │
│ Estado: ● Disponible    │
│                          │
│ [Editar] [Eliminar]     │
└──────────────────────────┘
```

### Campos del servicio

- Nombre ✅
- Descripción ✅
- Precio ✅ (por noche)
- Duración ✅ (estancia mínima en noches)
- Imagen opcional ✅ (subida PNG/JPEG/WebP hasta 1 MB)
- Estado ✅ (Disponible / Inactivo)
- Categoría ✅
- Capacidad ✅ (huéspedes)

---

# 6. HUS-06 — Crear reserva

**Historia de Usuario**

> Como usuario, quiero crear una reserva seleccionando un servicio, fecha y hora disponibles.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar flujo de reserva ✅ | UI/UX | Frontend |
| T02 | Diseñar selector de servicio ✅ (tarjetas de habitaciones) | UI/UX | Frontend |
| T03 | Diseñar selector de fecha ✅ | UI/UX | Frontend |
| T04 | Diseñar selector de hora | UI/UX | Frontend |
| T05 | Crear formulario ✅ | Frontend | Frontend |
| T06 | Crear modelo Reserva en MongoDB ✅ | BD | Backend |
| T07 | Crear `POST /api/reservations` ✅ | Backend | Backend |
| T08 | Validar disponibilidad en backend ✅ | Backend | Backend |
| T09 | Evitar solapamientos en backend ✅ | Backend | Backend |
| T10 | Guardar y editar reservas en MongoDB ✅ | BD | Backend |
| T11 | Mostrar confirmación ✅ | Frontend | Frontend |
| T12 | Mostrar resumen antes de confirmar ✅ (disponibilidad, estancia y precio en las tarjetas) | UI/UX | Frontend |
| T13 | Probar reservas de noches y horario en API/MongoDB y en la interfaz ✅ | QA | Integración/DevOps |
| T14 | Probar intento de solapamiento en API y rechazo de disponibilidad en interfaz ✅ | QA | Integración/DevOps |

## Elementos

```text
Nueva reserva

Servicio
[ Seleccione un servicio ▼ ]

Fecha
[ 📅 10/09/2026 ]

Hora
[ 10:30 AM ▼ ]

Observaciones
[________________________]

Resumen
Servicio: Corte de cabello
Fecha: 10/09/2026
Hora: 10:30 AM
Valor: $30.000

[Cancelar] [Confirmar reserva]
```

## UI/UX

Se recomienda utilizar el siguiente flujo:

**Servicio → Fecha → Hora → Confirmación**

El usuario debe poder identificar fácilmente:

1. Qué servicio está reservando.
2. Para qué fecha.
3. A qué hora.
4. Cuánto cuesta, si aplica.
5. Qué debe confirmar.

---

# 7. HUS-07 — Consultar reservas

**Historia de Usuario**

> Como usuario, quiero consultar mis reservas para conocer las fechas, horarios y estados.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar pantalla Mis Reservas ✅ | UI/UX | Frontend |
| T02 | Diseñar tabla/listado ✅ | UI/UX | Frontend |
| T03 | Crear endpoint GET reservas ✅ (`GET /api/reservations` con `q`, `estado`, `desde`, `hasta`, `skip`, `limit`; `GET /api/reservations/:id`) | Backend | Backend |
| T04 | Filtrar reservas por usuario ✅ (en el servidor: el cliente solo recibe las suyas; el administrador, todas) | Backend | Backend |
| T05 | Mostrar estado de reserva ✅ (el servidor calcula Confirmada / Pendiente / Cancelada / Finalizada) | Frontend | Frontend |
| T06 | Crear filtros por fecha ✅ (Desde / Hasta, en la zona horaria del usuario) | Frontend | Frontend |
| T07 | Crear filtros por estado ✅ | Frontend | Frontend |
| T08 | Crear vista detalle ✅ (modal "Ver detalle" con datos frescos del servidor) | Frontend | Frontend |
| T09 | Implementar paginación ✅ (5 por página, en el servidor) | Frontend | Frontend |
| T10 | Probar consultas ✅ (`test_hus07_list_filters_search_pagination_and_detail` + E2E) | QA | Integración/DevOps |

## Elementos

- Título **Mis reservas** ✅ (**Todas las reservas** para administrador)
- Buscador ✅ (servicio, código, observaciones y correo; sin distinguir tildes ni mayúsculas)
- Filtro por fecha ✅
- Filtro por estado ✅
- Tabla/listado ✅
- Servicio (habitación) ✅
- Fecha ✅
- Hora ✅ (citas por horario; "No aplica" en estancias por noches)
- Usuario ✅ (visible para administrador)
- Estado ✅
- Acciones ✅ (Ver detalle, Editar, Cancelar reserva, Eliminar del historial)
- Vista detalle ✅

## Estados

| Estado | Color sugerido |
|---|---|
| Confirmada | Verde `#16A34A` ✅ |
| Pendiente | Amarillo `#F59E0B` ✅ (representado si la API devuelve este estado; no existe flujo de aprobación) |
| Cancelada | Rojo `#DC2626` ✅ |
| Finalizada | Gris/Azul ✅ (`#475569`) |

---

# 8. HUS-08 — Actualizar reserva

**Historia de Usuario**

> Como usuario, quiero modificar una reserva para cambiar su fecha, hora o servicio cuando sea necesario.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar botón Editar ✅ | UI/UX | Frontend |
| T02 | Diseñar formulario de edición ✅ | UI/UX | Frontend |
| T03 | Cargar datos existentes ✅ (incluye observaciones) | Frontend | Frontend |
| T04 | Crear `PUT /api/reservations/:id` ✅ | Backend | Backend |
| T05 | Validar nueva disponibilidad ✅ (frontend y backend; el backend responde 409) | Backend | Backend |
| T06 | Evitar modificación de reservas canceladas ✅ (también finalizadas; 409) | Backend | Backend |
| T07 | Actualizar MongoDB ✅ (guarda `actualizadaEn`) | BD | Backend |
| T08 | Mostrar confirmación ✅ | Frontend | Frontend |
| T09 | Mostrar errores ✅ | Frontend | Frontend |
| T10 | Probar actualización ✅ (`test_hus08_update_rules_conflicts_and_blocked_states` + E2E) | QA | Integración/DevOps |
| T11 | Probar horario no disponible ✅ (API y E2E: choque con reserva de otro cliente → 409) | QA | Integración/DevOps |

## Elementos

Formulario:

- Servicio (habitación) ✅
- Fecha ✅
- Hora ✅ (visible solo en reservas por horario)
- Observaciones ✅
- Estado, si corresponde ✅ (se muestra; se cambia solo con "Cancelar reserva")
- Botón **Guardar cambios** ✅
- Botón **Cancelar** ✅

### Confirmación ✅

Antes de guardar:

> ¿Está seguro de actualizar esta reserva?

Botones:

**Cancelar | Confirmar cambios**

---

# 9. HUS-09 — Cancelar reserva

**Historia de Usuario**

> Como usuario, quiero cancelar una reserva para liberar el horario seleccionado.

## Tareas

| ID | Tarea | Área | Responsable |
|---|---|---|---|
| T01 | Diseñar botón Cancelar ✅ ("Cancelar reserva" en cada tarjeta activa) | UI/UX | Frontend |
| T02 | Diseñar modal de confirmación ✅ | UI/UX | Frontend |
| T03 | Crear endpoint de cancelación ✅ (`PATCH /api/reservations/:id/cancelar`) | Backend | Backend |
| T04 | Validar propietario de reserva ✅ (propietario o administrador; otro cliente → 403) | Backend | Backend |
| T05 | Cambiar estado a cancelada ✅ (guarda `canceladaEn` y `canceladaPor`) | Backend | Backend |
| T06 | Liberar disponibilidad ✅ (las canceladas no bloquean el horario) | Backend | Backend |
| T07 | Actualizar listado ✅ | Frontend | Frontend |
| T08 | Mostrar mensaje de confirmación ✅ | Frontend | Frontend |
| T09 | Probar cancelación ✅ (`test_hus09_cancel_owner_state_availability_and_already_cancelled`, integración MongoDB y E2E) | QA | Integración/DevOps |
| T10 | Probar reserva ya cancelada ✅ (409 "La reserva ya está cancelada.") | QA | Integración/DevOps |
| T11 | Crear PR | Git/GitHub | Todos |

## Modal de confirmación

```text
┌─────────────────────────────────┐
│       ⚠ Cancelar reserva        │
│                                 │
│ ¿Está seguro de cancelar        │
│ esta reserva?                   │
│                                 │
│ Servicio: Corte de cabello      │
│ Fecha: 10/09/2026               │
│ Hora: 10:30 AM                  │
│                                 │
│ [No cancelar] [Sí, cancelar]   │
└─────────────────────────────────┘
```

<✅ Implementado en `#cancel-reservation-dialog`.

### Colores

- Acción destructiva: rojo `#DC2626`
- Cancelar proceso: gris `#64748B`
- Advertencia: amarillo `#F59E0B`

--->

# 10. Sistema visual general del proyecto

Para que los tres aprendices trabajen sobre una misma aplicación, se recomienda definir desde el Sprint 1 un pequeño **Design System**.

## Paleta general

| Uso | Color | Hex |
|---|---|---|
| Primario | Azul | `#2563EB` ✅ |
| Primario oscuro | Azul oscuro | `#1E3A8A` ✅ |
| Fondo | Gris claro | `#F8FAFC` ✅ |
| Superficie | Blanco | `#FFFFFF` ✅ |
| Texto principal | Gris oscuro | `#1E293B` ✅ |
| Texto secundario | Gris | `#64748B` ✅ |
| Éxito | Verde | `#16A34A` ✅ |
| Advertencia | Amarillo | `#F59E0B` ✅ |
| Error | Rojo | `#DC2626` ✅ |
| Información | Celeste | `#0284C7` ✅ |
| Bordes | Gris | `#CBD5E1` ✅ |

---

# 11. Elementos comunes en todas las pantallas

## Header

Debe contener:

- Logo/nombre de aplicación ✅
- Nombre de usuario ✅
- Avatar opcional
- Menú de usuario ✅
- Cerrar sesión ✅

## Menú lateral

Puede contener:

- 🏠 Dashboard ✅ (navbar)
- 👥 Usuarios ✅ (navbar; solo administrador)
- 🛠 Servicios ✅ (navbar; solo administrador)
- 📅 Reservas ✅ (navbar)
- 👤 Mi perfil
- 🚪 Cerrar sesión ✅ (menú de cuenta)

## Botones

Se recomienda mantener una convención uniforme:

| Acción | Color |
|---|---|
| Acción principal | Azul |
| Confirmar/activar | Verde |
| Advertencia | Amarillo |
| Eliminar/cancelar | Rojo ✅ |
| Cancelar/volver | Gris |

## Formularios

Todos deberían contemplar:

- Label ✅
- Input ✅
- Placeholder
- Validación ✅
- Mensaje de error ✅
- Indicador de campo obligatorio `*` y atributo `required` (incluidos acceso y registro)
- Botón Guardar ✅
- Botón Cancelar ✅

## Tablas

Las tablas deberían contemplar, cuando corresponda:

- Encabezados ✅ (tabla de usuarios)
- Datos ✅ (tabla de usuarios)
- Estado ✅
- Acciones ✅
- Búsqueda ✅ (usuarios y reservas)
- Filtros ✅ (rol/estado de usuarios; estado/fecha de reservas)
- Paginación ✅ (usuarios y reservas)
- Mensaje cuando no existan registros ✅

---

# 12. Responsabilidad de los tres aprendices

La responsabilidad debe rotarse durante los tres Sprint.

| Sprint | Aprendiz 1 | Aprendiz 2 | Aprendiz 3 |
|---|---|---|---|
| Sprint 1 | Frontend | Backend | Integración/DevOps |
| Sprint 2 | Backend | Integración/DevOps | Frontend |
| Sprint 3 | Integración/DevOps | Frontend | Backend |

## Regla fundamental

**Responsable ≠ único encargado.**

Los tres aprendices deben participar en el flujo completo:

```text
Issue
  ↓
Branch
  ↓
Desarrollo
  ↓
Commit
  ↓
Push
  ↓
Pull Request
  ↓
Code Review
  ↓
Pruebas
  ↓
GitHub Actions
  ↓
Merge
  ↓
Develop
  ↓
Main
```

---

# 13. Estructura recomendada en GitHub Projects

Cada HUS puede convertirse en una **Issue principal**, y las tareas en subtareas.

**Estado de este proyecto:** el [GitHub Project vinculado al repositorio](https://github.com/users/baez91876-ship-it/projects/2) tiene la vista de tablero **Flujo de tareas**, agrupada por `Status`, con los estados Backlog, Pendiente, En Desarrollo, Code Review, Pruebas y Finalizado, en ese orden. Se crearon **9 Issues principales y 116 subtareas**, tomando las tablas de las secciones 1 a 9 como fuente. Las 125 Issues están abiertas y en Backlog, y además están asignadas a las iteraciones siguientes. Se verificaron mediante la API de GitHub las relaciones nativas de subtareas, los enlaces de seguimiento, la iteración y el estado de cada Issue en el tablero. Los roles sugeridos no asignan automáticamente cuentas.

| Historia | Issue principal | Subtareas |
|---|---|---|
| HUS-01 — Inicio de sesión | [#6](https://github.com/baez91876-ship-it/Miercoles/issues/6) | 14 |
| HUS-02 — Registro de usuario | [#21](https://github.com/baez91876-ship-it/Miercoles/issues/21) | 15 |
| HUS-03 — Dashboard | [#37](https://github.com/baez91876-ship-it/Miercoles/issues/37) | 13 |
| HUS-04 — Gestión de usuarios | [#51](https://github.com/baez91876-ship-it/Miercoles/issues/51) | 14 |
| HUS-05 — Gestión de servicios | [#66](https://github.com/baez91876-ship-it/Miercoles/issues/66) | 14 |
| HUS-06 — Crear reserva | [#81](https://github.com/baez91876-ship-it/Miercoles/issues/81) | 14 |
| HUS-07 — Consultar reservas | [#96](https://github.com/baez91876-ship-it/Miercoles/issues/96) | 10 |
| HUS-08 — Actualizar reserva | [#107](https://github.com/baez91876-ship-it/Miercoles/issues/107) | 11 |
| HUS-09 — Cancelar reserva | [#119](https://github.com/baez91876-ship-it/Miercoles/issues/119) | 11 |

### Plan de tres sprints

Las iteraciones del Project comienzan en las fechas indicadas y usan duraciones de semanas completas, como requiere GitHub Projects. La fecha calculada de fin es exclusiva (el último día incluido es el día anterior). Las historias y sus subtareas permanecen juntas en el mismo sprint. HUS-06 se programa después de HUS-05: crear reservas depende del catálogo de servicios.

**Sincronización pendiente:** GitHub rechazó las mutaciones de Issues y de elementos del Project durante este ajuste. La distribución que sigue es el plan acordado; la vista del Project aún conserva HUS-06 en Sprint 2, por lo que no debe tomarse como actualizado hasta que se confirme allí.

| Sprint | Inicio y duración | Historias | Issues |
|---|---|---|---:|
| Sprint 1 | 16 sep 2026 · 1 semana (hasta el 22 sep) | HUS-01 Inicio de sesión, HUS-02 Registro de usuario, HUS-03 Dashboard | 45 |
| Sprint 2 | 30 sep 2026 · 2 semanas (hasta el 13 oct) | HUS-04 Gestión de usuarios, HUS-05 Gestión de servicios | 30 |
| Sprint 3 | 14 oct 2026 · 1 semana (hasta el 20 oct) | HUS-06 Crear reserva, HUS-07 Consultar reservas, HUS-08 Actualizar reserva, HUS-09 Cancelar reserva | 50 |

### Sprint 2 — Desarrollo e integración

**Objetivo:** ampliar el sistema y fortalecer la colaboración.

| Área | Alcance |
|---|---|
| Backend | CRUD de usuarios y/o servicios. |
| Frontend | Interfaces y consumo de API para usuarios y servicios. |
| Integración / DevOps | Seguimiento de PR, revisión, integración y resolución de conflictos. |

**Historias:** HUS-04 y HUS-05 ([#51](https://github.com/baez91876-ship-it/Miercoles/issues/51) y [#66](https://github.com/baez91876-ship-it/Miercoles/issues/66)). HUS-06 ([#81](https://github.com/baez91876-ship-it/Miercoles/issues/81)) se programa en Sprint 3, después de disponer del catálogo de servicios.

#### Flujo colaborativo y evidencia requerida

- [ ] Actualizar ramas con `git fetch` y `git pull`.
- [ ] Crear nuevas ramas `feature/*`.
- [ ] Realizar PR hacia `frontend` y/o `backend`.
- [ ] Solicitar y atender cambios de Code Review.
- [ ] Provocar y resolver al menos un conflicto; documentar las ramas y la resolución.
- [ ] Integrar cambios aprobados en `develop`.
- [ ] Actualizar GitHub Projects y enlazar PR, revisiones, conflicto resuelto e integración como evidencia.

Los puntos anteriores son criterios de seguimiento, no actividades declaradas como completadas. Actualizar sus checks únicamente al adjuntar evidencia verificable.

### Registro histórico: ejecución solo frontend (anterior a la integración)

En aquella ejecución, el alcance conservaba el modo local con `localStorage` y excluía el consumo de API. Después se implementó la integración documentada en el estado actual al inicio de este archivo. Se conserva este registro como evidencia histórica de la interfaz local previa; ya no describe el comportamiento actual.

Se corrigió la presentación móvil de la navegación en [frontend/styles.css](../frontend/styles.css): hasta 480 px, los cuatro accesos se distribuyen en dos columnas uniformes y la fila del usuario ocupa todo el ancho disponible. El flujo de usuarios y servicios se revisó a 320, 390, 768, 1024 y 1440 px sin desbordamiento horizontal del documento.

En la fecha de ese registro, la aplicación guardaba datos de negocio en `localStorage` y no tenía conexión a servidor. Las revisiones de PR, la resolución de conflictos y la integración a `develop` continúan pendientes; no se creó evidencia de colaboración que no haya ocurrido.

Las marcas de implementación local se conservaron como evidencia en las descripciones, no como cierre automático de tareas. La implementación frontend sí se confirmó en un commit y se subió a `main` ✅; se hizo directamente sobre `main`, sin Pull Request, Code Review ni GitHub Actions verificados. El ejemplo siguiente sigue siendo ilustrativo; las subtareas creadas usan los identificadores `HUS-XX-TXX` y las tareas de las tablas, no esta lista abreviada.

Ejemplo:

```text
HUS-06 - Crear reserva
│
├── TASK-01 Diseñar wireframe
├── TASK-02 Diseñar selector de servicio
├── TASK-03 Diseñar selector de fecha
├── TASK-04 Diseñar selector de hora
├── TASK-05 Crear formulario Frontend
├── TASK-06 Crear modelo Reserva
├── TASK-07 Crear endpoint POST
├── TASK-08 Validar disponibilidad
├── TASK-09 Guardar reserva
├── TASK-10 Integrar Frontend + Backend
├── TASK-11 Pruebas
├── TASK-12 Code Review
└── TASK-13 Integración
```

## Flujo de las tareas

```text
Backlog
   ↓
Pendiente
   ↓
En Desarrollo
   ↓
Code Review
   ↓
Pruebas
   ↓
Finalizado
```

---

# 14. Flujo pedagógico completo

La estructura recomendada para cada Historia de Usuario es:

```text
Historia de Usuario
        ↓
Criterios de aceptación
        ↓
Diseño UI/UX
        ↓
Tareas Frontend
        ↓
Tareas Backend
        ↓
Tareas Base de Datos
        ↓
Tareas de pruebas
        ↓
Issue
        ↓
Branch
        ↓
Commit
        ↓
Push
        ↓
Pull Request
        ↓
Code Review
        ↓
GitHub Actions
        ↓
Merge
        ↓
Finalizado
```
