# Documentación de los servicios – API de Autenticación v1

**URL base:** `http://127.0.0.1:5000/api/v1`
**Formato:** todas las peticiones y respuestas usan JSON (`Content-Type: application/json`).
**Autenticación:** los servicios protegidos requieren el encabezado `Authorization: Bearer <token>`. El token se obtiene en `/login` y dura 1 hora.

Todas las respuestas incluyen el campo `ok` (`true` / `false`) y un `mensaje`.

---

## 1. Verificar estado del servicio

| | |
|---|---|
| **Método y ruta** | `GET /salud` |
| **Autenticación** | No |
| **Descripción** | Confirma que la API está activa. |

**Respuesta 200**
```json
{ "ok": true, "mensaje": "Servicio activo" }
```

---

## 2. Registrar usuario

| | |
|---|---|
| **Método y ruta** | `POST /registro` |
| **Autenticación** | No |
| **Descripción** | Crea un usuario nuevo. La contraseña se almacena cifrada (hash), nunca en texto plano. |

**Cuerpo de la petición**

| Campo | Tipo | Reglas |
|---|---|---|
| `usuario` | string | 3 a 30 caracteres: letras, números, `.`, `-`, `_` |
| `correo` | string | Correo válido, único |
| `password` | string | Mínimo 8 caracteres, con letras y números |

```json
{ "usuario": "alejandro", "correo": "ale@correo.com", "password": "Clave1234" }
```

**Respuestas**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 201 | Registro exitoso | `{"ok": true, "mensaje": "Usuario registrado correctamente"}` |
| 400 | Datos inválidos | `{"ok": false, "mensaje": "<detalle del error>"}` |
| 409 | Usuario o correo ya existen | `{"ok": false, "mensaje": "El usuario o el correo ya están registrados"}` |

---

## 3. Iniciar sesión

| | |
|---|---|
| **Método y ruta** | `POST /login` |
| **Autenticación** | No |
| **Descripción** | Valida usuario y contraseña. Si son correctos devuelve un token. |

**Cuerpo de la petición**
```json
{ "usuario": "alejandro", "password": "Clave1234" }
```

**Respuestas**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Credenciales correctas | `{"ok": true, "mensaje": "Autenticación satisfactoria", "token": "...", "expira_en_segundos": 3600}` |
| 401 | Credenciales incorrectas | `{"ok": false, "mensaje": "Error en la autenticación"}` |

> El mensaje de error es el mismo si falla el usuario o la contraseña, para no revelar cuál de los dos es incorrecto.

---

## 4. Consultar perfil

| | |
|---|---|
| **Método y ruta** | `GET /usuarios/me` |
| **Autenticación** | Sí (Bearer token) |
| **Descripción** | Devuelve los datos del usuario autenticado (sin la contraseña). |

**Respuestas**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Token válido | `{"ok": true, "usuario": {"id": 1, "usuario": "alejandro", "correo": "ale@correo.com", "creado_en": "2026-11-08 21:30:00"}}` |
| 401 | Token ausente, inválido o expirado | `{"ok": false, "mensaje": "Token inválido"}` |

---

## 5. Cambiar contraseña

| | |
|---|---|
| **Método y ruta** | `PUT /usuarios/me/password` |
| **Autenticación** | Sí (Bearer token) |
| **Descripción** | Cambia la contraseña del usuario autenticado. |

**Cuerpo de la petición**
```json
{ "password_actual": "Clave1234", "password_nueva": "NuevaClave99" }
```

**Respuestas**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Cambio exitoso | `{"ok": true, "mensaje": "Contraseña actualizada correctamente"}` |
| 400 | La contraseña nueva no cumple las reglas | `{"ok": false, "mensaje": "..."}` |
| 401 | Contraseña actual incorrecta o token inválido | `{"ok": false, "mensaje": "La contraseña actual es incorrecta"}` |

---

## 6. Eliminar cuenta

| | |
|---|---|
| **Método y ruta** | `DELETE /usuarios/me` |
| **Autenticación** | Sí (Bearer token) |
| **Descripción** | Elimina definitivamente la cuenta del usuario autenticado. |

**Respuestas**

| Código | Cuándo | Cuerpo |
|---|---|---|
| 200 | Cuenta eliminada | `{"ok": true, "mensaje": "Cuenta eliminada correctamente"}` |
| 401 | Token inválido | `{"ok": false, "mensaje": "Token inválido"}` |

---

## Ejemplos con curl

```bash
# Registro
curl -X POST http://127.0.0.1:5000/api/v1/registro \
  -H "Content-Type: application/json" \
  -d '{"usuario":"alejandro","correo":"ale@correo.com","password":"Clave1234"}'

# Login
curl -X POST http://127.0.0.1:5000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"usuario":"alejandro","password":"Clave1234"}'

# Perfil (reemplazar TOKEN por el recibido en el login)
curl http://127.0.0.1:5000/api/v1/usuarios/me -H "Authorization: Bearer TOKEN"
```

## Códigos de estado usados

| Código | Significado |
|---|---|
| 200 | Operación exitosa |
| 201 | Recurso creado |
| 400 | Datos de entrada inválidos |
| 401 | No autenticado o credenciales incorrectas |
| 404 | Ruta no encontrada |
| 405 | Método HTTP no permitido |
| 409 | Conflicto (usuario o correo duplicado) |
