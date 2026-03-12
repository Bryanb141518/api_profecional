# 🎓 Sistema de Gestión Académica — API REST

API REST para la gestión académica de estudiantes universitarios. Permite administrar semestres, materias, notas, tareas y horarios con autenticación JWT.

---

## 🚀 Tecnologías

- **Backend:** Python 3.12 + Django 5 + Django REST Framework
- **Base de datos:** PostgreSQL
- **Autenticación:** JWT (SimpleJWT)
- **Documentación:** drf-spectacular (Swagger/OpenAPI)
- **Tests:** pytest-django + coverage (83% cobertura)

---

## 📋 Requisitos

- Python 3.10+
- PostgreSQL 14+
- pip

---

## ⚙️ Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/tu-repositorio.git
cd tu-repositorio/myproject
```

### 2. Crear entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
```env
SECRET_KEY=tu_secret_key_aqui
DEBUG=True
DB_NAME=users
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 5. Crear la base de datos
```bash
# En PostgreSQL, crear la base de datos:
CREATE DATABASE users;
```

### 6. Aplicar migraciones
```bash
python manage.py migrate
```

### 7. Correr el servidor
```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000`

---

## 📖 Documentación de la API

Una vez corriendo el servidor, accede a la documentación interactiva:

```
http://127.0.0.1:8000/api/docs/
```

---

## 🔑 Autenticación

La API usa JWT. Para autenticarte:

1. Regístrate en `POST /api/registro/`
2. Inicia sesión en `POST /api/login/` — recibirás un `access` token y un `refresh` token
3. Incluye el token en cada petición:
```
Authorization: Bearer <access_token>
```
4. Cuando el access token expire, renuévalo en `POST /api/token/refresh/`

---

## 📡 Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/registro/` | Registrar nuevo usuario |
| POST | `/api/login/` | Iniciar sesión |
| POST | `/api/logout/` | Cerrar sesión |
| POST | `/api/token/refresh/` | Renovar token |
| POST | `/api/tipo-estudiante/` | Seleccionar tipo (universidad/colegio) |
| POST | `/api/perfil-universitario/` | Crear perfil universitario |
| GET/PUT | `/api/perfil-universitario/detalle/` | Ver/editar perfil |
| GET/POST | `/api/semestres/` | Listar/crear semestres |
| GET/POST | `/api/semestres/<id>/materias/` | Listar/crear materias |
| GET/POST | `/api/materias/<id>/notas/` | Listar/crear notas |
| GET/POST | `/api/semestres/<id>/tareas/` | Listar/crear tareas |
| GET/POST | `/api/horario/` | Ver/crear horario semanal |

---

## 🧪 Tests

```bash
# Correr todos los tests
python manage.py test usuarios

# Correr con cobertura
coverage run manage.py test usuarios
coverage report
```

Cobertura actual: **83%** — 75 tests

---

## 🌐 Frontend

El frontend está incluido en la carpeta `front/` y es servido directamente por Django.

Flujo de navegación:
```
registro.html → seleccion.html → configuracion.html → dashboard.html
login.html → dashboard.html (si ya tiene perfil)
```

---

## 📁 Estructura del proyecto

```
myproject/
├── manage.py
├── .env                    # Variables de entorno (no incluido en git)
├── front/                  # Frontend HTML/CSS/JS
│   ├── registro.html
│   ├── login.html
│   ├── seleccion.html
│   ├── configuracion.html
│   └── dashboard.html
├── myproject/
│   ├── settings.py
│   └── urls.py
└── usuarios/
    ├── models.py           # Modelos de la BD
    ├── serializers.py      # Serializers DRF
    ├── views.py            # Vistas/endpoints
    ├── urls.py             # Rutas
    └── tests.py            # 75 tests
```

---

## 🔒 Seguridad

- Contraseñas hasheadas con PBKDF2
- Bloqueo de cuenta tras 5 intentos fallidos (30 minutos)
- Tokens JWT con expiración (access: 30 min, refresh: 7 días)
- Token blacklist al hacer logout
- Validaciones estrictas en registro (mayúsculas, números, caracteres especiales)

---

## 👤 Autor

Bryan Benitez — [GitHub](https://github.com/tu-usuario)