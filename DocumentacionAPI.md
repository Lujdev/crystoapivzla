# Documentación API - CrystoAPIVzla

## Información General

**Nombre:** CrystoAPIVzla API Simple  
**Versión:** 1.0.0  
**Descripción:** API simplificada para cotizaciones USDT/VES en tiempo real  
**Base URL:** `http://localhost:8000` (desarrollo) / `https://tu-dominio.com` (producción)  
**Documentación Interactiva:** `/docs` (Swagger UI) y `/redoc` (ReDoc)  

### Fuentes de Datos
- **BCV (Banco Central de Venezuela):** Cotizaciones oficiales USD/VES y EUR/VES
- **Binance P2P:** Cotizaciones USDT/VES del mercado peer-to-peer

### Formato de Respuesta Estándar

Todas las respuestas siguen un formato JSON consistente:

**Respuesta Exitosa:**
```json
{
  "success": true,
  "data": {},
  "message": "Operación exitosa",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Respuesta de Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Descripción del error",
    "details": {}
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Endpoints de la API

### 1. Endpoints Básicos

#### GET `/`
**Descripción:** Endpoint raíz de la API  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "success": true,
  "data": {
    "message": "CrystoAPIVzla API Simple",
    "version": "1.0.0",
    "description": "Cotizaciones USDT/VES en tiempo real",
    "sources": ["BCV", "Binance P2P"],
    "docs": "/docs",
    "status": "operational",
    "environment": "development"
  },
  "message": "API funcionando correctamente",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/health`
**Descripción:** Health check para verificar el estado del servicio  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "service": "crystoapivzla",
    "message": "Service is running",
    "environment": "development",
    "database_url": "configured"
  },
  "message": "Servicio funcionando correctamente",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/status`
**Descripción:** Estado detallado del sistema  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "success": true,
  "data": {
    "service": "crystoapivzla",
    "version": "1.0.0",
    "environment": "development",
    "database_configured": true
  },
  "message": "Estado del sistema obtenido exitosamente",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/config`
**Descripción:** Configuración del sistema (sin información sensible)  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "success": true,
  "data": {
    "environment": "development",
    "log_level": "INFO",
    "api_debug": "false",
    "scheduler_enabled": "true",
    "redis_enabled": "false",
    "bcv_api_url": "not_configured",
    "binance_api_url": "not_configured"
  },
  "message": "Configuración obtenida exitosamente",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 2. Endpoints de Cotizaciones

#### GET `/api/v1/rates/current`
**Descripción:** Obtener cotizaciones actuales  
**Parámetros de Query:**
- `exchange_code` (opcional): Filtrar por exchange (ej: "BCV", "BINANCE_P2P")
- `currency_pair` (opcional): Filtrar por par de monedas (ej: "USD/VES", "USDT/VES")

**Ejemplo de Consulta:**
```
GET /api/v1/rates/current
GET /api/v1/rates/current?exchange_code=BCV
GET /api/v1/rates/current?currency_pair=USD/VES
GET /api/v1/rates/current?exchange_code=BINANCE_P2P&currency_pair=USDT/VES
```

**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "exchange_code": "BCV",
      "currency_pair": "USD/VES",
      "base_currency": "USD",
      "quote_currency": "VES",
      "buy_price": 36.50,
      "sell_price": 36.50,
      "avg_price": 36.50,
      "volume": null,
      "volume_24h": null,
      "source": "bcv",
      "api_method": "web_scraping",
      "trade_type": "official",
      "timestamp": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "auto_saved_to_history": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/history`
**Descripción:** Obtener historial de cotizaciones  
**Parámetros de Query:**
- `limit` (opcional): Número máximo de registros (default: 100)

**Ejemplo de Consulta:**
```
GET /api/v1/rates/history
GET /api/v1/rates/history?limit=50
```

**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "exchange_code": "BCV",
      "currency_pair": "USD/VES",
      "buy_price": 36.50,
      "sell_price": 36.50,
      "avg_price": 36.50,
      "volume_24h": null,
      "source": "bcv",
      "api_method": "web_scraping",
      "trade_type": "official",
      "timestamp": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "limit": 100,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/summary`
