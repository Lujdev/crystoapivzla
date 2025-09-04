"""
Servicio para operaciones de base de datos
"""

from loguru import logger
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

# Importar servicios optimizados para Supabase
from app.core.database_optimized import optimized_db
from app.models.rate_models import RateHistory, CurrentRate
from app.models.exchange_models import Exchange, CurrencyPair
from app.models.api_models import ApiLog
from app.services.cache_service import cache_service

class DatabaseService:
    """
    Servicio para operaciones CRUD en la base de datos
    """
    
    @staticmethod
    async def save_bcv_rates(usd_ves: float, eur_ves: float, source_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones del BCV usando OptimizedDatabaseService (compatible con Supabase)
        """
        try:
            # Usar OptimizedDatabaseService para Supabase Transaction Mode
            success_usd = await optimized_db.upsert_current_rate_fast(
                "BCV", "USD/VES", usd_ves, usd_ves, 0.0, 0.0, "bcv_scrape"
            )
            
            success_eur = await optimized_db.upsert_current_rate_fast(
                "BCV", "EUR/VES", eur_ves, eur_ves, 0.0, 0.0, "bcv_scrape"
            )
            
            if success_usd and success_eur:
                # Invalidar caché Redis después de guardar nuevos datos
                cache_service.invalidate_all()
                logger.debug("🗑️ Caché Redis invalidado después de guardar BCV rates")
                
                logger.info(f"✅ BCV rates guardados: USD={usd_ves}, EUR={eur_ves}")
                return True
            else:
                logger.error("❌ Error guardando BCV rates con OptimizedDatabaseService")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error guardando BCV rates: {e}")
            return False
    
    @staticmethod
    async def save_binance_p2p_rates(binance_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones de Binance P2P (un precio a la vez)
        """
        try:
            async for session in get_db_session():
                # Extraer datos
                buy_price = binance_data.get("usdt_ves_buy")
                sell_price = binance_data.get("usdt_ves_sell")
                avg_price = binance_data.get("usdt_ves_avg")
                volume = binance_data.get("volume_24h")
                source = binance_data.get("source", "binance_p2p")
                
                if buy_price:
                    # Guardar precio de compra
                    buy_history = RateHistory(
                        exchange_code="BINANCE_P2P",
                        currency_pair="USDT/VES",
                        buy_price=buy_price,
                        sell_price=None,
                        avg_price=avg_price,
                        volume_24h=volume,
                        source=source,
                        api_method="official_api",
                        trade_type="buy_usdt",
                        timestamp=datetime.now()
                    )
                    session.add(buy_history)
                
                if sell_price:
                    # Guardar precio de venta
                    sell_history = RateHistory(
                        exchange_code="BINANCE_P2P",
                        currency_pair="USDT/VES",
                        buy_price=None,
                        sell_price=sell_price,
                        avg_price=avg_price,
                        volume_24h=volume,
                        source=source,
                        api_method="official_api",
                        trade_type="sell_usdt",
                        timestamp=datetime.now()
                    )
                    session.add(sell_history)
                
                # Actualizar cotizaciones actuales
                # Si solo tenemos un precio, usarlo para ambos campos temporalmente
                if buy_price or sell_price:
                    # Si solo tenemos buy_price, usarlo como sell_price también
                    # Si solo tenemos sell_price, usarlo como buy_price también
                    final_buy_price = buy_price if buy_price else sell_price
                    final_sell_price = sell_price if sell_price else buy_price
                    
                    await optimized_db.upsert_current_rate_fast(
                        "BINANCE_P2P", "USDT/VES", final_buy_price, final_sell_price, 0.0, volume, "binance_p2p"
                    )
                
                await session.commit()
                
                # Invalidar caché Redis después de guardar nuevos datos
                cache_service.invalidate_all()
                logger.debug("🗑️ Caché Redis invalidado después de guardar Binance P2P rates")
                
                logger.info(f"✅ Binance P2P rates guardados: Buy={buy_price}, Sell={sell_price}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error guardando Binance P2P rates: {e}")
            return False

    @staticmethod
    async def save_binance_p2p_complete_rates(binance_data: Dict[str, Any]) -> bool:
        """
        Guardar cotizaciones completas de Binance P2P usando OptimizedDatabaseService
        """
        try:
            # Obtener precios de compra y venta
            buy_data = binance_data.get("buy_usdt", {})
            sell_data = binance_data.get("sell_usdt", {})
            
            buy_price = buy_data.get("price", 0)
            sell_price = sell_data.get("price", 0)
            
            if buy_price > 0 and sell_price > 0:
                # Calcular promedio general
                general_avg = (buy_price + sell_price) / 2
                volume_24h = binance_data.get("market_analysis", {}).get("volume_24h", 0)
                
                # Usar OptimizedDatabaseService para Supabase Transaction Mode
                success = await optimized_db.upsert_current_rate_fast(
                    "BINANCE_P2P", "USDT/VES", 
                    buy_price, sell_price, 0.0, volume_24h, "binance_p2p_complete"
                )
                
                if success:
                    logger.info(f"✅ Binance P2P COMPLETE rates guardados: Buy={buy_price}, Sell={sell_price}, Avg={general_avg}")
                    return True
                else:
                    logger.error("❌ Error guardando Binance P2P COMPLETE rates con OptimizedDatabaseService")
                    return False
            else:
                logger.warning(f"⚠️ No se pudieron obtener ambos precios para actualizar current_rates")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error guardando Binance P2P COMPLETE rates: {e}")
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
            async for session in get_db_session():
                stmt = select(CurrentRate).options(
                    selectinload(CurrentRate.exchange),
                    selectinload(CurrentRate.currency_pair_rel)
                ).where(CurrentRate.market_status == "active")
                
                result = await session.execute(stmt)
                current_rates = result.scalars().all()
                
                rates_with_variation = []
                for rate in current_rates:
                    # Calcular variación avanzada con diferentes períodos de tiempo
                    # Calcular variación usando OptimizedDatabaseService
                    variation_data = {"variation_24h": 0.0, "variation_percentage": "0.00%"}
                    
                    # Formatear variaciones como porcentajes con símbolo %
                    variation_main_formatted = f"{variation_data['variation_main']:+.2f}%" if variation_data['variation_main'] != 0 else "0.00%"
                    variation_1h_formatted = f"{variation_data['variation_1h']:+.2f}%" if variation_data['variation_1h'] != 0 else "0.00%"
                    variation_24h_formatted = f"{variation_data['variation_24h']:+.2f}%" if variation_data['variation_24h'] != 0 else "0.00%"
                    
                    rates_with_variation.append({
                        "exchange_code": rate.exchange_code,
                        "currency_pair": rate.currency_pair,
                        "base_currency": rate.currency_pair_rel.base_currency if rate.currency_pair_rel else None,
                        "quote_currency": rate.currency_pair_rel.quote_currency if rate.currency_pair_rel else None,
                        "buy_price": rate.buy_price,
                        "sell_price": rate.sell_price,
                        "avg_price": rate.avg_price,
                        "volume_24h": rate.volume_24h,
                        "source": rate.source,
                        "last_update": rate.last_update.isoformat() if rate.last_update else None,
                        "market_status": rate.market_status,
                        "variation_percentage": variation_main_formatted,  # Usar la variación principal (último valor registrado)
                        "variation_1h": variation_1h_formatted,
                        "variation_24h": variation_24h_formatted,
                        "variation_main_raw": variation_data["variation_main"],  # Valor numérico para cálculos
                        "variation_1h_raw": variation_data["variation_1h"],  # Valor numérico para cálculos
                        "variation_24h_raw": variation_data["variation_24h"],  # Valor numérico para cálculos
                        "trend_main": variation_data["trend_main"],  # Tendencia principal
                        "trend_1h": variation_data["trend_1h"],
                        "trend_24h": variation_data["trend_24h"]
                    })
                
                # Almacenar en caché Redis (TTL configurado en settings)
                cache_service.set_current_rates(rates_with_variation)
                logger.debug("💾 Cotizaciones actuales almacenadas en caché Redis")
                
                return rates_with_variation
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo current rates: {e}")
            return []
    
    @staticmethod
    async def _calculate_variation_percentage(session, exchange_code: str, currency_pair: str, current_price: float) -> float:
        """
        Calcular el porcentaje de variación basado en la diferencia entre los dos últimos valores de rate_history
        """
        try:
            from sqlalchemy import select, func
            from app.models.rate_models import RateHistory
            
            # Obtener los dos últimos precios registrados en rate_history para este exchange y currency_pair
            stmt = select(RateHistory.avg_price).where(
                RateHistory.exchange_code == exchange_code,
                RateHistory.currency_pair == currency_pair
            ).order_by(RateHistory.timestamp.desc()).limit(2)
            
            result = await session.execute(stmt)
            price_rows = result.fetchall()
            
            if len(price_rows) >= 2:
                last_price = float(price_rows[0][0])  # Primer precio (más reciente)
                second_last_price = float(price_rows[1][0])  # Segundo precio (penúltimo)
                
                if second_last_price > 0:
                    # Calcular variación porcentual entre los dos últimos valores
                    variation = ((last_price - second_last_price) / second_last_price) * 100
                    return round(variation, 4)
            
            return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculando variación para {exchange_code} {currency_pair}: {e}")
            return 0.0
    
    @staticmethod
    async def log_api_call(
        endpoint: str,
        method: str,
        status_code: int,
        source: Optional[str] = None,
        operation_type: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        request_data: Optional[Dict] = None,
        response_data: Optional[Dict] = None
    ) -> None:
        """
        Registrar llamada a la API
        """
        try:
            async for session in get_db_session():
                api_log = ApiLog(
                    endpoint=endpoint,
                    method=method,
                    status_code=status_code,
                    source=source,
                    operation_type=operation_type,
                    response_time_ms=response_time_ms,
                    request_data=request_data,
                    response_data=response_data,
                    success=status_code < 400,
                    timestamp=datetime.now()
                )
                
                session.add(api_log)
                await session.commit()
                
        except Exception as e:
            logger.error(f"❌ Error loggeando API call: {e}")
    
    @staticmethod
    async def cleanup_old_data() -> Dict[str, int]:
        """
        Limpiar datos antiguos
        """
        try:
            async for session in get_db_session():
                # Limpiar rate_history > 90 días
                stmt = delete(RateHistory).where(
                    RateHistory.timestamp < datetime.now() - timedelta(days=90)
                )
                result1 = await session.execute(stmt)
                
                # Limpiar api_logs > 30 días
                stmt2 = delete(ApiLog).where(
                    ApiLog.timestamp < datetime.now() - timedelta(days=30)
                )
                result2 = await session.execute(stmt2)
                
                await session.commit()
                
                return {
                    "rate_history_deleted": result1.rowcount,
                    "api_logs_deleted": result2.rowcount,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error en cleanup: {e}")
            return {"error": str(e)}
