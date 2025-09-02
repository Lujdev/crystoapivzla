"""
Configuración optimizada de base de datos para Neon.tech
Reducir consumo de tiempo de cómputo con connection pooling y prepared statements
"""

import asyncpg
import asyncio
from typing import AsyncGenerator, Any
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import json

from app.core.config import settings

# Pool de conexiones global optimizado para Neon.tech
_connection_pool: asyncpg.Pool | None = None
_prepared_statements_cache: dict[str, str] = {}

# Configuración optimizada para Neon.tech
POOL_CONFIG = {
    "min_size": 2,          # Mínimo 2 conexiones (reducir de 5)
    "max_size": 8,          # Máximo 8 conexiones (reducir de 15)
    "max_queries": 50000,   # Cache de prepared statements
    "max_inactive_connection_lifetime": 300.0,  # 5 min (igual que antes)
    "command_timeout": 30,  # Timeout de comandos
    "server_settings": {
        "application_name": "crystoapivzla_optimized",
        "shared_preload_libraries": "",
    }
}

# Prepared statements para consultas frecuentes
PREPARED_QUERIES = {
    # Consultas de current_rates
    "get_current_rates": """
        SELECT cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price, 
               cr.variation_24h, cr.volume_24h, cr.last_update, cr.market_status
        FROM current_rates cr 
        WHERE cr.market_status = 'active'
        ORDER BY cr.exchange_code, cr.currency_pair
    """,
    
    "get_current_rate_by_exchange": """
        SELECT cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price,
               cr.variation_24h, cr.volume_24h, cr.last_update, cr.market_status
        FROM current_rates cr 
        WHERE cr.exchange_code = $1 AND cr.market_status = 'active'
        ORDER BY cr.currency_pair
    """,
    
    "get_current_rate_filtered": """
        SELECT cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price,
               cr.variation_24h, cr.volume_24h, cr.last_update, cr.market_status
        FROM current_rates cr 
        WHERE cr.exchange_code = $1 AND cr.currency_pair = $2 AND cr.market_status = 'active'
    """,
    
    # Operaciones de escritura optimizadas
    "upsert_current_rate": """
        INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price, 
                                 variation_24h, volume_24h, last_update, market_status)
        VALUES ($1, $2, $3, $4, $5, $6, NOW(), 'active')
        ON CONFLICT (exchange_code, currency_pair) 
        DO UPDATE SET 
            buy_price = EXCLUDED.buy_price,
            sell_price = EXCLUDED.sell_price,
            variation_24h = EXCLUDED.variation_24h,
            volume_24h = EXCLUDED.volume_24h,
            last_update = NOW(),
            market_status = 'active'
    """,
    
    # Rate history optimizado
    "insert_rate_history": """
        INSERT INTO rate_history (exchange_code, currency_pair, buy_price, sell_price, 
                                avg_price, volume_24h, source, api_method, trade_type)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
    """,
    
    "get_latest_rates": """
        SELECT exchange_code, currency_pair, buy_price, sell_price, avg_price,
               volume_24h, source, trade_type, timestamp
        FROM rate_history 
        ORDER BY timestamp DESC 
        LIMIT $1
    """,
    
    # Verificación de cambios optimizada
    "check_rate_changed": """
        SELECT buy_price, sell_price, avg_price
        FROM current_rates 
        WHERE exchange_code = $1 AND currency_pair = $2
        LIMIT 1
    """
}


