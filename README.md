# DocManager Drive

Sistema de gestión documental con integración a Google Drive, desarrollado con FastAPI, PostgreSQL y Docker.

## 🚀 Características

- ✅ **Autenticación Multi-Usuario**: Sistema JWT con roles (Usuario, Admin, Superadmin)
- ✅ **Integración Google Drive**: Soporte para Service Account y OAuth
- ✅ **Multi-Tenant**: Múltiples admins pueden gestionar sus propios usuarios y archivos
- ✅ **Upload/Download**: Subida y descarga de archivos a Google Drive
- ✅ **Comentarios**: Sistema de comentarios con historial completo
- ✅ **Docker**: Completamente dockerizado para fácil despliegue
- ✅ **API REST**: Documentación automática con OpenAPI/Swagger
- ✅ **Frontend Simple**: Interfaz HTML/JS sin frameworks

## 📋 Requisitos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- PostgreSQL 15+ (incluido en Docker)
- Cuenta de Google Cloud Platform

## 🏗️ Arquitectura

```
docmanager-drive/
├── backend/              # API FastAPI
│   ├── app/
│   │   ├── routers/     # Endpoints REST
│   │   ├── models.py    # Modelos SQLAlchemy
│   │   ├── schemas.py   # Schemas Pydantic
│   │   ├── auth.py      # Autenticación JWT
│   │   ├── google_drive.py  # Integración Drive
│   │   └── scripts/     # Scripts de utilidad
│   ├── alembic/         # Migraciones de DB
│   └── tests/           # Tests con pytest
├── frontend/            # Frontend HTML/JS
├── infra/nginx/         # Configuración Nginx
└── pgdata/             # Datos PostgreSQL (persistente)
```

## 🔧 Configuración Local

### Opción 1: Quick Start (Recomendado para Windows)

```powershell
# Inicio rápido automático
.\quick-start.ps1
```

Este script hace todo automáticamente:
- Verifica Docker
- Crea y configura .env
- Inicia servicios
- Ejecuta migraciones
- Crea superadmin

### Opción 2: Script Completo de Desarrollo

```powershell
# Primera vez (con todas las opciones)
.\start-local.ps1

# Reconstruir imágenes
.\start-local.ps1 -Build

# Ver logs en tiempo real
.\start-local.ps1 -Logs

# Reiniciar servicios
.\start-local.ps1 -Restart

# Reset completo (elimina datos)
.\start-local.ps1 -Reset

# Detener servicios
.\start-local.ps1 -Stop
```

### Opción 3: Detener y Limpiar

```powershell
# Detener manteniendo datos
.\stop-clean.ps1 -KeepData

# Detener y eliminar todos los datos
.\stop-clean.ps1
```

### Opción 4: Manual (Linux/Mac o Windows WSL)

#### 1. Clonar y configurar

```bash
git clone <repository>
cd docmanager-drive
cp .env.example .env
```

#### 2. Configurar variables de entorno

Edita el archivo `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/docmanager
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=docmanager

# JWT
JWT_SECRET=tu-clave-secreta-muy-segura
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# Encryption (generar con el comando abajo)
ENCRYPTION_KEY=tu-clave-fernet-aqui

# Superadmin
SUPERADMIN_EMAIL=admin@tudominio.com
SUPERADMIN_PASSWORD=CambiarEsto123!

# Google Drive (opcional, se puede configurar por admin)
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret
```

#### 3. Generar clave de encriptación

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copia el resultado en `ENCRYPTION_KEY` del archivo `.env`.

#### 4. Iniciar servicios

```bash
docker compose up -d
```

#### 5. Ejecutar migraciones

```bash
docker compose exec web alembic upgrade head
```

#### 6. Crear superadmin

```bash
docker compose exec web python app/scripts/create_superadmin.py
```

### 📱 Acceder a la Aplicación

- **Frontend**: http://localhost
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## 🔑 Configuración de Google Drive

### Opción 1: Service Account (Recomendado para producción)

