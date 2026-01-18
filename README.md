# DNI Lookup API

Sistema de consulta de DNI con caché en base de datos local y API propia para consumo por terceros.

## Características

- 🔍 **Búsqueda de DNI**: Consulta datos de personas por número de DNI
- 💾 **Base de datos persistente**: Los datos se almacenan en SQLite para consultas futuras
- 🔑 **Sistema de Tokens**: Crea tokens ilimitados sin expiración para que otras aplicaciones consuman tu API
- ⚙️ **Configuración**: Panel para gestionar el token de apisperu.com
- 🐳 **Dockerizado**: Listo para desplegar con Dokploy
- 💾 **Backup**: Descarga la base de datos SQLite como backup
- 🛡️ **Seguridad**: Rate limiting, headers de seguridad, protección contra fuerza bruta

## Seguridad Implementada

| Característica | Descripción |
|----------------|-------------|
| **Rate Limiting** | 200 peticiones/minuto por IP |
| **Protección Login** | Bloqueo temporal tras 5 intentos fallidos (15 min) |
| **Tokens API** | Tokens de 64 caracteres, ilimitados, sin expiración |
| **Headers de Seguridad** | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection |
| **Comparación Segura** | Uso de `secrets.compare_digest` contra timing attacks |
| **Backup Protegido** | Limitado a 5 descargas/hora, requiere autenticación |
| **Validación DNI** | Sanitización y validación estricta de entrada |

## Despliegue con Dokploy

1. Sube el proyecto a un repositorio Git (GitHub, GitLab, etc.)

2. En Dokploy:
   - Crear nuevo proyecto
   - Seleccionar "Docker Compose"
   - Conectar el repositorio
   - Configurar las variables de entorno

3. Variables de entorno requeridas:
   ```env
   # Credenciales del panel de administración
   ADMIN_USER=admin
   ADMIN_PASSWORD=tu_password_muy_seguro
   
   # Credenciales para backup de base de datos
   DB_BACKUP_USER=backup_admin
   DB_BACKUP_PASSWORD=tu_password_backup_seguro
   
   # Token de apisperu.com (opcional)
   APISPERU_TOKEN=<tu_token_de_apisperu>
   
   # Rate limiting (opcional, default: 200)
   RATE_LIMIT_PER_IP=200
   ```

4. Configurar el dominio en Dokploy

## Uso

### Interfaz Web

Accede a la URL configurada y utiliza las credenciales:
- **Usuario**: admin
- **Contraseña**: escolastica123

### API para Terceros

1. Crea un token desde la interfaz web (pestaña "Tokens API")

2. Usa el token en tus aplicaciones:
   ```bash
   curl -H "Authorization: Bearer TU_TOKEN" \
        https://tu-dominio.com/api/persona/12345678
   ```

### Endpoints

| Método | Ruta | Descripción | Auth | Rate Limit |
|--------|------|-------------|------|------------|
| GET | `/api/persona/{dni}` | Buscar persona | Token API | 200/min |
| GET | `/api/buscar/{dni}` | Buscar persona (admin) | Basic Auth | 200/min |
| GET | `/api/tokens` | Listar tokens | Basic Auth | - |
| POST | `/api/tokens` | Crear token | Basic Auth | - |
| DELETE | `/api/tokens/{id}` | Eliminar token | Basic Auth | - |
| GET | `/api/backup` | Descargar backup BD | Basic Auth | 5/hora |
| GET | `/api/config` | Ver configuración | Basic Auth | - |
| PUT | `/api/config` | Actualizar token apisperu | Basic Auth | - |
| POST | `/api/login` | Login administrador | - | 10/min |
| GET | `/health` | Health check | Ninguna | - |

## Estructura de Respuestas de la API

Todas las respuestas de la API siguen una estructura estándar para facilitar la integración con otros sistemas:

```json
{
    "success": true,
    "code": 200,
    "code_description": "OK - Solicitud procesada exitosamente",
    "message": "Persona encontrada",
    "data": {
        "id": 1,
        "tipodoc": "DNI",
        "nrodoc": "12345678",
        "nombres": "JUAN CARLOS",
        "apellido_paterno": "PEREZ",
        "apellido_materno": "GARCIA",
        "codigo_verificacion": "5",
        "fecha_registro": "2026-01-18T10:30:00"
    }
}
```

### Campos de la Respuesta

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `success` | boolean | `true` si la operación fue exitosa, `false` si hubo error |
| `code` | integer | Código HTTP de respuesta |
| `code_description` | string | Descripción legible del código HTTP |
| `message` | string | Mensaje descriptivo de la operación |
| `data` | object/null | Datos de respuesta (puede ser objeto, array o null) |

### Códigos de Respuesta

| Código | Descripción | Cuándo ocurre |
|--------|-------------|---------------|
| `200` | OK - Solicitud procesada exitosamente | Consulta exitosa |
| `201` | Created - Recurso creado exitosamente | Nuevo token o persona creada |
| `400` | Bad Request - Datos de entrada inválidos | DNI con formato incorrecto |
| `401` | Unauthorized - Credenciales inválidas | Token o credenciales incorrectas |
| `403` | Forbidden - Sin permisos | Acción no permitida |
| `404` | Not Found - Recurso no encontrado | DNI no existe en la BD ni en API externa |
| `429` | Too Many Requests - Límite excedido | Más de 200 peticiones/min por IP |
| `500` | Internal Server Error | Error interno del servidor |

### Ejemplos de Uso

**Buscar persona por DNI (con Token API):**
```bash
curl -X GET "https://tu-dominio.com/api/persona/12345678" \
     -H "Authorization: Bearer tu_token_aqui"
```

**Respuesta exitosa:**
```json
{
    "success": true,
    "code": 200,
    "code_description": "OK - Solicitud procesada exitosamente",
    "message": "Persona encontrada en caché local",
    "data": {
        "id": 1,
        "tipodoc": "DNI",
        "nrodoc": "12345678",
        "nombres": "JUAN CARLOS",
        "apellido_paterno": "PEREZ",
        "apellido_materno": "GARCIA",
        "codigo_verificacion": "5",
        "fecha_registro": "2026-01-18T10:30:00",
        "desde_cache": true
    }
}
```

**Respuesta de error (DNI no encontrado):**
```json
{
    "success": false,
    "code": 404,
    "code_description": "Not Found - Recurso no encontrado",
    "message": "No se encontró información para el DNI especificado"
}
```

**Respuesta de error (Token inválido):**
```json
{
    "success": false,
    "code": 401,
    "code_description": "Unauthorized - Credenciales inválidas o no proporcionadas",
    "message": "Token inválido o inactivo"
}
```

## Desarrollo Local

```bash
# Clonar repositorio
cd /root/proyect/personas

# Construir y ejecutar
docker-compose up --build

# Acceder en http://localhost:8000
```

## Estructura del Proyecto

```
personas/
├── backend/
│   ├── app/
│   │   ├── main.py           # API FastAPI
│   │   ├── config.py         # Configuración
│   │   ├── database.py       # SQLite
│   │   ├── models.py         # Modelos
│   │   ├── schemas.py        # Schemas Pydantic
│   │   ├── auth.py           # Autenticación
│   │   └── services/
│   │       ├── dni_service.py    # Lógica de DNI
│   │       └── token_service.py  # Gestión de tokens
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/app.js
├── Dockerfile
├── docker-compose.yml
└── .env.example
```
