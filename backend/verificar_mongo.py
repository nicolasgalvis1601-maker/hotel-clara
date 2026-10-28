from backend.api.database import verificar_conexion

if __name__ == "__main__":
    raise SystemExit(0 if verificar_conexion() else 1)
