"""
API REST de autenticación de usuarios (AA5_EV01 - Construcción API)
Autor: Alejandro Sepúlveda Ardila
Tecnologías: Python 3 + Flask + SQLite

Servicios (versión 1):
    GET    /api/v1/salud                 -> Verifica que el servicio esté activo
    POST   /api/v1/registro              -> Registra un usuario nuevo
    POST   /api/v1/login                 -> Inicia sesión (usuario + contraseña)
    GET    /api/v1/usuarios/me           -> Consulta el perfil (requiere token)
    PUT    /api/v1/usuarios/me/password  -> Cambia la contraseña (requiere token)
    DELETE /api/v1/usuarios/me           -> Elimina la cuenta (requiere token)
"""
import os
import re
import sqlite3
from functools import wraps

from flask import Flask, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["DATABASE"] = os.environ.get("DATABASE", "usuarios.db")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")
app.config["TOKEN_MAX_AGE"] = 3600  # el token dura 1 hora (en segundos)
app.config["JSON_AS_ASCII"] = False  # permite tildes y ñ en las respuestas

PREFIJO = "/api/v1"
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


# ---------------------------------------------------------------------------
# Base de datos (SQLite)
# ---------------------------------------------------------------------------
def get_db():
    """Devuelve la conexión a la base de datos de la petición actual."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def cerrar_db(_error):
    """Cierra la conexión al terminar la petición."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea la tabla de usuarios si todavía no existe."""
    db = sqlite3.connect(app.config["DATABASE"])
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            correo TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def serializador():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="auth-token")


def generar_token(usuario_id):
    """Crea un token firmado con el id del usuario."""
    return serializador().dumps({"id": usuario_id})


def error(mensaje, codigo):
    """Respuesta de error uniforme en formato JSON."""
    return jsonify({"ok": False, "mensaje": mensaje}), codigo


def token_requerido(f):
    """Decorador: exige el encabezado 'Authorization: Bearer <token>'."""

    @wraps(f)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return error("Falta el token de autenticación", 401)
        try:
            datos = serializador().loads(
                cabecera[7:], max_age=app.config["TOKEN_MAX_AGE"]
            )
        except SignatureExpired:
            return error("El token ha expirado", 401)
        except BadSignature:
            return error("Token inválido", 401)

        usuario = get_db().execute(
            "SELECT * FROM usuarios WHERE id = ?", (datos["id"],)
        ).fetchone()
        if usuario is None:
            return error("El usuario ya no existe", 401)
        g.usuario = usuario
        return f(*args, **kwargs)

    return envoltura


def password_valida(password):
    """Mínimo 8 caracteres, con al menos una letra y un número."""
    return (
        isinstance(password, str)
        and len(password) >= 8
        and re.search(r"[A-Za-z]", password)
        and re.search(r"\d", password)
    )


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------
@app.get(f"{PREFIJO}/salud")
def salud():
    """Servicio de verificación: indica que la API está funcionando."""
    return jsonify({"ok": True, "mensaje": "Servicio activo"}), 200


@app.post(f"{PREFIJO}/registro")
def registro():
    """Registra un usuario nuevo. Cuerpo JSON: usuario, correo, password."""
    datos = request.get_json(silent=True) or {}
    usuario = (datos.get("usuario") or "").strip()
    correo = (datos.get("correo") or "").strip().lower()
    password = datos.get("password")

    # Validaciones de entrada
    if not PATRON_USUARIO.match(usuario):
        return error(
            "El usuario debe tener entre 3 y 30 caracteres "
            "(letras, números, punto, guion o guion bajo)",
            400,
        )
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", correo):
        return error("El correo electrónico no es válido", 400)
    if not password_valida(password):
        return error(
            "La contraseña debe tener mínimo 8 caracteres, con letras y números", 400
        )

    # La contraseña NUNCA se guarda en texto plano: se guarda su hash
    try:
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (usuario, correo, password_hash) VALUES (?, ?, ?)",
            (usuario, correo, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return error("El usuario o el correo ya están registrados", 409)

    return jsonify({"ok": True, "mensaje": "Usuario registrado correctamente"}), 201


@app.post(f"{PREFIJO}/login")
def login():
    """Inicia sesión. Cuerpo JSON: usuario, password."""
    datos = request.get_json(silent=True) or {}
    usuario = (datos.get("usuario") or "").strip()
    password = datos.get("password") or ""

    fila = get_db().execute(
        "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
    ).fetchone()

    # Mismo mensaje si falla el usuario o la contraseña (no revela cuál falló)
    if fila is None or not check_password_hash(fila["password_hash"], password):
        return error("Error en la autenticación", 401)

    return (
        jsonify(
            {
                "ok": True,
                "mensaje": "Autenticación satisfactoria",
                "token": generar_token(fila["id"]),
                "expira_en_segundos": app.config["TOKEN_MAX_AGE"],
            }
        ),
        200,
    )


@app.get(f"{PREFIJO}/usuarios/me")
@token_requerido
def perfil():
    """Devuelve los datos del usuario autenticado (sin la contraseña)."""
    u = g.usuario
    return (
        jsonify(
            {
                "ok": True,
                "usuario": {
                    "id": u["id"],
                    "usuario": u["usuario"],
                    "correo": u["correo"],
                    "creado_en": u["creado_en"],
                },
            }
        ),
        200,
    )


@app.put(f"{PREFIJO}/usuarios/me/password")
@token_requerido
def cambiar_password():
    """Cambia la contraseña. Cuerpo JSON: password_actual, password_nueva."""
    datos = request.get_json(silent=True) or {}
    actual = datos.get("password_actual") or ""
    nueva = datos.get("password_nueva")

    if not check_password_hash(g.usuario["password_hash"], actual):
        return error("La contraseña actual es incorrecta", 401)
    if not password_valida(nueva):
        return error(
            "La contraseña nueva debe tener mínimo 8 caracteres, con letras y números",
            400,
        )

    db = get_db()
    db.execute(
        "UPDATE usuarios SET password_hash = ? WHERE id = ?",
        (generate_password_hash(nueva), g.usuario["id"]),
    )
    db.commit()
    return jsonify({"ok": True, "mensaje": "Contraseña actualizada correctamente"}), 200


@app.delete(f"{PREFIJO}/usuarios/me")
@token_requerido
def eliminar_cuenta():
    """Elimina la cuenta del usuario autenticado."""
    db = get_db()
    db.execute("DELETE FROM usuarios WHERE id = ?", (g.usuario["id"],))
    db.commit()
    return jsonify({"ok": True, "mensaje": "Cuenta eliminada correctamente"}), 200


# Respuestas JSON para errores generales
@app.errorhandler(404)
def no_encontrado(_e):
    return error("Ruta no encontrada", 404)


@app.errorhandler(405)
def metodo_no_permitido(_e):
    return error("Método HTTP no permitido en esta ruta", 405)


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------
init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
