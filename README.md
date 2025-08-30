# 🚀 CrystoAPIVzla

API para cotizaciones USDT/VES en tiempo real con guardado automático en base de datos.

## ✨ Funcionalidades

### Cotizaciones y Datos
- **Cotizaciones BCV en tiempo real**: Web scraping automático del Banco Central de Venezuela
- **Cotizaciones P2P de Binance**: Integración con API de Binance para USD/VES
- **Historial completo**: Almacenamiento y consulta de datos históricos
- **Análisis de tendencias**: Cálculo automático de variaciones y tendencias 24h
- **Múltiples fuentes**: Consolidación de datos de diferentes proveedores

### API y Documentación
- **API REST moderna**: Endpoints RESTful con FastAPI
- **Documentación automática**: Swagger UI y ReDoc integrados
- **Versionado de API**: Estructura `/api/v1/` para compatibilidad
- **Respuestas estandarizadas**: Formato JSON consistente en todas las respuestas
- **Validación de datos**: Esquemas Pydantic para entrada y salida

### Rendimiento y Cache
- **Cache inteligente con Redis**: TTL configurable para diferentes tipos de datos
- **Invalidación automática**: Sistema de cache con actualización programada
- **Optimización de consultas**: Pool de conexiones PostgreSQL
- **Compresión HTTP**: Respuestas optimizadas para reducir latencia
- **Consultas asíncronas**: Procesamiento no bloqueante con AsyncPG

### Automatización y Monitoreo
- **Scheduler robusto**: Tareas programadas con APScheduler
  - Actualización de cotizaciones cada 5 minutos
  - Monitoreo de salud de APIs externas cada 10 minutos
  - Invalidación de cache programada
- **Logging detallado**: Registro completo de operaciones y errores
- **Manejo de errores**: Recuperación automática ante fallos temporales
- **Métricas de rendimiento**: Tiempo de ejecución y estadísticas de operaciones

### Configuración y Despliegue
- **Configuración flexible**: Variables de entorno con Pydantic Settings
- **Soporte multi-entorno**: Configuraciones para desarrollo, testing y producción
- **Despliegue en Railway**: Configuración optimizada para la nube
- **Docker ready**: Contenedores para desarrollo y producción
- **CORS configurable**: Soporte para aplicaciones frontend

## 📋 Características

- **Cotizaciones en tiempo real** de BCV y Binance P2P
- **Sistema de tareas programadas** que actualiza datos cada 5 minutos
- **Guardado automático** en `rate_history` y `current_rates` para análisis histórico
- **Comparación de exchanges** con cálculo de spreads
- **Variaciones y tendencias** calculadas automáticamente
- **Caché Redis** con TTL de 5 minutos para datos de tareas programadas
- **Endpoints optimizados** que consultan solo la base de datos sin web scraping
- **Optimizado para Railway** con configuración de producción

## 📊 Cálculo de Variaciones

El sistema calcula automáticamente las variaciones porcentuales para cada cotización:

- **variation_percentage**: Diferencia entre los dos últimos precios registrados.
- **variation_1h**: Variación en la última hora
- **variation_24h**: Variación en las últimas 24 horas
- **trend_main**: Tendencia general (up/down/stable) basada en la variación principal
- **trend_1h**: Tendencia en la última hora
- **trend_24h**: Tendencia en las últimas 24 horas

## 🏗️ Arquitectura

### Componentes Principales

- **FastAPI**: Framework web asíncrono para APIs REST
- **PostgreSQL**: Base de datos principal para almacenamiento persistente
- **Redis**: Sistema de cache en memoria (opcional)
- **APScheduler**: Sistema de tareas programadas para actualización automática
- **AsyncPG**: Driver asíncrono de alto rendimiento para PostgreSQL
- **Pydantic**: Validación de datos y configuración
- **Uvicorn**: Servidor ASGI de alto rendimiento

### Flujo de Datos

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scheduler     │    │   External APIs  │    │   Database      │
│   (APScheduler) │───▶│   (BCV/Binance)  │───▶│   (PostgreSQL)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         │              ┌─────────────────┐              │
         └─────────────▶│   Redis Cache   │◀─────────────┘
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   FastAPI App   │
                        │   (REST API)    │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Client Apps   │
                        └─────────────────┘