**Descripción:** Resumen del mercado con estadísticas  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "total_exchanges": 2,
    "total_currency_pairs": 3,
    "last_update": "2024-01-01T00:00:00Z",
    "exchanges": {
      "BCV": {
        "currency_pairs": ["USD/VES", "EUR/VES"],
        "last_update": "2024-01-01T00:00:00Z"
      },
      "BINANCE_P2P": {
        "currency_pairs": ["USDT/VES"],
        "last_update": "2024-01-01T00:00:00Z"
      }
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 3. Endpoints de Binance P2P

#### GET `/api/v1/rates/binance-p2p`
**Descripción:** Cotizaciones de compra USDT/VES en Binance P2P  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "trade_type": "BUY",
    "asset": "USDT",
    "fiat": "VES",
    "price": 36.85,
    "advertiser": "Usuario123",
    "min_amount": 100,
    "max_amount": 5000,
    "payment_methods": ["Transferencia bancaria"],
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/binance-p2p/sell`
**Descripción:** Cotizaciones de venta USDT/VES en Binance P2P  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "trade_type": "SELL",
    "asset": "USDT",
    "fiat": "VES",
    "price": 36.75,
    "advertiser": "Usuario456",
    "min_amount": 50,
    "max_amount": 3000,
    "payment_methods": ["Pago móvil"],
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/binance-p2p/complete`
**Descripción:** Cotizaciones completas de Binance P2P (compra y venta)  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "buy_usdt": {
      "trade_type": "BUY",
      "asset": "USDT",
      "fiat": "VES",
      "price": 36.85,
      "advertiser": "Usuario123",
      "min_amount": 100,
      "max_amount": 5000,
      "payment_methods": ["Transferencia bancaria"]
    },
    "sell_usdt": {
      "trade_type": "SELL",
      "asset": "USDT",
      "fiat": "VES",
      "price": 36.75,
      "advertiser": "Usuario456",
      "min_amount": 50,
      "max_amount": 3000,
      "payment_methods": ["Pago móvil"]
    },
    "spread": 0.10,
    "spread_percentage": 0.27,
    "avg_price": 36.80,
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/binance`
**Descripción:** Cotización simplificada de Binance (alias para binance-p2p)  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "exchange_code": "binance_p2p",
    "currency_pair": "USDT/VES",
    "base_currency": "USDT",
    "quote_currency": "VES",
    "buy_price": 36.85,
    "sell_price": 36.75,
    "avg_price": 36.80,
    "source": "binance_p2p",
    "api_method": "official_api",
    "trade_type": "p2p",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 4. Endpoints del BCV

#### GET `/api/v1/rates/scrape-bcv`
**Descripción:** Scraping en tiempo real del BCV  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "usd_ves": 36.50,
    "eur_ves": 39.75,
    "source": "BCV",
    "url": "https://www.bcv.org.ve/",
    "exchange_code": "BCV",
    "base_currency": "USD",
    "database_info": {
      "exchange_code": "BCV",
      "base_currency": "USD",
      "source": "database"
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/rates/bcv`
**Descripción:** Cotización oficial del BCV formateada  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "exchange_code": "bcv",
    "currency_pair": "USD/VES",
    "base_currency": "USD",
    "quote_currency": "VES",
    "buy_price": 36.50,
    "sell_price": 36.50,
    "avg_price": 36.50,
    "volume": null,
    "volume_24h": null,
    "source": "bcv",
    "api_method": "web_scraping",
    "trade_type": "official",
    "timestamp": "2024-01-01T00:00:00Z",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

### 5. Endpoints de Comparación y Análisis

#### GET `/api/v1/rates/compare`
**Descripción:** Comparar cotizaciones entre BCV y Binance P2P  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "bcv": {
      "exchange_code": "bcv",
      "currency_pair": "USD/VES",
      "base_currency": "USD",
      "quote_currency": "VES",
      "usd_ves": 36.50,
      "eur_ves": 39.75,
      "timestamp": "2024-01-01T00:00:00Z"
    },
    "binance_p2p": {
      "exchange_code": "binance_p2p",
      "currency_pair": "USDT/VES",
      "base_currency": "USDT",
      "quote_currency": "VES",
      "usdt_ves_buy": 36.85,
      "usdt_ves_sell": 36.75,
      "usdt_ves_avg": 36.80,
      "timestamp": "2024-01-01T00:00:00Z"
    },
    "analysis": {
      "spread_bcv_binance": -0.30,
      "spread_percentage": -0.82,
      "timestamp": "2024-01-01T00:00:00Z"
    }
  },
  "auto_saved_to_history": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET `/api/v1/exchanges`
