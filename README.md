# Hotel Clara — Sistema de reservas

Interfaz web y API REST en FastAPI para usuarios, catálogo de servicios y
reservas persistidas en MongoDB.

## Estructura del proyecto

- `backend/` — API FastAPI (`api/`), punto de entrada `app.py`, verificación de MongoDB y script de configuración local.
- `frontend/` — interfaz web (`index.html`, `script.js`, `styles.css`) servida por FastAPI.
- `ui-ux/` — historias de usuario, tareas y evidencias de diseño UI/UX.
- `qa/` — pruebas automatizadas (`tests/`) y credenciales/guía de prueba.

## Ejecutar localmente

Desde la raíz del proyecto puedes iniciar la página y la API juntas:

```powershell
python -m pip install -r requirements.txt
npm run dev
```

Requiere Node.js, Python y MongoDB en ejecución. No requiere `npm install`:
el lanzador no usa paquetes npm externos. Usa Python de `.venv` si existe o
`python` del PATH en caso contrario; instala las dependencias en ese mismo
intérprete. Si falta `.env`, crea uno con secretos aleatorios; si ya existe,
lo conserva. Un `.env` existente debe tener `JWT_SECRET` y `ADMIN_SETUP_KEY`
configurados. Abre `http://127.0.0.1:8000/`. La API se reinicia al cambiar
código Python; para ver cambios del frontend, recarga el navegador.
`Ctrl+C` detiene el servidor.

Para usar otro puerto: `npm run dev -- --port 8001`. El comando no inicia ni
instala MongoDB: usa la conexión configurada en `.env` y muestra un error si
no puede conectarse.

También puedes usar las tareas de VS Code:

1. Inicia MongoDB local (`mongodb://localhost:27017/`).
2. En VS Code ejecuta la tarea **Crear configuración local segura**. Crea
   `.env` con secretos aleatorios solo si aún no existe; no reemplaza una
   configuración existente. `.env` está excluido de Git.
3. Ejecuta la tarea **Iniciar API Hotel Clara**.
4. Abre `http://localhost:8000/`. La documentación de la API está en
   `http://localhost:8000/docs` y `http://localhost:8000/health` verifica la
   conexión a la base `hotel`.

Para crear el primer administrador, abre `/docs`, ejecuta
`POST /api/auth/bootstrap-admin` una sola vez y envía nombre, correo,
contraseña y el valor local de `ADMIN_SETUP_KEY` en `.env`. Después inicia
sesión desde la página. No hay cuenta ni contraseña de demostración.

Si no usas las tareas de VS Code, crea un entorno virtual e instala las
dependencias desde la raíz:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.app:app --reload
```

Antes de ejecutar el servidor manualmente, configura `JWT_SECRET` (mínimo 32
caracteres) y `ADMIN_SETUP_KEY` en `.env`. No compartas ni subas ese archivo.

## Funcionalidad

- Registro de clientes, login con JWT y sesión validada por el servidor.
- Dashboard con estadísticas y reservas recientes, limitado por el rol.
- CRUD administrativo de usuarios y servicios, con búsqueda, filtros,
  paginación y validaciones. La API protege roles e historial.
- Reservas de dos modalidades: alojamiento por noches o cita por horario con
  fecha y hora de inicio y fin. El servidor valida disponibilidad, capacidad,
  servicio activo, fechas y solapamientos; calcula el total según el precio
  actual del servicio.
- Clientes consultan sus reservas con buscador, filtros por estado y fecha,
  paginación y vista detalle. Los administradores consultan todas.
- Editar pide confirmación ("¿Está seguro de actualizar esta reserva?"). Las
  reservas canceladas o finalizadas no se pueden modificar.
- Cancelar es lógico: la reserva queda con estado `cancelada` en el historial
  y su horario se libera. Pueden cancelar el propietario o un administrador.
  Solo el propietario puede eliminar del historial una reserva cancelada o
  finalizada.
- Catálogo de diez habitaciones y suites sembrado una sola vez en una base
  nueva. No se vuelve a recrear si se elimina posteriormente.
- Precios en pesos colombianos (COP), con separador de miles y sin decimales:
  Estándar $89.000, Doble $115.000, Junior $162.000, Premium $234.000,
  Individual $65.000, Deluxe $148.000, Familiar $178.000, Ejecutiva $195.000,
  Accesible $105.000 y Presidencial $320.000 por noche. Al iniciar la API,
  una migración actualiza las tarifas originales del catálogo existente;
  no recrea servicios eliminados ni modifica tarifas personalizadas o los
  totales de reservas anteriores.

## Despliegue en Render

FastAPI entrega la página (`frontend/`) y la API desde el mismo servidor, así
que en Render basta **un solo servicio web**. `frontend/config.js` deja la URL
de la API vacía y el navegador llama a `/api/...` en el mismo dominio.

1. **Base de datos:** crea un clúster gratuito M0 en MongoDB Atlas, un usuario
   de base de datos y, en *Network Access*, permite `0.0.0.0/0` (Render no tiene
   IP fija en el plan gratuito). Copia la cadena `mongodb+srv://...`.
