# Acceso a Hotel Clara

No hay contraseñas de demostración ni cuentas compartidas en el código.
El acceso se valida contra la base de datos MongoDB del servidor.

## Primer administrador

1. Inicia MongoDB y configura/inicia la API siguiendo [README.md](./README.md).
2. Abre `http://localhost:8000/docs`.
3. Ejecuta `POST /api/auth/bootstrap-admin` una sola vez con nombre, correo,
   contraseña y el valor local de `ADMIN_SETUP_KEY` que está en `.env`.
4. Inicia sesión desde `http://localhost:8000/`.

La clave de configuración y las claves de firma JWT son secretos locales:
no se deben incluir en este documento, compartir ni subir a Git.
El endpoint de alta inicial rechaza nuevas altas cuando ya existe un
administrador.

## Usuarios y pruebas

Los clientes crean sus propias cuentas desde **Crear cuenta** y usan una
contraseña segura. Las pruebas automatizadas crean usuarios y reservas en una
base MongoDB temporal aislada, que se elimina al finalizar; no se proporcionan
cuentas de prueba persistentes.