async def init_optimized_db_pool() -> asyncpg.Pool:
    """
    Inicializar pool de conexiones optimizado para Neon.tech
    """
    global _connection_pool
    
    if _connection_pool is not None:
        logger.info("✅ Pool de conexiones ya está iniciado")
        return _connection_pool
    
    try:
        # Extraer componentes de la URL de Neon.tech
        database_url = settings.DATABASE_URL
        logger.info("🔄 Iniciando pool de conexiones optimizado para Neon.tech...")
        
        # Crear pool con configuración optimizada
        _connection_pool = await asyncpg.create_pool(
            database_url,
            **POOL_CONFIG
        )
        
        # Preparar statements frecuentes
        await _prepare_common_statements()
        
        logger.info(f"✅ Pool optimizado iniciado - Min: {POOL_CONFIG['min_size']}, Max: {POOL_CONFIG['max_size']}")
        logger.info(f"💾 {len(PREPARED_QUERIES)} prepared statements creados")
        
        return _connection_pool
        
    except Exception as e:
        logger.error(f"❌ Error inicializando pool optimizado: {e}")
        raise


async def _prepare_common_statements():
    """
    Preparar statements comunes para mejor rendimiento
    """
    global _connection_pool, _prepared_statements_cache
    
    try:
        async with _connection_pool.acquire() as conn:
            for stmt_name, query in PREPARED_QUERIES.items():
                try:
                    prepared = await conn.prepare(query)
                    _prepared_statements_cache[stmt_name] = query
                    logger.debug(f"✅ Prepared statement: {stmt_name}")
                except Exception as e:
                    logger.error(f"❌ Error preparing {stmt_name}: {e}")
                    
    except Exception as e:
        logger.error(f"❌ Error preparando statements: {e}")


async def close_optimized_db_pool():
    """
    Cerrar pool de conexiones optimizado
    """
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("✅ Pool de conexiones cerrado")


@asynccontextmanager
async def get_optimized_connection():
    """
    Context manager para obtener conexión del pool optimizado
    """
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = await init_optimized_db_pool()
    
    async with _connection_pool.acquire() as conn:
        try:
            yield conn
        except Exception as e:
            logger.error(f"❌ Error en conexión optimizada: {e}")
            raise