1. Ir a [Google Cloud Console](https://console.cloud.google.com)
2. Crear un proyecto nuevo o seleccionar uno existente
3. Habilitar Google Drive API
4. Crear Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Descargar JSON key
5. Compartir carpeta de Drive con el email del Service Account
6. En el panel de Admin, pegar el contenido del JSON en "Service Account JSON"

### Opción 2: OAuth (Recomendado para desarrollo)

1. En Google Cloud Console, crear OAuth 2.0 Client ID
2. Configurar redirect URI: `http://localhost`
3. Obtener refresh token usando OAuth Playground:
   - Ir a https://developers.google.com/oauthplayground
   - Configurar OAuth 2.0 con tu Client ID y Secret
   - Autorizar Google Drive API v3
   - Copiar el Refresh Token
4. En el panel de Admin, ingresar el Refresh Token

## 👥 Roles y Permisos

### Usuario (user)
- Subir archivos a Drive
- Ver sus archivos y los de sus admins asociados
- Descargar archivos
- Agregar y editar comentarios propios

### Admin (admin)
- Todo lo del usuario
- Configurar credenciales de Google Drive
- Ver todos los archivos de sus usuarios
- Gestionar usuarios
- Asociar/desasociar usuarios

### Superadmin (superadmin)
- Todo lo del admin
- Crear y gestionar admins
- Ver auditoría completa del sistema
- Acceso total a todos los recursos

## 🚀 Despliegue en Producción

### Usando el script de despliegue (Linux/Mac)

```bash
DEPLOY_HOST=tu-servidor.com ./deploy.sh
```

### Usando PowerShell (Windows)

```powershell
.\deploy.ps1 -RemoteHost tu-servidor.com
```

### Despliegue manual

1. **En el servidor** (Ubuntu/Debian):

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo apt install docker-compose-plugin

# Crear directorio
sudo mkdir -p /opt/docmanager-drive
cd /opt/docmanager-drive
```

2. **Subir archivos** al servidor

3. **Configurar y ejecutar**:

```bash
# Editar .env con configuración de producción
nano .env

# Iniciar servicios
docker compose up -d

# Ver logs
docker compose logs -f
```

### Configurar SSL con Let's Encrypt

1. Instalar Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
```

2. Obtener certificado:

```bash
sudo certbot --nginx -d tudominio.com
```

3. Actualizar nginx.conf para usar SSL

4. Reiniciar Nginx:

```bash
docker compose restart nginx
```

## 🧪 Tests

Ejecutar tests:

```bash
cd backend
pip install -r requirements.txt
pytest
```

Con coverage:

```bash
pytest --cov=app --cov-report=html
```

## 📝 API Endpoints

### Autenticación
- `POST /auth/register` - Registrar usuario
- `POST /auth/login` - Iniciar sesión

### Usuarios
- `GET /users/me` - Obtener perfil
- `PATCH /users/me` - Actualizar perfil
- `GET /users/me/admins` - Obtener admins asociados

### Archivos
- `POST /files/upload` - Subir archivo
- `GET /files/` - Listar archivos
- `GET /files/{id}` - Obtener archivo
- `GET /files/{id}/download` - Descargar archivo
- `DELETE /files/{id}` - Eliminar archivo

### Comentarios
- `POST /files/{id}/comments` - Agregar comentario
- `GET /files/{id}/comments` - Listar comentarios
- `PATCH /files/{id}/comments/{comment_id}` - Editar comentario
- `DELETE /files/{id}/comments/{comment_id}` - Eliminar comentario

### Admin
- `GET /admin/profile` - Perfil de admin
- `POST /admin/settings/drive-credentials` - Configurar Drive
- `POST /admin/users/create` - Crear usuario
- `POST /admin/create` - Crear admin (superadmin only)
- `GET /admin/all` - Listar admins (superadmin only)

Ver documentación completa en: http://localhost:8000/docs

## 🔒 Seguridad

- ✅ Contraseñas hasheadas con bcrypt
- ✅ JWT para autenticación
- ✅ Credenciales de Drive encriptadas con Fernet
- ✅ CORS configurado
- ✅ Rate limiting en Nginx
- ✅ Validación de inputs con Pydantic
- ✅ SQL injection protection (SQLAlchemy ORM)

## 🐛 Troubleshooting

### Base de datos no conecta

```powershell
docker compose logs db
docker compose restart db
```

### Migraciones fallan

```powershell
docker compose exec web alembic downgrade -1
docker compose exec web alembic upgrade head
```

### Error de permisos en Drive

- Verificar que el Service Account tiene acceso a la carpeta
- O verificar que el Refresh Token es válido

### Frontend no carga

```powershell
docker compose logs nginx
docker compose restart nginx
```

### Reset completo del sistema

```powershell
# Windows
.\start-local.ps1 -Reset

# Linux/Mac
docker compose down -v
rm -rf pgdata
docker compose up -d
```

### Ver logs específicos

```powershell
# Backend
docker compose logs -f web

# Frontend/Nginx
docker compose logs -f nginx

# Base de datos
docker compose logs -f db

# Todos los servicios
docker compose logs -f
```

## 📚 Stack Tecnológico

- **Backend**: FastAPI 0.109, SQLAlchemy 2.0 (async), Alembic
- **Database**: PostgreSQL 15
- **Auth**: JWT (python-jose), bcrypt
- **Drive**: google-api-python-client
- **Frontend**: HTML5, JavaScript (Vanilla)
- **Web Server**: Nginx
- **Container**: Docker, Docker Compose
- **Tests**: pytest, pytest-asyncio

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT.

## 👨‍💻 Autor

Desarrollado para gestión documental empresarial con Google Drive.

## 📞 Soporte

Para reportar bugs o solicitar features, crear un issue en el repositorio.

---

**Nota**: Este es un sistema de producción. Asegúrate de cambiar todas las contraseñas por defecto y configurar correctamente las variables de entorno antes de usar en producción.