```

### Estructura del Proyecto

```
crystoapivzla/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── rates.py          # Endpoints de cotizaciones
│   │       │   └── health.py         # Endpoint de salud del sistema
│   │       └── router.py             # Router principal de la API
│   ├── core/
│   │   ├── config.py                # Configuración con Pydantic Settings
│   │   ├── database.py              # Servicio de conexión a PostgreSQL
│   │   ├── redis_client.py          # Cliente Redis para cache
│   │   └── scheduler.py             # Tareas programadas (BCV/Binance)
│   ├── models/
│   │   └── database.py              # Modelos de base de datos
│   ├── services/
│   │   ├── bcv_service.py           # Web scraping del BCV
│   │   ├── binance_service.py       # API de Binance P2P
│   │   └── rate_service.py          # Lógica de negocio de cotizaciones
│   └── utils/
│       ├── cache.py                 # Utilidades de cache Redis
│       ├── logger.py                # Configuración de logging
│       └── response.py              # Respuestas HTTP estandarizadas
├── database/                        # Esquemas y configuración de BD
├── simple_server_railway.py         # Servidor principal para Railway
└── requirements.txt                 # Dependencias
```

### Patrones de Diseño Implementados

- **Repository Pattern**: Separación de lógica de acceso a datos
- **Service Layer**: Lógica de negocio encapsulada en servicios
- **Dependency Injection**: Inyección de dependencias con FastAPI
- **Factory Pattern**: Creación de conexiones de base de datos
- **Observer Pattern**: Sistema de cache con invalidación automática

## 🚀 Instalación

### Desarrollo Local

#### Prerrequisitos
- Python 3.8+ (recomendado 3.11+)
- PostgreSQL 12+ (recomendado 14+)
- Redis 6+ (opcional, para cache)
- Git

#### Instalación Paso a Paso

1. **Clonar el repositorio:**
   ```bash
   git clone <repository-url>
   cd crystoapivzla
   ```

2. **Crear y activar entorno virtual:**
   ```bash
   # Crear entorno virtual
   python -m venv venv
   
   # Activar entorno virtual
   # En Linux/Mac:
   source venv/bin/activate
   
   # En Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   
   # En Windows (CMD):
   venv\Scripts\activate.bat
   ```

3. **Actualizar pip e instalar dependencias:**
   ```bash
   # Actualizar pip
   python -m pip install --upgrade pip
   
   # Instalar dependencias
   pip install -r requirements.txt
   ```

4. **Configurar base de datos PostgreSQL:**
   ```bash
   # Crear base de datos (usando psql)
   createdb crystoapivzla
   
   # O usando SQL directo:
   psql -U postgres -c "CREATE DATABASE crystoapivzla;"
   
   # Ejecutar migraciones (si existen)
   # python -m alembic upgrade head
   ```

5. **Configurar variables de entorno:**
   ```bash
   # Copiar archivo de ejemplo (si existe)
   cp .env.example .env
   
   # O crear archivo .env manualmente con las variables requeridas
   # Ver sección "Variables de Entorno" para configuración completa
   ```

6. **Verificar configuración:**
   ```bash
   # Verificar conexión a base de datos
   python -c "from app.core.database import DatabaseService; print('DB OK')"
   
   # Verificar dependencias
   python -c "import fastapi, uvicorn, asyncpg; print('Dependencies OK')"
   ```

7. **Ejecutar la aplicación:**
   ```bash
   # Modo desarrollo
   python simple_server_railway.py
   
   # O usando uvicorn directamente
   uvicorn simple_server_railway:app --reload --host 0.0.0.0 --port 8000
   
   # Con variables de entorno específicas
   DEBUG=true LOG_LEVEL=DEBUG python simple_server_railway.py
   ```

8. **Verificar instalación:**
   - Abrir navegador en `http://localhost:8000`
   - Verificar documentación API en `http://localhost:8000/docs`
   - Probar endpoint de salud: `http://localhost:8000/health`

### Desarrollo con Docker

```bash
# Ejecutar con Docker Compose (incluye Redis)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Acceder a Redis Commander (interfaz web)
# http://localhost:8081 (admin/admin123)

# Detener servicios
docker-compose down
```

### Desarrollo con Redis Commander

```bash
# Ejecutar con herramientas de desarrollo
docker-compose --profile tools up -d

# Esto incluye Redis Commander para monitorear el caché
```

## 🚀 Desarrollo Local con Docker

```bash
# Ejecutar con Docker Compose (incluye Redis)
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Ejecutar solo herramientas de desarrollo (Redis Commander)
docker-compose --profile tools up -d
```

## ⚡ Sistema de Caché Redis

La API implementa un sistema de caché Redis para optimizar el rendimiento:

### 🔧 Características del Caché
- **Caché automático** para cotizaciones actuales y históricas
- **TTL configurable** (10 min para actuales, 5 min para históricas)
- **Caché de tareas programadas** con TTL de 5 minutos para datos de BCV y Binance
- **Invalidación automática** cada 10 minutos
- **Fallback a base de datos** si Redis no está disponible

### 📊 Endpoints con Caché
- `GET /api/v1/rates/current` - Cotizaciones actuales (TTL: 10 min)
- `GET /api/v1/rates/history` - Historial de cotizaciones (TTL: 5 min)
- **Tareas programadas** - Datos de BCV y Binance P2P (TTL: 5 min)

### 🔄 Sistema de Tareas Programadas
- **Actualización automática** cada 5 minutos de BCV y Binance P2P
- **Almacenamiento en Redis** con TTL de 5 minutos
- **Guardado en base de datos** en `current_rates` y `rate_history`
- **Ejecución en paralelo** para mayor eficiencia
- **Logs detallados** para monitoreo y debugging

### 🛠️ Configuración Redis
```bash
# Variables de entorno para Redis
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_TTL_CURRENT_RATES=600
REDIS_TTL_LATEST_RATES=300
```

### 🔍 Monitoreo Redis
Accede a Redis Commander en desarrollo:
- URL: http://localhost:8081
- Usuario: admin
- Contraseña: admin123

## ⚙️ Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

### Variables Requeridas

