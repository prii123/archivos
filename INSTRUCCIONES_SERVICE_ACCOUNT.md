# 🔐 Instrucciones para Configurar Google Drive con Service Account

## ✅ Migración Completada

Se ha migrado exitosamente de **OAuth** a **Service Account** para la autenticación con Google Drive.

### Ventajas del Nuevo Sistema:
- ✅ **No requiere verificación de Google** (sin proceso de OAuth consent screen)
- ✅ **Sin problemas de 403 access_denied**
- ✅ **Credenciales que no expiran** (no hay refresh tokens que puedan fallar)
- ✅ **Configuración más simple** (solo subir JSON, sin flujo de autorización)
- ✅ **Soporte multi-admin** (cada admin con su propio Service Account)

---

## 📋 Pasos para Configurar tu Service Account

### 1. Crear Proyecto en Google Cloud Console

1. Ve a https://console.cloud.google.com/
2. Crea un nuevo proyecto o selecciona uno existente
3. Dale un nombre descriptivo (ej: "Mi Archivador DocManager")

### 2. Habilitar Google Drive API

1. En el menú lateral, ve a **APIs & Services** → **Enabled APIs & Services**
2. Clic en **+ ENABLE APIS AND SERVICES**
3. Busca "Google Drive API"
4. Clic en **ENABLE**

### 3. Crear Service Account

1. Ve a **IAM & Admin** → **Service Accounts**
2. Clic en **+ CREATE SERVICE ACCOUNT**
3. Configuración:
   - **Name**: Mi Archivador DocManager
   - **Description**: Service Account para gestión de documentos
   - Clic en **CREATE AND CONTINUE**
4. Rol (opcional): No es necesario asignar un rol para Drive
5. Clic en **CONTINUE** y luego **DONE**

### 4. Crear Clave JSON

1. En la lista de Service Accounts, localiza el que acabas de crear
2. Clic en el email del Service Account
3. Ve a la pestaña **KEYS**
4. Clic en **ADD KEY** → **Create new key**
5. Selecciona **JSON**
6. Clic en **CREATE**
7. **Guarda el archivo JSON descargado** en un lugar seguro

### 5. Compartir tu Carpeta de Drive

**IMPORTANTE**: El Service Account necesita acceso a tu carpeta de Google Drive.

1. Abre el archivo JSON que descargaste
2. Copia el valor de `client_email` (ej: `mi-archivador@proyecto.iam.gserviceaccount.com`)
3. Ve a Google Drive (https://drive.google.com)
4. Crea o selecciona la carpeta donde quieres guardar los documentos
5. Clic derecho en la carpeta → **Share** (Compartir)
6. Pega el `client_email` del Service Account
7. Dale permisos de **Editor** o **Owner**
8. Clic en **Send** (Enviar)

### 6. Obtener el Folder ID

1. Abre la carpeta compartida en Google Drive
2. Observa la URL en el navegador:
   ```
   https://drive.google.com/drive/folders/1a2B3c4D5e6F7g8H9i0J
   ```
3. Copia el ID que está después de `/folders/` (en este ejemplo: `1a2B3c4D5e6F7g8H9i0J`)

### 7. Configurar en DocManager Drive

1. Abre http://localhost en tu navegador
2. Inicia sesión con tu cuenta de admin o superadmin
3. En el panel de admin, busca la sección **"Configurar Google Drive - Service Account"**
4. **Pega el contenido completo del archivo JSON** en el campo "Service Account JSON"
5. **Pega el Folder ID** que copiaste en el paso anterior
6. Clic en **💾 Guardar Credenciales**

¡Listo! Tu Drive está configurado y listo para usar.

---

## 🎯 Ejemplo de JSON del Service Account

El archivo JSON que descargaste debe verse así:

```json
{
  "type": "service_account",
  "project_id": "mi-proyecto-123456",
  "private_key_id": "abc123def456...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQ...==\n-----END PRIVATE KEY-----\n",
  "client_email": "mi-archivador@mi-proyecto-123456.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/...",
  "universe_domain": "googleapis.com"
}
```

---

## 🚨 Solución de Problemas

### Error: "El JSON debe ser de tipo 'service_account'"
- **Causa**: Estás pegando el JSON incorrecto
- **Solución**: Asegúrate de pegar el JSON del Service Account, no el de OAuth (client_secret.json)

### Error: "El JSON no contiene los campos requeridos"
- **Causa**: El JSON está incompleto o corrupto
- **Solución**: Descarga nuevamente la clave JSON desde Google Cloud Console

### Error al listar archivos: "Permission denied"
- **Causa**: El Service Account no tiene acceso a la carpeta
- **Solución**: Ve al paso 5 y comparte la carpeta con el `client_email` del Service Account

### Error al crear carpetas: "Not found"
- **Causa**: El Folder ID es incorrecto
- **Solución**: Verifica que copiaste correctamente el ID después de `/folders/` en la URL

---

## 🔄 Múltiples Administradores

Cada administrador puede tener su propio Service Account:

1. Cada admin crea su propio Service Account en Google Cloud
2. Cada admin comparte SU carpeta de Drive con SU Service Account
3. Cada admin configura sus propias credenciales en el panel

**No hay límite** de administradores configurados con Service Account.

---

## 📊 Estado del Sistema

### Cambios Realizados:
- ✅ Backend migrado a solo Service Account
- ✅ Frontend actualizado con nueva UI
- ✅ Base de datos migrada (columna `drive_cred_type` eliminada)
- ✅ Archivo `oauth-callback.html` eliminado
- ✅ Endpoints OAuth eliminados
- ✅ Documentación actualizada

### Archivos Modificados:
- `backend/app/schemas.py` - Schemas simplificados
- `backend/app/routers/drive.py` - Solo Service Account
- `backend/app/google_drive.py` - Eliminado soporte OAuth
- `backend/app/crud.py` - Simplificado para SA
- `backend/app/models.py` - Columna `drive_cred_type` eliminada
- `frontend/admin.html` - Nueva UI para Service Account
- `backend/alembic/versions/26ca7dbacc24_*.py` - Migración DB

---

## 🎉 ¡Todo Listo!

El sistema ahora es más simple, confiable y no requiere verificación de Google. Cada admin puede configurar su propio Service Account de forma independiente.

**Soporte**: Si tienes problemas, verifica que:
1. El JSON es válido y completo
2. La carpeta está compartida con el `client_email`
3. El Folder ID es correcto
4. La API de Google Drive está habilitada en tu proyecto

---

**Versión**: 2.0 - Service Account Only  
**Fecha**: Diciembre 10, 2025
