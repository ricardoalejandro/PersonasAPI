# DNI Lookup API

Sistema de consulta de DNI con caché en base de datos local y API propia para consumo por terceros.

## Características

- 🔍 **Búsqueda de DNI**: Consulta datos de personas por número de DNI
- 💾 **Base de datos persistente**: Los datos se almacenan en SQLite para consultas futuras
- 🔑 **Sistema de Tokens**: Crea tokens para que otras aplicaciones consuman tu API
- ⚙️ **Configuración**: Panel para gestionar el token de apisperu.com
- 🐳 **Dockerizado**: Listo para desplegar con Dokploy

## Despliegue con Dokploy

1. Sube el proyecto a un repositorio Git (GitHub, GitLab, etc.)

2. En Dokploy:
   - Crear nuevo proyecto
   - Seleccionar "Docker Compose"
   - Conectar el repositorio
   - Configurar las variables de entorno

3. Variables de entorno requeridas:
   ```
   ADMIN_USER=admin
   ADMIN_PASSWORD=escolastica123
   APISPERU_TOKEN=<tu_token_de_apisperu>
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

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/persona/{dni}` | Buscar persona | Token API |
| GET | `/api/buscar/{dni}` | Buscar persona (admin) | Basic Auth |
| GET | `/api/tokens` | Listar tokens | Basic Auth |
| POST | `/api/tokens` | Crear token | Basic Auth |
| DELETE | `/api/tokens/{id}` | Eliminar token | Basic Auth |
| GET | `/api/config` | Ver configuración | Basic Auth |
| PUT | `/api/config` | Actualizar token apisperu | Basic Auth |
| GET | `/health` | Health check | Ninguna |

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