```env
# Configuración de la aplicación
APP_NAME="CrystoDolar API"
APP_VERSION="1.0.0"
DEBUG=false
ENVIRONMENT=production

# Base de datos PostgreSQL
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/crystodolar
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis Cache (opcional)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
REDIS_TTL=300

# Configuración del Scheduler
SCHEDULER_ENABLED=true
UPDATE_INTERVAL_MINUTES=5
HEALTH_CHECK_INTERVAL_MINUTES=10
CACHE_INVALIDATION_INTERVAL_MINUTES=10

# APIs Externas
BINANCE_API_BASE_URL="https://p2p.binance.com"
BCV_BASE_URL="https://www.bcv.org.ve"

# Configuración de CORS
ALLOWED_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
ALLOWED_METHODS=["GET","POST","PUT","DELETE"]
ALLOWED_HEADERS=["*"]

# Configuración de Logging
LOG_LEVEL=INFO
LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Configuración del servidor
HOST=0.0.0.0
PORT=8000
WORKERS=1
```

### Variables de Desarrollo

Para desarrollo local, puedes usar estas configuraciones adicionales:

```env
# Desarrollo
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Base de datos local
DATABASE_URL=postgresql://postgres:password@localhost:5432/crystodolar_dev

# Desactivar Redis en desarrollo
REDIS_ENABLED=false
```

### Configuración con Pydantic Settings

El proyecto utiliza Pydantic Settings para la gestión de configuración, lo que permite:

- Carga automática desde archivos `.env`
- Validación de tipos de datos
- Valores por defecto
- Variables de entorno con precedencia sobre el archivo `.env`

**Ejemplo de uso:**
```bash
# Ejecutar con variables de entorno específicas
DEBUG=true APP_NAME="CrystoDolar Dev" python simple_server_railway.py

# O usando uvicorn directamente
DEBUG=true uvicorn simple_server_railway:app --reload
```

## 📚 Endpoints de la API

### 🔍 Información General

#### `GET /`
Información básica de la API.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message": "CrystoAPIVzla Simple",
    "version": "1.0.0",
    "description": "Cotizaciones USDT/VES en tiempo real",
    "sources": ["BCV", "Binance P2P"],
    "docs": "/docs",
    "status": "operational",
    "environment": "production"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /health`
Health check para Railway.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "service": "crystoapivzla",
    "message": "Service is running",
    "environment": "production",
    "database_url": "configured"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/status`
Estado del sistema.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "service": "crystoapivzla",
    "version": "1.0.0",
    "environment": "production",
    "database_configured": true
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### 💰 Cotizaciones

#### `GET /api/v1/rates/current`
Obtener cotizaciones actuales desde la tabla `current_rates` (sin web scraping en tiempo real).

**Características:**
- **Consulta optimizada** solo a la base de datos
- **Datos actualizados** por tareas programadas cada 5 minutos
- **Variaciones calculadas** automáticamente (1h, 24h)
- **Caché Redis** con TTL de 10 minutos

**Parámetros:**
- `exchange_code` (opcional): Filtrar por exchange (`bcv`, `binance_p2p`)
- `currency_pair` (opcional): Filtrar por par de monedas

**Ejemplo:**
```bash
GET /api/v1/rates/current?exchange_code=bcv
```

**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "exchange_code": "bcv",
      "currency_pair": "USD/VES",
      "base_currency": "USD",
      "quote_currency": "VES",
      "buy_price": 35.85,
      "sell_price": 35.85,
      "avg_price": 35.85,
      "variation_percentage": "+0.15%",
      "variation_1h": "+0.08%",
      "variation_24h": "+1.25%",
      "trend_main": "up",
      "trend_1h": "up",
      "trend_24h": "up",
      "timestamp": "2024-01-15T10:30:00",
      "last_update": "2024-01-15T10:25:00"
    }
  ],
  "count": 1,
  "source": "database_with_scheduled_updates",
  "cache_hit": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/summary`
Resumen del mercado con análisis de spreads.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "total_rates": 2,
    "exchanges_active": 2,
    "last_update": "2024-01-15T10:30:00",
    "rates": [...],
    "market_analysis": {
      "bcv_usd": 35.85,
      "binance_usdt": 36.20,
      "spread_ves": 0.35,
      "spread_percentage": 0.98,
      "market_difference": "premium"
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/compare`
Comparar cotizaciones entre BCV y Binance P2P.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "bcv": {
      "exchange_code": "bcv",
      "currency_pair": "USD/VES",
      "usd_ves": 35.85,
      "eur_ves": 39.12
    },
    "binance_p2p": {
      "exchange_code": "binance_p2p",
      "currency_pair": "USDT/VES",
      "usdt_ves_buy": 36.20,
      "usdt_ves_sell": 36.15,
      "usdt_ves_avg": 36.18
    },
    "analysis": {
      "spread_bcv_binance": 0.33,
      "spread_percentage": 0.92
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

### 🏦 Fuentes Específicas

#### `GET /api/v1/rates/bcv`
Cotización oficial del BCV.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "exchange_code": "bcv",
    "currency_pair": "USD/VES",
    "buy_price": 35.85,
    "sell_price": 35.85,
    "avg_price": 35.85,
    "source": "bcv",
    "api_method": "web_scraping",
    "trade_type": "official"
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

#### `GET /api/v1/rates/binance-p2p/complete`
Precios completos de Binance P2P.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "exchange_code": "binance_p2p",
    "currency_pair": "USDT/VES",
    "buy_usdt": {
      "price": 36.20,
      "avg_price": 36.18
    },
    "sell_usdt": {
      "price": 36.15,
      "avg_price": 36.18
    },
    "market_analysis": {
      "spread_internal": 0.05,
      "spread_percentage": 0.14,
      "volume_24h": 1250.50,
      "liquidity_score": "high"
    }
  },
  "timestamp": "2024-01-15T10:30:00"
}
```

### 📊 Histórico y Estado

#### `GET /api/v1/rates/history`
Obtener histórico de cotizaciones.

**Parámetros:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Ejemplo:**
```bash
GET /api/v1/rates/history?limit=50
```

#### `GET /api/v1/rates/auto-save-status`
Estado del guardado automático.

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "auto_save_enabled": true,
    "database_available": true,
    "total_records_in_history": 15420,
    "exchange_statistics": [
      {
        "exchange_code": "BCV",
        "total_records": 8230,
        "last_update": "2024-01-15T10:30:00"
      }
    ],
    "auto_save_endpoints": [
      "/api/v1/rates/current",
      "/api/v1/rates/summary",
      "/api/v1/rates/compare"
    ]
  }
}
```

