"""Pruebas automáticas de la API. Ejecutar con: pytest -v"""
import os
import tempfile

import pytest

# Base de datos temporal para no tocar la real
_fd, _ruta = tempfile.mkstemp(suffix=".db")
os.close(_fd)
os.environ["DATABASE"] = _ruta

import app as modulo  # noqa: E402

BASE = "/api/v1"
USUARIO = {"usuario": "alejandro", "correo": "ale@correo.com", "password": "Clave1234"}


@pytest.fixture()
def cliente():
    os.remove(_ruta)
    modulo.init_db()
    modulo.app.config["TESTING"] = True
    with modulo.app.test_client() as c:
        yield c


def token_de(c):
    c.post(f"{BASE}/registro", json=USUARIO)
    r = c.post(f"{BASE}/login", json={"usuario": "alejandro", "password": "Clave1234"})
    return {"Authorization": f"Bearer {r.get_json()['token']}"}


def test_salud(cliente):
    assert cliente.get(f"{BASE}/salud").status_code == 200


def test_registro_ok(cliente):
    assert cliente.post(f"{BASE}/registro", json=USUARIO).status_code == 201


def test_registro_duplicado(cliente):
    cliente.post(f"{BASE}/registro", json=USUARIO)
    assert cliente.post(f"{BASE}/registro", json=USUARIO).status_code == 409


def test_registro_datos_invalidos(cliente):
    malo = dict(USUARIO, password="corta")
    assert cliente.post(f"{BASE}/registro", json=malo).status_code == 400
    malo = dict(USUARIO, correo="sin-arroba")
    assert cliente.post(f"{BASE}/registro", json=malo).status_code == 400


def test_login_satisfactorio(cliente):
    cliente.post(f"{BASE}/registro", json=USUARIO)
    r = cliente.post(f"{BASE}/login", json={"usuario": "alejandro", "password": "Clave1234"})
    assert r.status_code == 200
    assert r.get_json()["mensaje"] == "Autenticación satisfactoria"
    assert "token" in r.get_json()


def test_login_error(cliente):
    cliente.post(f"{BASE}/registro", json=USUARIO)
    r = cliente.post(f"{BASE}/login", json={"usuario": "alejandro", "password": "mala"})
    assert r.status_code == 401
    assert r.get_json()["mensaje"] == "Error en la autenticación"


def test_perfil_requiere_token(cliente):
    assert cliente.get(f"{BASE}/usuarios/me").status_code == 401


def test_perfil_con_token(cliente):
    r = cliente.get(f"{BASE}/usuarios/me", headers=token_de(cliente))
    assert r.status_code == 200
    assert r.get_json()["usuario"]["usuario"] == "alejandro"
    assert "password" not in str(r.get_json())


def test_cambiar_password(cliente):
    h = token_de(cliente)
    r = cliente.put(
        f"{BASE}/usuarios/me/password",
        json={"password_actual": "Clave1234", "password_nueva": "NuevaClave99"},
        headers=h,
    )
    assert r.status_code == 200
    ok = cliente.post(f"{BASE}/login", json={"usuario": "alejandro", "password": "NuevaClave99"})
    assert ok.status_code == 200


def test_cambiar_password_actual_incorrecta(cliente):
    r = cliente.put(
        f"{BASE}/usuarios/me/password",
        json={"password_actual": "otra", "password_nueva": "NuevaClave99"},
        headers=token_de(cliente),
    )
    assert r.status_code == 401


def test_eliminar_cuenta(cliente):
    h = token_de(cliente)
    assert cliente.delete(f"{BASE}/usuarios/me", headers=h).status_code == 200
    assert cliente.get(f"{BASE}/usuarios/me", headers=h).status_code == 401
