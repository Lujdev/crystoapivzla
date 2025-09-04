"""
Configuración optimizada de base de datos para Supabase
Connection pooling compatible con Supabase Transaction Mode (sin prepared statements)
"""

import asyncpg
import asyncio
from typing import AsyncGenerator, Any, Optional
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import json

from app.core.config import settings

# Pool de conexiones global optimizado para Supabase
_connection_pool: asyncpg.Pool | None = None
# Nota: Supabase Transaction Mode NO soporta prepared statements

# Configuración optimizada para Supabase Transaction Mode
POOL_CONFIG = {
    "min_size": 1,          # Mínimo 1 conexión (Supabase maneja el pooling)
    "max_size": 3,          # Máximo 3 conexiones (Transaction Mode es más eficiente)
    "max_queries": 1000,    # Reducido significativamente 
    "max_inactive_connection_lifetime": 60.0,  # 1 min (Transaction Mode es más eficiente)
    "command_timeout": 30,  # Timeout de comandos
    "server_settings": {
        "application_name": "crystoapivzla_supabase",
    }
}

# Consultas SQL reutilizables para Supabase (sin prepared statements)
# Nota: Supabase Transaction Mode no soporta prepared statements
OPTIMIZED_QUERIES = {
    # Consultas de current_rates con todos los campos necesarios
    "get_current_rates": """
        SELECT cr.id, cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price, cr.avg_price,
               cr.variation_24h, cr.volume_24h, cr.source, cr.market_status, cr.last_update,
               COALESCE(cp.base_currency, '') as base_currency, 
               COALESCE(cp.quote_currency, '') as quote_currency
        FROM current_rates cr 
        LEFT JOIN currency_pairs cp ON cr.currency_pair = cp.symbol
        WHERE cr.market_status = 'active'
        ORDER BY cr.exchange_code, cr.currency_pair
    """,
    
    "get_current_rate_by_exchange": """
        SELECT cr.id, cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price, cr.avg_price,
               cr.variation_24h, cr.volume_24h, cr.source, cr.market_status, cr.last_update,
               COALESCE(cp.base_currency, '') as base_currency, 
               COALESCE(cp.quote_currency, '') as quote_currency
        FROM current_rates cr 
        LEFT JOIN currency_pairs cp ON cr.currency_pair = cp.symbol
        WHERE cr.exchange_code = $1 AND cr.market_status = 'active'
        ORDER BY cr.currency_pair
    """,
    
    "get_current_rate_filtered": """
        SELECT cr.id, cr.exchange_code, cr.currency_pair, cr.buy_price, cr.sell_price, cr.avg_price,
               cr.variation_24h, cr.volume_24h, cr.source, cr.market_status, cr.last_update,
               COALESCE(cp.base_currency, '') as base_currency, 
               COALESCE(cp.quote_currency, '') as quote_currency
        FROM current_rates cr 
        LEFT JOIN currency_pairs cp ON cr.currency_pair = cp.symbol
        WHERE cr.exchange_code = $1 AND cr.currency_pair = $2 AND cr.market_status = 'active'
    """,
    
    # Operaciones de escritura optimizadas
    "upsert_current_rate": """
        INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price,
                                 variation_24h, volume_24h, source, last_update, market_status)
        VALUES ($1, $2, $3::DECIMAL, $4::DECIMAL, $5::DECIMAL, $6::DECIMAL, $7, NOW(), 'active')
        ON CONFLICT (exchange_code, currency_pair) 
        DO UPDATE SET 
            buy_price = EXCLUDED.buy_price,
            sell_price = EXCLUDED.sell_price,
            variation_24h = EXCLUDED.variation_24h,
            volume_24h = EXCLUDED.volume_24h,
            source = EXCLUDED.source,
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
    Inicializar pool de conexiones optimizado para Supabase Transaction Mode
    """
    global _connection_pool
    
    if _connection_pool is not None:
        logger.info("✅ Pool de conexiones ya está iniciado")
        return _connection_pool
    
    try:
        # URL de Supabase con Transaction Mode
        database_url = settings.database_url_async
        logger.info("🔄 Iniciando pool de conexiones optimizado para Supabase Transaction Mode...")
        
        # Crear pool con configuración optimizada para Supabase
        # IMPORTANTE: statement_cache_size=0 para deshabilitar prepared statements
        _connection_pool = await asyncpg.create_pool(
            database_url,
            statement_cache_size=0,  # CRITICAL: Deshabilitar prepared statements para Supabase Transaction Mode
            **POOL_CONFIG
        )
        
        # NOTA: NO preparar statements (Supabase Transaction Mode no los soporta)
        
        logger.info(f"✅ Pool Supabase iniciado - Min: {POOL_CONFIG['min_size']}, Max: {POOL_CONFIG['max_size']}")
        logger.info("ℹ️ Transaction Mode: prepared statements deshabilitados")
        
        return _connection_pool
        
    except Exception as e:
        logger.error(f"❌ Error inicializando pool de Supabase: {e}")
        raise


# Función eliminada: _prepare_common_statements()
# Supabase Transaction Mode no soporta prepared statements


async def close_optimized_db_pool():
    """
    Cerrar pool de conexiones optimizado
    """
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None
        logger.info("✅ Pool de conexiones cerrado")


async def get_pool() -> Optional[asyncpg.Pool]:
    """
    Obtener pool de conexiones optimizado para Supabase
    """
    global _connection_pool
    
    if _connection_pool is None:
        await init_optimized_db_pool()
    
    return _connection_pool


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
    Servicio de base de datos optimizado para Supabase Transaction Mode
    Usa asyncpg directo con connection pooling eficiente (sin prepared statements)
    """
    
    @staticmethod
    async def get_current_rates_fast(
        exchange_code: str | None = None, 
        currency_pair: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Obtener current_rates usando queries optimizadas para Supabase Transaction Mode
        """
        try:
            async with get_optimized_connection() as conn:
                if exchange_code and currency_pair:
                    # Query más específico
                    rows = await conn.fetch(OPTIMIZED_QUERIES["get_current_rate_filtered"], exchange_code.upper(), currency_pair.upper())
                elif exchange_code:
                    # Query por exchange
                    rows = await conn.fetch(OPTIMIZED_QUERIES["get_current_rate_by_exchange"], exchange_code.upper())
                else:
                    # Query general
                    rows = await conn.fetch(OPTIMIZED_QUERIES["get_current_rates"])
                
                return [
                    {
                        "id": int(row["id"]) if row["id"] else 0,
                        "exchange_code": row["exchange_code"] or "",
                        "currency_pair": row["currency_pair"] or "",
                        "base_currency": row["base_currency"] or "",
                        "quote_currency": row["quote_currency"] or "",
                        "buy_price": float(row["buy_price"]) if row["buy_price"] else 0.0,
                        "sell_price": float(row["sell_price"]) if row["sell_price"] else 0.0,
                        "avg_price": float(row["avg_price"]) if row["avg_price"] else 0.0,
                        "variation_24h": float(row["variation_24h"]) if row["variation_24h"] else 0,
                        "volume_24h": float(row["volume_24h"]) if row["volume_24h"] else 0.0,
                        "source": row["source"] or "api",
                        "trade_type": "general",  # Campo fijo para compatibilidad
                        "timestamp": row["last_update"].isoformat() if row["last_update"] else "",
                        "market_status": row["market_status"] or "active",
                        "variation_percentage": f"{float(row['variation_24h']) if row['variation_24h'] else 0:+.2f}%",
                        "trend_main": "stable" if not row["variation_24h"] or float(row["variation_24h"]) == 0 
                                     else ("up" if float(row["variation_24h"]) > 0 else "down")
                    }
                    for row in rows
                ]
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo current_rates de Supabase: {e}")
            return []
    
    @staticmethod
    async def upsert_current_rate_fast(
        exchange_code: str | None = None,
        currency_pair: str | None = None, 
        buy_price: float | None = None,
        sell_price: float | None = None,
        variation_24h: float = 0,
        volume_24h: float | None = None,
        source: str = "api",
        data: dict | None = None
    ) -> bool:
        """
        Insertar/actualizar current_rate usando query directa en Supabase
        Soporta tanto parámetros individuales como diccionario de datos
        """
        try:
            # Si se proporciona un diccionario de datos, extraer los valores
            if data:
                if isinstance(data, dict):
                    # Manejar diferentes formatos de datos según la fuente
                    if 'usd_ves_compra' in data and 'usd_ves_venta' in data:
                        # Formato de ITALCAMBIOS
                        exchange_code = data.get('source', 'ITALCAMBIOS').upper()
                        currency_pair = 'USD/VES'
                        buy_price = data['usd_ves_compra']
                        sell_price = data['usd_ves_venta']
                        source = data.get('scraping_method', 'web_scraping')
                    elif 'usd_ves' in data and 'eur_ves' in data:
                        # Formato de BCV - Necesitamos hacer dos upserts: uno para USD/VES y otro para EUR/VES
                        # Primero USD/VES
                        await OptimizedDatabaseService._upsert_single_rate(
                            data.get('source', 'BCV').upper(),
                            'USD/VES',
                            data['usd_ves'],
                            data['usd_ves'],  # BCV tiene un solo precio
                            data.get('scraping_method', 'web_scraping')
                        )
                        # Luego EUR/VES
                        await OptimizedDatabaseService._upsert_single_rate(
                            data.get('source', 'BCV').upper(),
                            'EUR/VES',
                            data['eur_ves'],
                            data['eur_ves'],  # BCV tiene un solo precio
                            data.get('scraping_method', 'web_scraping')
                        )
                        return True  # Ya se guardaron ambos pares
                    elif 'usdt_ves_buy' in data and 'usdt_ves_sell' in data:
                        # Formato de Binance P2P (formato individual)
                        exchange_code = data.get('source', 'BINANCE_P2P').upper()
                        currency_pair = 'USDT/VES'
                        buy_price = data['usdt_ves_buy']
                        sell_price = data['usdt_ves_sell']
                        source = data.get('api_method', 'official_api')
                    elif 'buy_usdt' in data and 'sell_usdt' in data:
                        # Formato de Binance P2P (formato completo)
                        exchange_code = data.get('source', 'BINANCE_P2P').upper()
                        currency_pair = 'USDT/VES'
                        buy_price = data['buy_usdt']['price']
                        sell_price = data['sell_usdt']['price']
                        source = data.get('api_method', 'official_api')
                    else:
                        # Formato genérico
                        exchange_code = data.get('exchange_code', data.get('source', 'UNKNOWN')).upper()
                        currency_pair = data.get('currency_pair', 'USD/VES')
                        buy_price = data.get('buy_price', data.get('usd_ves_compra', 0))
                        sell_price = data.get('sell_price', data.get('usd_ves_venta', 0))
                        source = data.get('source', 'api')
            
            # Validar parámetros requeridos
            if not exchange_code or not currency_pair or buy_price is None or sell_price is None:
                logger.error(f"❌ Parámetros insuficientes para upsert: exchange_code={exchange_code}, currency_pair={currency_pair}, buy_price={buy_price}, sell_price={sell_price}")
                return False
            
            async with get_optimized_connection() as conn:
                await conn.fetchval(
                    OPTIMIZED_QUERIES["upsert_current_rate"],
                    exchange_code.upper(),
                    currency_pair.upper(), 
                    buy_price,
                    sell_price,
                    variation_24h,
                    volume_24h or 0,
                    source
                )
                return True
                
        except Exception as e:
            logger.error(f"❌ Error upsert current_rate en Supabase: {e}")
            return False
    
    @staticmethod
    async def insert_rate_history_fast(
        exchange_code: str,
        currency_pair: str,
        buy_price: float,
        sell_price: float,
        avg_price: float,
        volume_24h: float | None = None,
        source: str = "api",
        api_method: str = "fetch",
        trade_type: str = "general"
    ) -> bool:
        """
        Insertar en rate_history usando query directa en Supabase
        """
        try:
            async with get_optimized_connection() as conn:
                await conn.fetchval(
                    OPTIMIZED_QUERIES["insert_rate_history"],
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
            logger.error(f"❌ Error insert rate_history en Supabase: {e}")
            return False
    
    @staticmethod
    async def get_latest_rates_fast(limit: int = 100) -> list[dict[str, Any]]:
        """
        Obtener rate_history usando query directa en Supabase
        """
        try:
            async with get_optimized_connection() as conn:
                rows = await conn.fetch(OPTIMIZED_QUERIES["get_latest_rates"], limit)
                
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
            logger.error(f"❌ Error get_latest_rates en Supabase: {e}")
            return []
    
    @staticmethod
    async def check_rate_changed_fast(
        exchange_code: str, 
        currency_pair: str, 
        new_price: float,
        tolerance: float = 0.0001
    ) -> bool:
        """
        Verificar si una tasa cambió usando query directa en Supabase
        """
        try:
            async with get_optimized_connection() as conn:
                row = await conn.fetchrow(OPTIMIZED_QUERIES["check_rate_changed"], exchange_code.upper(), currency_pair.upper())
                
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
            logger.error(f"❌ Error check_rate_changed en Supabase: {e}")
            return True
    
    @staticmethod
    async def _upsert_single_rate(
        exchange_code: str,
        currency_pair: str,
        buy_price: float,
        sell_price: float,
        source: str,
        variation_24h: float = 0,
        volume_24h: float = 0
    ) -> bool:
        """
        Método auxiliar para hacer upsert de un solo par de monedas
        """
        try:
            async with get_optimized_connection() as conn:
                await conn.fetchval(
                    OPTIMIZED_QUERIES["upsert_current_rate"],
                    exchange_code.upper(),
                    currency_pair.upper(), 
                    buy_price,
                    sell_price,
                    variation_24h,
                    volume_24h,
                    source
                )
                return True
        except Exception as e:
            logger.error(f"❌ Error upsert single rate {exchange_code} {currency_pair}: {e}")
            return False

    @staticmethod
    async def get_pool_stats() -> dict[str, Any]:
        """
        Obtener estadísticas del pool de conexiones Supabase
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
            "mode": "transaction_mode",
            "prepared_statements": 0  # Disabled in Transaction Mode
        }


# Instancia global del servicio optimizado
optimized_db = OptimizedDatabaseService()