### 🔄 Operaciones

#### `POST /api/v1/rates/refresh`
Forzar actualización de cotizaciones.

**Parámetros:**
- `exchange_code` (opcional): Exchange específico a actualizar

**Ejemplo:**
```bash
POST /api/v1/rates/refresh
Content-Type: application/json

{
  "exchange_code": "bcv"
}
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message": "Actualización iniciada",
    "exchanges_updated": ["bcv"],
    "timestamp": "2024-01-15T10:30:00"
  }
}
```

## 🗄️ Base de Datos

### Esquema Principal

```sql
-- Tabla de historial de tasas
CREATE TABLE rate_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange_code VARCHAR(50) NOT NULL,
    currency_pair VARCHAR(20) NOT NULL,
    buy_price DECIMAL(15,4),
    sell_price DECIMAL(15,4),
    avg_price DECIMAL(15,4),
    volume_24h DECIMAL(15,2),
    source VARCHAR(100),
    api_method VARCHAR(50),
    trade_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT NOW()
);
```

### Guardado Automático

Los siguientes endpoints guardan automáticamente en `rate_history`:
- `/api/v1/rates/current` - Todas las tasas obtenidas
- `/api/v1/rates/summary` - Tasas del resumen
- `/api/v1/rates/compare` - Tasas de comparación

**Lógica inteligente:** Solo se insertan tasas con cambios significativos (>0.01% por defecto).

## 🚀 Despliegue en Railway

### Configuración Inicial

1. **Conectar Repositorio**
   ```bash
   # Instalar Railway CLI
   npm install -g @railway/cli
   
   # Login en Railway
   railway login
   
   # Inicializar proyecto
   railway init
   
   # Conectar repositorio existente
   railway link
   ```

2. **Configurar Servicios**
   ```bash
   # Agregar PostgreSQL
   railway add postgresql
   
   # Agregar Redis
   railway add redis
   
   # Ver servicios
   railway status
   ```

### Variables de Entorno en Railway

#### Variables Requeridas
```env
# Aplicación
APP_NAME=CrystoDolar API
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Base de datos (automática con Railway PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Redis (automática con Railway Redis)
REDIS_URL=${{Redis.REDIS_URL}}
REDIS_ENABLED=true
REDIS_TTL=300

# Servidor
PORT=${{PORT}}  # Automático en Railway
HOST=0.0.0.0
WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS
ALLOWED_ORIGINS=["https://crystodolar.com","https://www.crystodolar.com"]
ALLOWED_METHODS=["GET","POST","PUT","DELETE"]
ALLOWED_HEADERS=["*"]

# Scheduler
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=America/Caracas
UPDATE_INTERVAL_MINUTES=5
HEALTH_CHECK_INTERVAL_MINUTES=10

# APIs Externas
BCV_BASE_URL=https://www.bcv.org.ve
BINANCE_API_BASE_URL=https://p2p.binance.com
REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

#### Configuración de Variables
```bash
# Configurar variables individualmente
railway variables set APP_NAME="CrystoDolar API"
railway variables set ENVIRONMENT=production
railway variables set DEBUG=false

# Configurar desde archivo
railway variables set --from-file .env.production

# Ver variables configuradas
railway variables
```

### Configuración de Despliegue

#### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python simple_server_railway.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

#### Procfile (alternativo)
```
web: python simple_server_railway.py
```

### Monitoreo y Logs

```bash
# Ver logs en tiempo real
railway logs

# Ver logs con filtros
railway logs --filter="ERROR"
railway logs --since="1h"

# Ver métricas
railway status

# Conectar a base de datos
railway connect postgresql

# Conectar a Redis
railway connect redis
```

### Comandos de Despliegue

```bash
# Desplegar manualmente
railway up

# Desplegar con logs
railway up --detach=false

# Redeploy
railway redeploy

# Rollback
railway rollback
```

### Configuración de Dominio

```bash
# Generar dominio Railway
railway domain

# Configurar dominio personalizado
railway domain add crystodolar-api.com

# Ver dominios
railway domain list
```

### Optimizaciones para Producción

#### 1. **Configuración de Workers**
```python
# simple_server_railway.py
import os
from multiprocessing import cpu_count

# Calcular workers óptimos
workers = int(os.getenv("WORKERS", min(cpu_count() * 2 + 1, 8)))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=workers,
        access_log=False,  # Desactivar en producción
        log_level="info"
    )
```

#### 2. **Health Checks**
```python
# Configurar health check robusto
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "scheduler": check_scheduler_status()
    }
    
    if all(checks.values()):
        return {"status": "healthy", "checks": checks}
    else:
        raise HTTPException(status_code=503, detail={"status": "unhealthy", "checks": checks})
