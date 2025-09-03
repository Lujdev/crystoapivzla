"""
Servicio para operaciones de base de datos usando asyncpg directo
Compatible con Supabase Transaction Mode
"""

from loguru import logger
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from app.core.database_optimized import get_pool
from app.services.cache_service import cache_service


class DatabaseServiceAsyncpg:
    """
    Servicio para operaciones CRUD usando asyncpg directo
    Compatible con Supabase Transaction Mode sin prepared statements
    """
    
    @staticmethod
    async def save_bcv_rates(usd_ves: float, eur_ves: float, source_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones del BCV usando asyncpg directo
        """
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                
                # Upsert BCV USD/VES
                usd_query = """
                INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price, 
                                         variation_24h, volume_24h, last_update, market_status, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (exchange_code, currency_pair)
                DO UPDATE SET
                    buy_price = EXCLUDED.buy_price,
                    sell_price = EXCLUDED.sell_price,
                    variation_24h = EXCLUDED.variation_24h,
                    last_update = EXCLUDED.last_update,
                    source = EXCLUDED.source
                """
                
                await conn.execute(
                    usd_query,
                    "BCV", "USD/VES", usd_ves, usd_ves,
                    source_data.get("usd_variation", 0.0),
                    0.0, datetime.utcnow(), "active", "bcv_direct"
                )
                
                # Upsert BCV EUR/VES
                eur_query = """
                INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price, 
                                         variation_24h, volume_24h, last_update, market_status, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (exchange_code, currency_pair)
                DO UPDATE SET
                    buy_price = EXCLUDED.buy_price,
                    sell_price = EXCLUDED.sell_price,
                    variation_24h = EXCLUDED.variation_24h,
                    last_update = EXCLUDED.last_update,
                    source = EXCLUDED.source
                """
                
                await conn.execute(
                    eur_query,
                    "BCV", "EUR/VES", eur_ves, eur_ves,
                    source_data.get("eur_variation", 0.0),
                    0.0, datetime.utcnow(), "active", "bcv_direct"
                )
                
                # Insertar en historial también
                history_query = """
                INSERT INTO rate_history (exchange_code, currency_pair, buy_price, sell_price, 
                                        avg_price, volume_24h, source, api_method, trade_type, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                # Historial USD
                await conn.execute(
                    history_query,
                    "BCV", "USD/VES", usd_ves, usd_ves, usd_ves,
                    0.0, "bcv_direct", "web_scraping", "official", datetime.utcnow()
                )
                
                # Historial EUR
                await conn.execute(
                    history_query,
                    "BCV", "EUR/VES", eur_ves, eur_ves, eur_ves,
                    0.0, "bcv_direct", "web_scraping", "official", datetime.utcnow()
                )
                
                logger.info(f"✅ BCV rates guardadas: USD/VES={usd_ves}, EUR/VES={eur_ves}")
                
                # Invalidar caché
                cache_service.invalidate_current_rates()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando BCV rates: {e}")
            return False
    
    @staticmethod
    async def save_binance_rates(rates_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones de Binance P2P usando asyncpg directo
        """
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                
                # Extraer datos
                buy_price = rates_data.get("usdt_ves_buy")
                sell_price = rates_data.get("usdt_ves_sell")
                avg_price = (buy_price + sell_price) / 2 if buy_price and sell_price else buy_price or sell_price
                volume = rates_data.get("volume_24h", 0.0)
                variation = rates_data.get("variation_24h", 0.0)
                
                # Upsert Binance P2P USDT/VES
                query = """
                INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price, 
                                         variation_24h, volume_24h, last_update, market_status, source)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (exchange_code, currency_pair)
                DO UPDATE SET
                    buy_price = EXCLUDED.buy_price,
                    sell_price = EXCLUDED.sell_price,
                    variation_24h = EXCLUDED.variation_24h,
                    volume_24h = EXCLUDED.volume_24h,
                    last_update = EXCLUDED.last_update,
                    source = EXCLUDED.source
                """
                
                await conn.execute(
                    query,
                    "BINANCE_P2P", "USDT/VES", buy_price, sell_price,
                    variation, volume, datetime.utcnow(), "active", "binance_p2p_api"
                )
                
                # Insertar en historial
                history_query = """
                INSERT INTO rate_history (exchange_code, currency_pair, buy_price, sell_price, 
                                        avg_price, volume_24h, source, api_method, trade_type, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """
                
                await conn.execute(
                    history_query,
                    "BINANCE_P2P", "USDT/VES", buy_price, sell_price, avg_price,
                    volume, "binance_p2p_api", "official_api", "p2p", datetime.utcnow()
                )
                
                logger.info(f"✅ Binance P2P rates guardadas: USDT/VES buy={buy_price}, sell={sell_price}")
                
                # Invalidar caché
                cache_service.invalidate_current_rates()
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando Binance P2P rates: {e}")
            return False
    
    @staticmethod
    async def get_current_rates() -> List[Dict[str, Any]]:
        """
        Obtener cotizaciones actuales con caché Redis
        """
        try:
            # Intentar obtener desde caché Redis primero
            cached_rates = cache_service.get_current_rates()
            if cached_rates:
                logger.debug("✅ Cotizaciones actuales obtenidas desde caché Redis")
                return cached_rates.get("rates", [])
            
            # Si no hay caché, obtener desde base de datos
            logger.debug("📊 Obteniendo cotizaciones actuales desde base de datos")
            pool = await get_pool()
            
            async with pool.acquire() as conn:
                query = """
                SELECT exchange_code, currency_pair, buy_price, sell_price, avg_price,
                       variation_24h, volume_24h, last_update, market_status, source
                FROM current_rates
                WHERE market_status = 'active'
                ORDER BY exchange_code, currency_pair
                """
                
                rows = await conn.fetch(query)
                
                rates_data = []
                for row in rows:
                    rate_dict = {
                        "exchange_code": row["exchange_code"],
                        "currency_pair": row["currency_pair"], 
                        "buy_price": float(row["buy_price"]) if row["buy_price"] else None,
                        "sell_price": float(row["sell_price"]) if row["sell_price"] else None,
                        "avg_price": float(row["avg_price"]) if row["avg_price"] else None,
                        "variation_24h": float(row["variation_24h"]) if row["variation_24h"] else 0.0,
                        "volume_24h": float(row["volume_24h"]) if row["volume_24h"] else 0.0,
                        "last_update": row["last_update"].isoformat() if row["last_update"] else None,
                        "market_status": row["market_status"],
                        "source": row["source"]
                    }
                    rates_data.append(rate_dict)
                
                # Guardar en caché Redis
                if rates_data:
                    cache_service.set_current_rates(rates_data)
                    logger.debug("💾 Cotizaciones actuales guardadas en caché Redis")
                
                return rates_data
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo cotizaciones actuales: {e}")
            return []
    
    @staticmethod
    async def get_latest_rates(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtener las últimas cotizaciones con caché Redis
        """
        try:
            # Intentar obtener desde caché Redis primero
            cached_rates = cache_service.get_latest_rates(limit)
            if cached_rates:
                logger.debug("✅ Latest rates obtenidas desde caché Redis")
                return cached_rates.get("rates", [])
            
            # Si no hay caché, obtener desde base de datos
            logger.debug("📊 Obteniendo latest rates desde base de datos")
            pool = await get_pool()
            
            async with pool.acquire() as conn:
                query = """
                SELECT exchange_code, currency_pair, buy_price, sell_price, avg_price,
                       volume_24h, source, api_method, trade_type, timestamp
                FROM rate_history
                ORDER BY timestamp DESC
                LIMIT $1
                """
                
                rows = await conn.fetch(query, limit)
                
                rates_data = []
                for row in rows:
                    rate_dict = {
                        "exchange_code": row["exchange_code"],
                        "currency_pair": row["currency_pair"],
                        "buy_price": float(row["buy_price"]) if row["buy_price"] else None,
                        "sell_price": float(row["sell_price"]) if row["sell_price"] else None,
                        "avg_price": float(row["avg_price"]) if row["avg_price"] else None,
                        "volume_24h": float(row["volume_24h"]) if row["volume_24h"] else 0.0,
                        "source": row["source"],
                        "api_method": row["api_method"],
                        "trade_type": row["trade_type"],
                        "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None
                    }
                    rates_data.append(rate_dict)
                
                # Guardar en caché Redis
                if rates_data:
                    cache_service.set_latest_rates(rates_data, limit)
                    logger.debug("💾 Latest rates guardadas en caché Redis")
                
                return rates_data
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo latest rates: {e}")
            return []


# Instancia global para usar en place del DatabaseService original
database_service_asyncpg = DatabaseServiceAsyncpg()
