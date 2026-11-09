# API de Autenticación – AA5_EV01 (Construcción API)

**Aprendiz:** Alejandro Sepúlveda Ardila
**Programa:** Análisis y desarrollo de software – Ficha 3336915

API REST desarrollada con **Python + Flask + SQLite** que ofrece los servicios de registro e inicio de sesión de usuarios, además de consulta de perfil, cambio de contraseña y eliminación de cuenta.

## Estructura del proyecto

```
├── app.py                  # Código de la API (comentado)
├── test_api.py             # Pruebas automáticas (11 pruebas)
├── requirements.txt        # Dependencias
├── docs/API.md             # Documentación de cada servicio
├── openapi.yaml            # Especificación OpenAPI 3.0 de la API
├── ENLACE_REPOSITORIO.txt  # Enlace al repositorio en GitHub
└── .gitignore
```

## Instalación y ejecución

```bash
# 1. (Opcional) crear entorno virtual
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar la API
python app.py
```

La API queda disponible en `http://127.0.0.1:5000/api/v1`. La base de datos `usuarios.db` se crea automáticamente al iniciar.

## Servicios

| Método | Ruta | Descripción | Token |
|---|---|---|---|
| GET | `/api/v1/salud` | Estado del servicio | No |
| POST | `/api/v1/registro` | Registrar usuario | No |
| POST | `/api/v1/login` | Iniciar sesión | No |
| GET | `/api/v1/usuarios/me` | Consultar perfil | Sí |
| PUT | `/api/v1/usuarios/me/password` | Cambiar contraseña | Sí |
| DELETE | `/api/v1/usuarios/me` | Eliminar cuenta | Sí |

Documentación detallada de cada servicio (cuerpos, respuestas y ejemplos): [`docs/API.md`](docs/API.md).
Especificación formal: [`openapi.yaml`](openapi.yaml) (se puede abrir en https://editor.swagger.io).

## Pruebas

```bash
pytest -v
```

## Seguridad aplicada

- Contraseñas almacenadas como hash (no en texto plano).
- Token firmado con expiración de 1 hora.
- Mensaje de error genérico en el login para no revelar si falló el usuario o la contraseña.
- Consultas SQL parametrizadas (previene inyección SQL).
- La clave secreta se puede definir con la variable de entorno `SECRET_KEY`.

## Versionamiento

El proyecto se gestiona con **Git**. El enlace al repositorio remoto está en `ENLACE_REPOSITORIO.txt`.