```

#### 3. **Configuración de Logs**
```python
# Configurar logging para producción
logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(name)s"}'
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "level": "INFO"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
})
```

### Troubleshooting

#### Problemas Comunes

1. **Error de Conexión a Base de Datos**
   ```bash
   # Verificar variables
   railway variables | grep DATABASE
   
   # Probar conexión
   railway run python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
   ```

2. **Error de Puerto**
   ```bash
   # Verificar configuración de puerto
   railway variables | grep PORT
   
   # El puerto debe ser dinámico
   PORT=${{PORT}}
   ```

3. **Problemas de Memory/CPU**
   ```bash
   # Ver uso de recursos
   railway status
   
   # Ajustar workers
   railway variables set WORKERS=2
   ```

### Backup y Recuperación

```bash
# Backup de base de datos
railway run pg_dump $DATABASE_URL > backup.sql

# Restaurar backup
railway run psql $DATABASE_URL < backup.sql

# Backup de Redis (si es necesario)
railway connect redis
# Dentro de Redis CLI:
# BGSAVE
```

## 🧪 Testing y Calidad de Código

### Configuración de Testing

El proyecto incluye un conjunto completo de tests para garantizar la calidad y confiabilidad:

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx pytest-cov pytest-mock

# Instalar dependencias adicionales para testing
pip install factory-boy faker
```

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar con output detallado
pytest -v

# Ejecutar con cobertura de código
pytest --cov=app --cov-report=html --cov-report=term

# Ejecutar tests específicos
pytest tests/test_rates.py
pytest tests/test_services/

# Ejecutar tests con marcadores específicos
pytest -m "not slow"  # Excluir tests lentos
pytest -m "integration"  # Solo tests de integración

# Ejecutar tests en paralelo
pytest -n auto  # Requiere pytest-xdist
```

### Estructura de Tests

```
tests/
├── conftest.py                 # Configuración y fixtures globales
├── test_main.py               # Tests del punto de entrada
├── api/
│   ├── test_health.py         # Tests de endpoints de salud
│   └── test_rates.py          # Tests de endpoints de cotizaciones
├── services/
│   ├── test_bcv_service.py    # Tests del servicio BCV
│   ├── test_binance_service.py # Tests del servicio Binance
│   └── test_rate_service.py   # Tests de lógica de cotizaciones
├── core/
│   ├── test_database.py       # Tests de conexión a BD
│   ├── test_redis_client.py   # Tests de cliente Redis
│   └── test_scheduler.py      # Tests del scheduler
└── utils/
    ├── test_cache.py          # Tests de utilidades de cache
    └── test_response.py       # Tests de respuestas HTTP
```

### Tests de Endpoints

```bash
# Tests manuales de endpoints

# Health check
curl -X GET http://localhost:8000/health

# Cotizaciones actuales
curl -X GET http://localhost:8000/api/v1/rates/current

# Cotizaciones históricas
curl -X GET "http://localhost:8000/api/v1/rates/history?days=7"

# Test con headers específicos
curl -H "Accept: application/json" \
     -H "User-Agent: CrystoDolar-Test/1.0" \
     http://localhost:8000/api/v1/rates/current
```

### Tests de Carga y Rendimiento

```bash
# Instalar herramientas de testing de carga
pip install locust

# Ejecutar tests de carga básicos
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Test de carga desde línea de comandos
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
       --users 10 --spawn-rate 2 --run-time 1m --headless
```

### Variables de Entorno para Testing

```env
# .env.test
ENVIRONMENT=testing
DEBUG=true
LOG_LEVEL=DEBUG

# Base de datos de testing
DATABASE_URL=postgresql://postgres:password@localhost:5432/crystodolar_test

# Redis de testing
REDIS_ENABLED=false
# O usar una instancia separada:
# REDIS_URL=redis://localhost:6379/1

# Desactivar scheduler en tests
SCHEDULER_ENABLED=false

# APIs mock para testing
BCV_BASE_URL=http://localhost:8001/mock/bcv
BINANCE_API_BASE_URL=http://localhost:8001/mock/binance
```

### Cobertura de Código

```bash
# Generar reporte de cobertura HTML
pytest --cov=app --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows

# Generar reporte de cobertura en terminal
pytest --cov=app --cov-report=term-missing

# Configurar umbral mínimo de cobertura
pytest --cov=app --cov-fail-under=80
```

### Mocking y Fixtures

Ejemplo de fixtures para testing:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_redis(mocker):
    return mocker.patch('app.core.redis_client.redis_client')

@pytest.fixture
def mock_database(mocker):
    return mocker.patch('app.core.database.DatabaseService')
```

### Integración Continua

Ejemplo de configuración para GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3
```

### Endpoints de Prueba

```bash
# Health check
curl https://your-app.railway.app/health

# Cotizaciones actuales
curl https://your-app.railway.app/api/v1/rates/current

# Estado del sistema
curl https://your-app.railway.app/api/v1/status
```

### Validación de Respuestas

Todas las respuestas incluyen:
- `status`: `success` o `error`
- `timestamp`: ISO 8601
- `data` o `error`: Contenido de la respuesta

## 🔍 Monitoreo y Observabilidad

### Health Check del Sistema

El sistema incluye endpoints de monitoreo para verificar el estado de todos los componentes:

```bash
# Health check general
curl http://localhost:8000/health