2. **Render:** *New → Blueprint* y elige este repositorio. Render lee
   `render.yaml`, pide `MONGODB_URI` y genera `JWT_SECRET` y `ADMIN_SETUP_KEY`.
3. **Primer administrador:** copia `ADMIN_SETUP_KEY` desde *Environment* del
   servicio, abre `https://<tu-servicio>.onrender.com/docs` y ejecuta
   `POST /api/auth/bootstrap-admin` una vez.

El plan gratuito se suspende tras 15 minutos sin visitas; la primera carga
después de eso tarda alrededor de un minuto.

**GitHub Pages (opcional):** Pages solo aloja archivos estáticos. El workflow
`Deploy GitHub Pages` se ejecuta a mano desde *Actions*. Si lo usas, pon la URL
de Render en `RENDER_API_URL` de `frontend/config.js` y agrega
`https://<usuario>.github.io` a `CORS_ORIGINS` en Render.

## Rutas principales

- Autenticación: `POST /api/auth/bootstrap-admin`, `/api/auth/register`,
  `/api/auth/login`, `GET /api/auth/me`.
- Dashboard: `GET /api/stats`.
- Usuarios: `GET`, `POST`, `PUT` y `DELETE /api/users`.
- Servicios: `GET`, `POST`, `PUT` y `DELETE /api/services`.
- Reservas: `GET`, `POST`, `PUT` y `DELETE /api/reservations`;
  `GET /api/reservations/availability`; `GET /api/reservations/{id}` (detalle);
  `PATCH /api/reservations/{id}/cancelar` (cancelación lógica).

`GET /api/reservations` acepta filtros opcionales: `q` (busca en servicio,
código, correo y observaciones), `estado` (`confirmada`, `pendiente`,
`cancelada`, `finalizada`), `desde` y `hasta` (AAAA-MM-DD), `utc_offset`
(minutos respecto a UTC del navegador, p. ej. `-300` en Bogotá) y paginación
con `skip` y `limit` (máx. 100). Devuelve `items` y `total`. Sin parámetros
devuelve todas las reservas visibles para el usuario.

Las operaciones administrativas requieren un token Bearer. Los endpoints
`GET /api/services` y `GET /api/reservations` aplican las reglas de acceso del
usuario autenticado.

## Pruebas

Instala las dependencias de desarrollo y ejecuta las pruebas unitarias y HTTP:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s qa/tests -v
```

Para probar persistencia real, en VS Code ejecuta **Probar API contra MongoDB
temporal**. La prueba usa una base `hotel_test_<id>` aislada y la elimina al
finalizar; no modifica `hotel`.

La tarea **Validar JavaScript del frontend** revisa la sintaxis del cliente.

`npm run check` valida la sintaxis JavaScript y `npm test` comprueba el
lanzador de desarrollo (selección de Python, argumentos, errores y cierre).
Las pruebas Python se ejecutan por separado con el comando anterior.