class OptimizedDatabaseService:
    """
    Servicio de base de datos optimizado para Neon.tech
    Usa asyncpg directo con prepared statements y connection pooling eficiente
    """
    
    @staticmethod
    async def get_current_rates_fast(
        exchange_code: str | None = None, 
        currency_pair: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Obtener current_rates usando prepared statements optimizados
        """
        try:
            async with get_optimized_connection() as conn:
                if exchange_code and currency_pair:
                    # Query más específico
                    stmt = await conn.prepare(PREPARED_QUERIES["get_current_rate_filtered"])
                    rows = await stmt.fetch(exchange_code.upper(), currency_pair.upper())
                elif exchange_code:
                    # Query por exchange
                    stmt = await conn.prepare(PREPARED_QUERIES["get_current_rate_by_exchange"])
                    rows = await stmt.fetch(exchange_code.upper())
                else:
                    # Query general
                    stmt = await conn.prepare(PREPARED_QUERIES["get_current_rates"])
                    rows = await stmt.fetch()
                
                return [
                    {
                        "exchange_code": row["exchange_code"],
                        "currency_pair": row["currency_pair"],
                        "buy_price": float(row["buy_price"]) if row["buy_price"] else None,
                        "sell_price": float(row["sell_price"]) if row["sell_price"] else None,
                        "variation_24h": float(row["variation_24h"]) if row["variation_24h"] else 0,
                        "volume_24h": float(row["volume_24h"]) if row["volume_24h"] else None,
                        "last_update": row["last_update"].isoformat() if row["last_update"] else None,
                        "market_status": row["market_status"]
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo current_rates optimizado: {e}")
            return []
    
    @staticmethod
    async def upsert_current_rate_fast(
        exchange_code: str,
        currency_pair: str, 
        buy_price: float,
        sell_price: float,
        variation_24h: float = 0,
        volume_24h: Optional[float] = None
    ) -> bool:
        """
        Insertar/actualizar current_rate usando prepared statement
        """
        try:
            async with get_optimized_connection() as conn:
                stmt = await conn.prepare(PREPARED_QUERIES["upsert_current_rate"])
                await stmt.fetchval(
                    exchange_code.upper(),
                    currency_pair.upper(), 
                    buy_price,
                    sell_price,
                    variation_24h,
                    volume_24h or 0
                )
                return True
                
        except Exception as e:
            logger.error(f"❌ Error upsert current_rate optimizado: {e}")
            return False
    
    @staticmethod
    async def insert_rate_history_fast(
        exchange_code: str,
        currency_pair: str,
        buy_price: float,
        sell_price: float,
        avg_price: float,
        volume_24h: Optional[float] = None,
        source: str = "api",
        api_method: str = "fetch",
        trade_type: str = "general"
    ) -> bool:
        """
        Insertar en rate_history usando prepared statement
        """
        try:
            async with get_optimized_connection() as conn:
                stmt = await conn.prepare(PREPARED_QUERIES["insert_rate_history"])
                await stmt.fetchval(
                    exchange_code.upper(),
                    currency_pair.upper(),
                    buy_price,
                    sell_price, 
                    avg_price,
                    volume_24h or 0,
                    source,
                    api_method,
                    trade_type
                )
                return True
                
        except Exception as e:
            logger.error(f"❌ Error insert rate_history optimizado: {e}")
            return False
    
    @staticmethod
    async def get_latest_rates_fast(limit: int = 100) -> List[dict[str, Any]]:
        """
        Obtener rate_history usando prepared statement
        """
        try:
            async with get_optimized_connection() as conn:
                stmt = await conn.prepare(PREPARED_QUERIES["get_latest_rates"])
                rows = await stmt.fetch(limit)
                
                return [
                    {
                        "exchange_code": row["exchange_code"],
                        "currency_pair": row["currency_pair"],
                        "buy_price": float(row["buy_price"]) if row["buy_price"] else None,
                        "sell_price": float(row["sell_price"]) if row["sell_price"] else None,
                        "avg_price": float(row["avg_price"]) if row["avg_price"] else None,
                        "volume_24h": float(row["volume_24h"]) if row["volume_24h"] else None,
                        "source": row["source"],
                        "trade_type": row["trade_type"],
                        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error get_latest_rates optimizado: {e}")
            return []
    
    @staticmethod
    async def check_rate_changed_fast(
        exchange_code: str, 
        currency_pair: str, 
        new_price: float,
        tolerance: float = 0.0001
    ) -> bool:
        """
        Verificar si una tasa cambió usando prepared statement
        """
        try:
            async with get_optimized_connection() as conn:
                stmt = await conn.prepare(PREPARED_QUERIES["check_rate_changed"])
                row = await stmt.fetchrow(exchange_code.upper(), currency_pair.upper())
                
                if not row:
                    return True  # Es nueva, insertar
                
                current_buy = float(row["buy_price"]) if row["buy_price"] else 0
                current_sell = float(row["sell_price"]) if row["sell_price"] else 0
                current_avg = float(row["avg_price"]) if row["avg_price"] else 0
                
                # Usar precio promedio para comparación
                current_price = current_avg or ((current_buy + current_sell) / 2) or current_buy or current_sell
                
                if current_price > 0:
                    price_diff = abs(new_price - current_price) / current_price
                    changed = price_diff > tolerance
                    
                    if changed:
                        logger.debug(f"🔄 Tasa cambió: {exchange_code} {currency_pair} - {price_diff*100:.2f}%")
                    
                    return changed
                
                return True  # Si no hay precio anterior, insertar
                
        except Exception as e:
            logger.error(f"❌ Error check_rate_changed optimizado: {e}")
            return True
    
    @staticmethod
    async def get_pool_stats() -> dict[str, Any]:
        """
        Obtener estadísticas del pool de conexiones
        """
        global _connection_pool
        
        if not _connection_pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "size": _connection_pool.get_size(),
            "min_size": _connection_pool.get_min_size(),
            "max_size": _connection_pool.get_max_size(),
            "idle_size": _connection_pool.get_idle_size(),
            "prepared_statements": len(_prepared_statements_cache)
        }


# Instancia global del servicio optimizado
optimized_db = OptimizedDatabaseService()