# Respuesta esperada:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "services": {
    "database": "connected",
    "redis": "connected",
    "scheduler": "running"
  },
  "version": "1.0.0"
}
```

### Logging Detallado

El sistema implementa logging estructurado con diferentes niveles:

```bash
# Ver logs en tiempo real (si están configurados en archivo)
tail -f logs/app.log

# Filtrar por nivel de error
grep "ERROR" logs/app.log

# Filtrar logs del scheduler
grep "scheduler" logs/app.log

# Ver logs de las últimas 24 horas
grep "$(date '+%Y-%m-%d')" logs/app.log
```

**Niveles de logging configurables:**
- `DEBUG`: Información detallada para desarrollo
- `INFO`: Operaciones normales del sistema
- `WARNING`: Situaciones que requieren atención
- `ERROR`: Errores que afectan funcionalidad
- `CRITICAL`: Errores críticos del sistema

### Monitoreo de Redis Cache

```bash
# Conectar a Redis CLI
redis-cli

# Ver estadísticas generales
INFO stats

# Ver memoria utilizada
INFO memory

# Listar keys de cache de cotizaciones
KEYS "rates:*"

# Ver TTL de una key específica
TTL "rates:current"

# Ver contenido de cache
GET "rates:current"

# Limpiar cache específico
DEL "rates:current"

# Limpiar todo el cache
FLUSHDB
```

### Monitoreo del Scheduler

El scheduler incluye logging detallado de todas las tareas:

```bash
# Ver estado de tareas programadas
grep "scheduled_" logs/app.log

# Monitorear tiempo de ejecución
grep "ejecutada en" logs/app.log