**Descripción:** Lista de exchanges disponibles  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": [
    {
      "name": "Banco Central de Venezuela",
      "code": "BCV",
      "type": "official",
      "description": "Cotizaciones oficiales del gobierno",
      "is_active": true
    },
    {
      "name": "Binance P2P",
      "code": "BINANCE_P2P",
      "type": "crypto",
      "description": "Mercado P2P de criptomonedas",
      "is_active": true
    }
  ],
  "count": 2
}
```

---

### 6. Endpoints de Estado y Administración

#### GET `/api/v1/rates/status`
**Descripción:** Estado de las cotizaciones y fuentes de datos  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "total_rates": 3,
    "exchanges_status": {
      "BCV": {
        "rates_count": 2,
        "last_update": "2024-01-01T00:00:00Z",
        "currency_pairs": ["USD/VES", "EUR/VES"]
      },
      "BINANCE_P2P": {
        "rates_count": 1,
        "last_update": "2024-01-01T00:00:00Z",
        "currency_pairs": ["USDT/VES"]
      }
    },
    "last_update": "2024-01-01T00:00:00Z",
    "data_sources": {
      "bcv": {
        "status": "active",
        "last_check": "2024-01-01T00:00:00Z"
      },
      "binance_p2p": {
        "status": "active",
        "last_check": "2024-01-01T00:00:00Z"
      }
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### POST `/api/v1/rates/refresh`
**Descripción:** Forzar actualización de cotizaciones  
**Parámetros de Query:**
- `exchange_code` (opcional): Exchange específico a actualizar ("bcv" o "binance_p2p")

**Ejemplo de Consulta:**
```
POST /api/v1/rates/refresh
POST /api/v1/rates/refresh?exchange_code=bcv
POST /api/v1/rates/refresh?exchange_code=binance_p2p
```

**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "message": "Actualización iniciada",
    "exchanges_updated": ["bcv", "binance_p2p"],
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### GET `/api/v1/rates/auto-save-status`
**Descripción:** Estado del guardado automático en el historial  
**Parámetros:** Ninguno  
**Respuesta:**
```json
{
  "status": "success",
  "data": {
    "auto_save_enabled": true,
    "database_available": true,
    "total_records_in_history": 1250,
    "exchange_statistics": [
      {
        "exchange_code": "BCV",
        "total_records": 800,
        "last_update": "2024-01-01T00:00:00Z",
        "first_update": "2023-12-01T00:00:00Z"
      },
      {
        "exchange_code": "BINANCE_P2P",
        "total_records": 450,
        "last_update": "2024-01-01T00:00:00Z",
        "first_update": "2023-12-01T00:00:00Z"
      }
    ],
    "latest_records": [
      {
        "exchange_code": "BCV",
        "currency_pair": "USD/VES",
        "avg_price": 36.50,
        "timestamp": "2024-01-01T00:00:00Z",
        "source": "bcv"
      }
    ],
    "daily_statistics": [
      {
        "date": "2024-01-01",
        "records_count": 48,
        "exchanges_count": 2
      }
    ],
    "auto_save_endpoints": [
      "/api/v1/rates/current",
      "/api/v1/rates/summary",
      "/api/v1/rates/compare"
    ]
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

---

## Códigos de Estado HTTP

- **200 OK:** Solicitud exitosa
- **400 Bad Request:** Error en los parámetros de la solicitud
- **404 Not Found:** Endpoint no encontrado
- **500 Internal Server Error:** Error interno del servidor
- **503 Service Unavailable:** Servicio temporalmente no disponible

---

## Códigos de Error Comunes

- `HEALTH_CHECK_ERROR`: Error en el health check del servicio
- `DATABASE_ERROR`: Error de conexión o consulta a la base de datos
- `SCRAPING_ERROR`: Error en el scraping de datos externos
- `BINANCE_API_ERROR`: Error al consultar la API de Binance
- `RATE_NOT_FOUND`: Cotización no encontrada
- `INVALID_PARAMETERS`: Parámetros de consulta inválidos

---

## Notas Importantes

1. **Guardado Automático:** Los endpoints `/api/v1/rates/current`, `/api/v1/rates/summary` y `/api/v1/rates/compare` guardan automáticamente las cotizaciones en el historial.

2. **Tolerancia de Cambios:** Las cotizaciones solo se guardan en el historial si hay un cambio significativo (tolerancia: 0.0001).

3. **Fuentes de Datos:**
   - **BCV:** Web scraping de la página oficial
   - **Binance P2P:** API oficial de Binance

4. **Limitaciones de Rate:**
   - No hay límites específicos implementados
   - Se recomienda no hacer más de 60 solicitudes por minuto

5. **Formato de Fechas:** Todas las fechas están en formato ISO 8601 UTC

6. **Monedas Soportadas:**
   - USD/VES (BCV)
   - EUR/VES (BCV)
   - USDT/VES (Binance P2P)

---

## Ejemplos de Uso

### Obtener todas las cotizaciones actuales
```bash
curl -X GET "http://localhost:8000/api/v1/rates/current"
```

### Obtener solo cotizaciones del BCV
```bash
curl -X GET "http://localhost:8000/api/v1/rates/current?exchange_code=BCV"
```

### Comparar BCV vs Binance P2P
```bash
curl -X GET "http://localhost:8000/api/v1/rates/compare"
```

### Forzar actualización de datos
```bash
curl -X POST "http://localhost:8000/api/v1/rates/refresh"
```

### Obtener historial limitado
```bash
curl -X GET "http://localhost:8000/api/v1/rates/history?limit=50"
```

---

## Contacto y Soporte

Para soporte técnico o reportar problemas, consulte la documentación interactiva en `/docs` o revise los logs del sistema.