# Ver errores en tareas programadas
grep "Error en tarea" logs/app.log
```

### Métricas de Base de Datos

```sql
-- Verificar conexiones activas
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- Ver tamaño de tablas principales
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename IN ('current_rates', 'rate_history')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verificar últimas actualizaciones
SELECT source, MAX(timestamp) as last_update 
FROM current_rates 
GROUP BY source;
```

### Métricas Disponibles

- **Total de registros** en `rate_history`
- **Estadísticas por exchange** y día
- **Estado del guardado automático**
- **Últimas tasas registradas**
- **Tiempo de respuesta de APIs externas**
- **Uso de memoria y CPU**
- **Estadísticas de cache hit/miss**

### Alertas y Notificaciones

El sistema puede configurarse para enviar alertas en caso de:
- Fallos en la conexión a APIs externas
- Errores en tareas programadas
- Problemas de conectividad con base de datos o Redis
- Tiempo de respuesta elevado en endpoints

## 📋 Cambios Recientes

### v2.0.0 - Arquitectura Mejorada y Automatización Completa
- ✅ **Scheduler Automatizado**: Tareas programadas cada 5 minutos para actualización de cotizaciones
- ✅ **Separación de Responsabilidades**: Endpoints optimizados que solo consultan datos sin ejecutar scraping
- ✅ **Cache Redis Avanzado**: Sistema de cache robusto con TTL de 5 minutos y fallback automático
- ✅ **Logging Estructurado**: Sistema de logs detallado con niveles configurables y formato JSON
- ✅ **Health Checks Completos**: Monitoreo de base de datos, Redis y scheduler
- ✅ **Configuración con Pydantic**: Gestión centralizada de configuración con validación automática

### v1.9.0 - Optimizaciones de Rendimiento
- ✅ **Pool de Conexiones**: Configuración optimizada para base de datos con pool sizing
- ✅ **Async/Await**: Implementación completa de operaciones asíncronas
- ✅ **Manejo de Errores**: Sistema robusto de manejo de excepciones y reintentos
- ✅ **Validación de Datos**: Schemas Pydantic para validación de entrada y salida
- ✅ **CORS Configurado**: Configuración flexible para múltiples orígenes

### v1.8.0 - Mejoras en Servicios Externos
- ✅ **Servicio BCV Mejorado**: Web scraping robusto con manejo de errores
- ✅ **Integración Binance P2P**: API optimizada para cotizaciones P2P
- ✅ **Rate Limiting**: Protección contra sobrecarga de APIs externas
- ✅ **Timeouts Configurables**: Gestión de timeouts para requests externos
- ✅ **User Agents Dinámicos**: Rotación de user agents para evitar bloqueos

### v1.7.0 - Base de Datos y Persistencia
- ✅ **Tablas Optimizadas**: Estructura mejorada para `current_rates` y `rate_history`
- ✅ **Índices de Rendimiento**: Índices optimizados para consultas frecuentes
- ✅ **Migraciones Automáticas**: Sistema de migraciones con Alembic
- ✅ **Backup Automático**: Estrategias de backup para datos críticos
- ✅ **Transacciones Seguras**: Manejo transaccional para operaciones críticas

### v1.6.0 - Testing y Calidad
- ✅ **Suite de Tests Completa**: Tests unitarios, integración y carga
- ✅ **Cobertura de Código**: Configuración de coverage con reportes HTML
- ✅ **Mocking Avanzado**: Fixtures y mocks para testing aislado
- ✅ **CI/CD Pipeline**: Configuración para GitHub Actions
- ✅ **Load Testing**: Tests de carga con Locust

### v1.5.0 - Despliegue y DevOps
- ✅ **Railway Optimizado**: Configuración completa para Railway deployment
- ✅ **Docker Support**: Containerización con multi-stage builds
- ✅ **Environment Management**: Gestión de múltiples entornos (dev, staging, prod)
- ✅ **Monitoring**: Métricas y observabilidad en producción
- ✅ **Auto-scaling**: Configuración para escalado automático

### v1.4.0 - Seguridad y Configuración
- ✅ **Variables de Entorno Seguras**: Gestión segura de secretos y configuración
- ✅ **Validación de Input**: Sanitización y validación de todas las entradas
- ✅ **Rate Limiting**: Protección contra abuso de API
- ✅ **HTTPS Enforcement**: Configuración para conexiones seguras
- ✅ **Security Headers**: Headers de seguridad configurados

### v1.3.0 - Documentación y API
- ✅ **OpenAPI 3.0**: Documentación automática mejorada
- ✅ **Ejemplos de Respuesta**: Ejemplos detallados en la documentación
- ✅ **Versionado de API**: Sistema de versionado con `/api/v1/`
- ✅ **Response Standards**: Formato estándar para todas las respuestas
- ✅ **Error Handling**: Códigos de error consistentes y descriptivos

### v1.2.0 - Sistema de Cache Redis
- ✅ Implementación de cache Redis para optimizar rendimiento
- ✅ TTL configurable para datos de cotizaciones
- ✅ Fallback automático cuando Redis no está disponible
- ✅ Invalidación inteligente de cache

### v1.1.0 - Mejoras en Scheduler
- ✅ Scheduler robusto con APScheduler
- ✅ Tareas programadas para actualización automática
- ✅ Manejo de errores y reintentos
- ✅ Logging detallado de operaciones

### v1.0.1 - Correcciones y Mejoras
- ✅ **Migración a FastAPI Lifespan Events**: Compatibilidad con versiones futuras
- ✅ **Corrección CacheService**: Eliminación de errores en logs de producción
- ✅ **Mejoras Técnicas**: Uso de `asynccontextmanager` y configuración centralizada

### v1.0.0 - Lanzamiento Inicial
- ✅ API REST completa para cotizaciones
- ✅ Integración con BCV y Binance
- ✅ Base de datos PostgreSQL
- ✅ Documentación automática con FastAPI

## 🔧 Desarrollo

### Estructura del Proyecto Detallada

```
crystodolar-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py             # Router principal v1
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           ├── health.py      # Health checks
│   │           └── rates.py       # Endpoints de cotizaciones
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuración con Pydantic
│   │   ├── database.py            # Configuración de base de datos
│   │   ├── redis_client.py        # Cliente Redis
│   │   ├── scheduler.py           # Tareas programadas
│   │   └── logging_config.py      # Configuración de logging
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py                # Modelo base SQLAlchemy
│   │   ├── rate.py                # Modelos de cotizaciones
│   │   └── schemas.py             # Schemas Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── bcv_service.py         # Servicio web scraping BCV
│   │   ├── binance_service.py     # Servicio API Binance
│   │   ├── cache_service.py       # Servicio de cache Redis
│   │   ├── database_service.py    # Servicio de base de datos
│   │   └── rate_service.py        # Lógica de negocio cotizaciones
│   └── utils/
│       ├── __init__.py
│       ├── cache.py               # Utilidades de cache
│       ├── http_client.py         # Cliente HTTP configurado
│       ├── response_helpers.py    # Helpers para respuestas
│       └── validators.py          # Validadores personalizados
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Configuración global de tests
│   ├── api/
│   ├── services/
│   ├── core/
│   └── utils/
├── alembic/                       # Migraciones de base de datos
├── docs/                          # Documentación adicional
├── scripts/                       # Scripts de utilidad
├── .env.example                   # Ejemplo de variables de entorno
├── .gitignore
├── requirements.txt               # Dependencias de producción
├── requirements-dev.txt           # Dependencias de desarrollo
├── simple_server_railway.py       # Punto de entrada para Railway
├── Dockerfile                     # Configuración Docker
├── railway.json                   # Configuración Railway
└── README.md
```

### Guías de Desarrollo

#### 1. **Principios de Arquitectura**

- **Separación de Responsabilidades**: Cada módulo tiene una responsabilidad específica
- **Inversión de Dependencias**: Usar inyección de dependencias donde sea posible
- **Single Responsibility**: Cada función/clase debe tener una sola responsabilidad
- **DRY (Don't Repeat Yourself)**: Evitar duplicación de código
- **SOLID Principles**: Aplicar principios SOLID en el diseño

#### 2. **Estándares de Código**

```python
# Ejemplo de estructura de endpoint
from fastapi import APIRouter, Depends, HTTPException
from app.services.rate_service import RateService
from app.models.schemas import RateResponse
from app.utils.response_helpers import create_success_response

router = APIRouter()

@router.get("/current", response_model=RateResponse)
async def get_current_rates(
    rate_service: RateService = Depends()
) -> dict:
    """
    Obtener cotizaciones actuales.
    
    Returns:
        dict: Respuesta con cotizaciones actuales
        
    Raises:
        HTTPException: Si hay error al obtener cotizaciones
    """
    try:
        rates = await rate_service.get_current_rates()
        return create_success_response(
            data=rates,
            message="Cotizaciones obtenidas exitosamente"
        )
    except Exception as e:
        logger.error(f"Error obteniendo cotizaciones: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
```

#### 3. **Manejo de Dependencias**

```python
# app/core/dependencies.py
from fastapi import Depends
from app.services.database_service import DatabaseService
from app.services.cache_service import CacheService
from app.core.database import get_db_session
from app.core.redis_client import get_redis_client

def get_database_service(
    session = Depends(get_db_session)
) -> DatabaseService:
    return DatabaseService(session)

def get_cache_service(
    redis_client = Depends(get_redis_client)
) -> CacheService:
    return CacheService(redis_client)
```

#### 4. **Logging Estructurado**

```python
import logging
from app.core.config import settings

# Configurar logger
logger = logging.getLogger(__name__)

# Usar logging estructurado
logger.info(
    "Actualizando cotizaciones",
    extra={
        "source": "bcv",
        "operation": "update_rates",
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

#### 5. **Manejo de Errores**

```python
from app.utils.exceptions import (
    ServiceUnavailableError,
    DataValidationError,
    CacheError
)

try:
    result = await external_service.fetch_data()
except httpx.TimeoutException:
    raise ServiceUnavailableError("Servicio externo no disponible")
except ValidationError as e:
    raise DataValidationError(f"Datos inválidos: {e}")
except Exception as e:
    logger.error(f"Error inesperado: {e}")
    raise
```

#### 6. **Testing Guidelines**

```python
# tests/test_rate_service.py
import pytest
from unittest.mock import AsyncMock, patch
from app.services.rate_service import RateService

@pytest.mark.asyncio
async def test_get_current_rates_success(mock_database_service):
    # Arrange
    mock_database_service.get_current_rates.return_value = {
        "usd": 36.50,
        "eur": 39.20
    }
    
    rate_service = RateService(mock_database_service)
    
    # Act
    result = await rate_service.get_current_rates()
    
    # Assert
    assert result["usd"] == 36.50
    assert result["eur"] == 39.20
    mock_database_service.get_current_rates.assert_called_once()
```

#### 7. **Performance Guidelines**

- **Async/Await**: Usar operaciones asíncronas para I/O
- **Connection Pooling**: Configurar pools de conexión apropiados
- **Caching**: Implementar cache en operaciones costosas
- **Lazy Loading**: Cargar datos solo cuando sea necesario
- **Pagination**: Implementar paginación para listas grandes

#### 8. **Security Best Practices**

```python
# Validación de entrada
from pydantic import BaseModel, validator

class RateRequest(BaseModel):
    currency: str
    amount: float
    
    @validator('currency')
    def validate_currency(cls, v):
        allowed_currencies = ['USD', 'EUR', 'COP']
        if v.upper() not in allowed_currencies:
            raise ValueError('Moneda no soportada')
        return v.upper()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('El monto debe ser positivo')
        return v
```

#### 9. **Database Guidelines**

```python
# Usar transacciones para operaciones críticas
async def update_rates_transactional(session, rates_data):
    async with session.begin():
        # Actualizar current_rates
        await session.execute(
            update(CurrentRate).values(rates_data)
        )
        
        # Insertar en rate_history
        await session.execute(
            insert(RateHistory).values(rates_data)
        )
        
        # Commit automático al salir del contexto
```

#### 10. **Deployment Checklist**

- [ ] Tests pasando al 100%
- [ ] Cobertura de código > 80%
- [ ] Variables de entorno configuradas
- [ ] Logs configurados apropiadamente
- [ ] Health checks funcionando
- [ ] Migraciones de BD aplicadas
- [ ] Cache configurado
- [ ] Monitoring configurado
- [ ] Backup strategy definida
- [ ] Security headers configurados

### Comandos de Desarrollo Útiles

```bash
# Desarrollo local
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Ejecutar tests con coverage
pytest --cov=app --cov-report=html --cov-report=term

# Linting y formateo
black app/ tests/
flake8 app/ tests/
mypy app/

# Migraciones
alembic revision --autogenerate -m "Descripción del cambio"
alembic upgrade head

# Generar requirements
pip freeze > requirements.txt

# Análisis de seguridad
bandit -r app/
safety check
```

### Estructura de Código

- **FastAPI** para la API web con lifespan events
- **asyncpg** para conexiones a PostgreSQL
- **BeautifulSoup** para scraping del BCV
- **httpx** para llamadas HTTP asíncronas

### Agregar Nuevos Exchanges

1. Implementar función de scraping
2. Agregar endpoint en `/api/v1/rates/`
3. Integrar con sistema de guardado automático
4. Actualizar documentación

## 📝 Licencia

Este proyecto está bajo la **Licencia Apache 2.0**. Ver el archivo [LICENSE](LICENSE) para más detalles.

### Información de Licencia

- **Tipo**: Licencia Apache 2.0
- **Protección**: Incluye protección de patentes
- **Uso**: Permite uso comercial, modificación y distribución
- **Requisitos**: Mantener archivo LICENSE y NOTICE
- **Atribución**: Incluir copyright y avisos de licencia

### Archivos de Licencia

- `LICENSE` - Texto completo de la licencia Apache 2.0
- `NOTICE` - Atribuciones y avisos legales

Para más información sobre la licencia Apache 2.0, visita: https://www.apache.org/licenses/LICENSE-2.0

## 🤝 Contribuciones

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Para soporte técnico o preguntas:
- Crear un issue en GitHub
- Revisar la documentación en `/docs`
- Verificar el estado del sistema en `/api/v1/status`
