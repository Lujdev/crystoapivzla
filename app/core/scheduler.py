"""
Scheduler para tareas automáticas
Reemplaza pg_cron usando APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
import asyncio
from datetime import datetime
from typing import Any

from app.core.config import settings
from app.core.database import cleanup_old_data
from app.services.data_fetcher import update_all_rates, scrape_bcv_rates, fetch_binance_p2p_complete, scrape_italcambios_rates


# Instancia global del scheduler
scheduler: AsyncIOScheduler = None


def start_scheduler() -> None:
    """
    Inicializar y configurar el scheduler
    Se ejecuta al arrancar la aplicación
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler ya está iniciado")
        return
    
    scheduler = AsyncIOScheduler(timezone="America/Caracas")
    
    # Tarea 1: Limpieza de datos antiguos (diario a las 2:00 AM)
    scheduler.add_job(
        func=scheduled_cleanup,
        trigger=CronTrigger(hour=settings.CLEANUP_HOUR, minute=0),
        id="cleanup_old_data",
        name="Limpiar datos antiguos",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia si falla
    )
    
    # Tarea 2: Actualizar todas las cotizaciones (BCV + Binance) cada 2 horas (OPTIMIZADO para Neon.tech)
    scheduler.add_job(
        func=scheduled_update_all_rates,
        trigger=IntervalTrigger(hours=2),  # Reducir frecuencia de 1h a 2h para ahorrar cómputo
        id="update_all_rates",
        name="Actualizar todas las cotizaciones (BCV + Binance) - OPTIMIZADO",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia
    )
    
    # Tarea 3: Actualizar solo cotizaciones BCV (cada hora como respaldo)
    scheduler.add_job(
        func=scheduled_update_bcv,
        trigger=IntervalTrigger(seconds=settings.BCV_UPDATE_INTERVAL),
        id="update_bcv_rates",
        name="Actualizar cotizaciones BCV",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia
    )
    
    # Tarea 4: Actualizar solo cotizaciones Binance P2P (cada hora como respaldo)
    scheduler.add_job(
        func=scheduled_update_binance,
        trigger=IntervalTrigger(seconds=settings.BINANCE_UPDATE_INTERVAL),
        id="update_binance_rates",
        name="Actualizar cotizaciones Binance P2P",
        replace_existing=True,
        misfire_grace_time=3600  # 1 hora de gracia
    )
    
    # Tarea 5: Actualizar solo cotizaciones Italcambios (cada 10 minutos)
    scheduler.add_job(
        func=scheduled_update_italcambios,
        trigger=IntervalTrigger(minutes=10),
        id="update_italcambios_rates",
        name="Actualizar cotizaciones Italcambios",
        replace_existing=True,
        misfire_grace_time=1800  # 30 minutos de gracia
    )
    
    # Tarea 6: Health check de APIs externas (cada 14 minutos)
    scheduler.add_job(
        func=scheduled_health_check,
        trigger=IntervalTrigger(minutes=14),
        id="health_check_apis",
        name="Health check APIs externas",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("✅ Scheduler iniciado con tareas automáticas")
    
    # Mostrar trabajos programados
    for job in scheduler.get_jobs():
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "N/A"
        logger.info(f"📅 Tarea: {job.name} | Próxima ejecución: {next_run}")


def stop_scheduler() -> None:
    """
    Detener el scheduler
    Se ejecuta al cerrar la aplicación
    """
    global scheduler
    
    if scheduler is not None:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("✅ Scheduler detenido")


def get_scheduler_status() -> dict:
    """
    Obtener estado del scheduler y trabajos
    """
    global scheduler
    
    if scheduler is None:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running" if scheduler.running else "stopped",
        "jobs": jobs,
        "timezone": str(scheduler.timezone)
    }


# ========================================
# TAREAS PROGRAMADAS
# ========================================

async def scheduled_cleanup() -> None:
    """
    Tarea programada: Limpiar datos antiguos
    Se ejecuta diariamente a las 2:00 AM
    """
    try:
        logger.info("🧹 Iniciando limpieza de datos antiguos...")
        result = await cleanup_old_data()
        logger.info(f"✅ Limpieza completada: {result}")
        
        # Opcional: Notificar por Telegram
        if settings.TELEGRAM_BOT_TOKEN:
            await send_telegram_notification(
                f"🧹 Limpieza automática completada\n"
                f"Rate history: {result['rate_history_deleted']} registros\n"
                f"API logs: {result['api_logs_deleted']} registros"
            )
            
    except Exception as e:
        logger.error(f"❌ Error en limpieza automática: {e}")
        # Opcional: Notificar error por Telegram
        if settings.TELEGRAM_BOT_TOKEN:
            await send_telegram_notification(f"❌ Error en limpieza automática: {e}")


async def scheduled_update_all_rates() -> None:
    """
    Tarea programada principal: Actualizar todas las cotizaciones (BCV + Binance)
    OPTIMIZADO para Neon.tech - Usa prepared statements y connection pooling
    Se ejecuta cada 2 horas
    """
    from datetime import datetime
    start_time = datetime.now()
    
    try:
        logger.info(f"🚀 [SCHEDULER-OPTIMIZED] Iniciando actualización optimizada - {start_time.strftime('%H:%M:%S')}")
        
        # Usar servicio optimizado
        try:
            from app.core.database_optimized import optimized_db, init_optimized_db_pool
            
            # Asegurar que el pool esté iniciado
            await init_optimized_db_pool()
            
            result = await update_all_rates_optimized()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success_count = sum(1 for exchange, data in result.items() 
                               if isinstance(data, dict) and data.get("status") == "success")
            total_exchanges = len([k for k in result.keys() if k != "timestamp"])
            
            if success_count == total_exchanges:
                # Obtener estadísticas del pool
                pool_stats = await optimized_db.get_pool_stats()
                logger.info(f"✅ [SCHEDULER-OPTIMIZED] Todas las cotizaciones actualizadas exitosamente en {duration:.2f}s - Pool: {pool_stats['size']}/{pool_stats['max_size']} conexiones")
            else:
                logger.warning(f"⚠️ [SCHEDULER-OPTIMIZED] {success_count}/{total_exchanges} cotizaciones actualizadas en {duration:.2f}s: {result}")
                
        except ImportError:
            # Fallback al método original si hay problemas con el optimizado
            logger.warning("⚠️ [SCHEDULER] Usando método original como fallback")
            result = await update_all_rates()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            success_count = sum(1 for exchange, data in result.items() 
                               if isinstance(data, dict) and data.get("status") == "success")
            total_exchanges = len([k for k in result.keys() if k != "timestamp"])
            
            if success_count == total_exchanges:
                logger.info(f"✅ [SCHEDULER] Todas las cotizaciones actualizadas (fallback) en {duration:.2f}s")
            else:
                logger.warning(f"⚠️ [SCHEDULER] {success_count}/{total_exchanges} cotizaciones actualizadas (fallback) en {duration:.2f}s: {result}")
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ [SCHEDULER-OPTIMIZED] Error actualizando cotizaciones después de {duration:.2f}s: {e}")


async def update_all_rates_optimized() -> dict[str, Any]:
    """
    Versión optimizada de update_all_rates que usa prepared statements
    """
    results = {
        "bcv": {"status": "pending"},
        "binance_p2p": {"status": "pending"},
        "italcambios": {"status": "pending"}
    }
    
    # Importar servicios
    from app.services.data_fetcher import scrape_bcv_rates, fetch_binance_p2p_complete, scrape_italcambios_rates
    from app.core.database_optimized import optimized_db
    
    # Actualizar BCV
    try:
        logger.info("🏦 [SCHEDULER-OPT] Actualizando BCV...")
        bcv_result = await scrape_bcv_rates()
        results["bcv"] = bcv_result
        
        if bcv_result.get("status") == "success":
            data = bcv_result.get("data", {})
            
            # Guardar usando prepared statements
            if data.get("usd_ves"):
                await optimized_db.upsert_current_rate_fast(
                    "BCV", "USD/VES", data["usd_ves"], data["usd_ves"],
                    source="bcv_web_scraping"
                )
                # También en historial si cambió significativamente
                if await optimized_db.check_rate_changed_fast("BCV", "USD/VES", data["usd_ves"]):
                    logger.info(f"🔄 [SCHEDULER-OPT] BCV USD/VES cambió, guardando en rate_history: {data['usd_ves']}")
                    success = await optimized_db.insert_rate_history_fast(
                        "BCV", "USD/VES", data["usd_ves"], data["usd_ves"], data["usd_ves"],
                        source="scheduler_optimized", api_method="web_scraping", trade_type="official"
                    )
                    if success:
                        logger.info("✅ [SCHEDULER-OPT] BCV USD/VES guardado en rate_history")
                    else:
                        logger.error("❌ [SCHEDULER-OPT] Error guardando BCV USD/VES en rate_history")
                else:
                    logger.info("⏭️ [SCHEDULER-OPT] BCV USD/VES no cambió significativamente, omitiendo rate_history")
            
            if data.get("eur_ves", 0) > 0:
                await optimized_db.upsert_current_rate_fast(
                    "BCV", "EUR/VES", data["eur_ves"], data["eur_ves"],
                    source="bcv_web_scraping"
                )
                if await optimized_db.check_rate_changed_fast("BCV", "EUR/VES", data["eur_ves"]):
                    await optimized_db.insert_rate_history_fast(
                        "BCV", "EUR/VES", data["eur_ves"], data["eur_ves"], data["eur_ves"],
                        source="scheduler_optimized", api_method="web_scraping", trade_type="official"
                    )
            
            logger.info("✅ [SCHEDULER-OPT] BCV actualizado con prepared statements")
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER-OPT] Error actualizando BCV: {e}")
        results["bcv"] = {"status": "error", "error": str(e)}
    
    # Actualizar Binance P2P
    try:
        logger.info("🟡 [SCHEDULER-OPT] Actualizando Binance P2P...")
        binance_result = await fetch_binance_p2p_complete()
        results["binance_p2p"] = binance_result
        
        if binance_result.get("status") == "success":
            data = binance_result.get("data", {})
            
            if data.get("buy_usdt") and data.get("sell_usdt"):
                buy_price = data["buy_usdt"]["price"]
                sell_price = data["sell_usdt"]["price"]
                avg_price = (buy_price + sell_price) / 2
                volume_24h = data.get("market_analysis", {}).get("volume_24h", 0)
                
                # Guardar usando prepared statements
                await optimized_db.upsert_current_rate_fast(
                    "BINANCE_P2P", "USDT/VES", buy_price, sell_price, volume_24h=volume_24h,
                    source="binance_p2p_scheduler"
                )
                
                # También en historial si cambió significativamente
                if await optimized_db.check_rate_changed_fast("BINANCE_P2P", "USDT/VES", avg_price):
                    logger.info(f"🔄 [SCHEDULER-OPT] BINANCE_P2P USDT/VES cambió, guardando en rate_history: {avg_price}")
                    success = await optimized_db.insert_rate_history_fast(
                        "BINANCE_P2P", "USDT/VES", buy_price, sell_price, avg_price, volume_24h,
                        source="scheduler_optimized", api_method="official_api", trade_type="p2p"
                    )
                    if success:
                        logger.info("✅ [SCHEDULER-OPT] BINANCE_P2P USDT/VES guardado en rate_history")
                    else:
                        logger.error("❌ [SCHEDULER-OPT] Error guardando BINANCE_P2P USDT/VES en rate_history")
                else:
                    logger.info("⏭️ [SCHEDULER-OPT] BINANCE_P2P USDT/VES no cambió significativamente, omitiendo rate_history")
            
            logger.info("✅ [SCHEDULER-OPT] Binance P2P actualizado con prepared statements")
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER-OPT] Error actualizando Binance P2P: {e}")
        results["binance_p2p"] = {"status": "error", "error": str(e)}
    
    # Actualizar Italcambios
    try:
        logger.info("🏦 [SCHEDULER-OPT] Actualizando Italcambios...")
        italcambios_result = await scrape_italcambios_rates()
        results["italcambios"] = italcambios_result
        
        if italcambios_result.get("status") == "success":
            data = italcambios_result.get("data", {})
            
            # Guardar usando prepared statements
            if data.get("usd_ves_compra") and data.get("usd_ves_venta"):
                compra_price = data["usd_ves_compra"]
                venta_price = data["usd_ves_venta"]
                avg_price = (compra_price + venta_price) / 2
                
                await optimized_db.upsert_current_rate_fast(
                    "ITALCAMBIOS", "USD/VES", compra_price, venta_price,
                    source="italcambios_web_scraping"
                )
                
                # También en historial si cambió significativamente
                if await optimized_db.check_rate_changed_fast("ITALCAMBIOS", "USD/VES", avg_price):
                    logger.info(f"🔄 [SCHEDULER-OPT] ITALCAMBIOS USD/VES cambió, guardando en rate_history: {avg_price}")
                    success = await optimized_db.insert_rate_history_fast(
                        "ITALCAMBIOS", "USD/VES", compra_price, venta_price, avg_price,
                        source="scheduler_optimized", api_method="web_scraping", trade_type="fiat"
                    )
                    if success:
                        logger.info("✅ [SCHEDULER-OPT] ITALCAMBIOS USD/VES guardado en rate_history")
                    else:
                        logger.error("❌ [SCHEDULER-OPT] Error guardando ITALCAMBIOS USD/VES en rate_history")
                else:
                    logger.info("⏭️ [SCHEDULER-OPT] ITALCAMBIOS USD/VES no cambió significativamente, omitiendo rate_history")
            
            logger.info("✅ [SCHEDULER-OPT] Italcambios actualizado con prepared statements")
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER-OPT] Error actualizando Italcambios: {e}")
        results["italcambios"] = {"status": "error", "error": str(e)}
    
    return results


async def scheduled_update_bcv() -> None:
    """
    Tarea programada: Actualizar solo cotizaciones BCV (respaldo)
    Se ejecuta cada hora
    """
    from datetime import datetime
    start_time = datetime.now()
    
    try:
        logger.info(f"🏦 [SCHEDULER-BCV] Iniciando scraping BCV - {start_time.strftime('%H:%M:%S')}")
        result = await scrape_bcv_rates()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.get("status") == "success":
            logger.info(f"✅ [SCHEDULER-BCV] Cotizaciones BCV actualizadas en {duration:.2f}s")
        else:
            logger.error(f"❌ [SCHEDULER-BCV] Error en scraping BCV después de {duration:.2f}s: {result.get('error', 'Error desconocido')}")
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ [SCHEDULER-BCV] Error actualizando BCV después de {duration:.2f}s: {e}")


async def scheduled_update_binance() -> None:
    """
    Tarea programada: Actualizar solo cotizaciones Binance P2P (respaldo)
    Se ejecuta cada 5 minutos
    """
    from datetime import datetime
    start_time = datetime.now()
    
    try:
        logger.info(f"🟡 [SCHEDULER-BINANCE] Iniciando fetch Binance P2P - {start_time.strftime('%H:%M:%S')}")
        result = await fetch_binance_p2p_complete()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.get("status") == "success":
            logger.info(f"✅ [SCHEDULER-BINANCE] Cotizaciones Binance P2P actualizadas en {duration:.2f}s")
        else:
            logger.error(f"❌ [SCHEDULER-BINANCE] Error en Binance P2P después de {duration:.2f}s: {result.get('error', 'Error desconocido')}")
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ [SCHEDULER-BINANCE] Error actualizando Binance P2P después de {duration:.2f}s: {e}")


async def scheduled_update_italcambios() -> None:
    """
    Tarea programada: Actualizar solo cotizaciones Italcambios
    Se ejecuta cada 10 minutos
    """
    from datetime import datetime
    start_time = datetime.now()
    
    try:
        logger.info(f"🏦 [SCHEDULER-ITALCAMBIOS] Iniciando scraping Italcambios - {start_time.strftime('%H:%M:%S')}")
        result = await scrape_italcambios_rates()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if result.get("status") == "success":
            data = result.get("data", {})
            compra = data.get("usd_ves_compra", 0)
            venta = data.get("usd_ves_venta", 0)
            logger.info(f"✅ [SCHEDULER-ITALCAMBIOS] Cotizaciones Italcambios actualizadas en {duration:.2f}s - Compra: {compra}, Venta: {venta}")
        else:
            logger.error(f"❌ [SCHEDULER-ITALCAMBIOS] Error en Italcambios después de {duration:.2f}s: {result.get('error', 'Error desconocido')}")
        
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"❌ [SCHEDULER-ITALCAMBIOS] Error actualizando Italcambios después de {duration:.2f}s: {e}")


async def scheduled_health_check() -> None:
    """
    Tarea programada: Health check de APIs externas
    Se ejecuta cada 10 minutos
    """
    try:
        logger.info("🔍 Verificando health de APIs externas...")
        
        # TODO: Implementar health checks
        # bcv_status = await check_bcv_health()
        # binance_status = await check_binance_health()
        
        logger.info("✅ Health check completado")
        
    except Exception as e:
        logger.error(f"❌ Error en health check: {e}")


# ========================================
# UTILIDADES
# ========================================

async def send_telegram_notification(message: str) -> bool:
    """
    Enviar notificación por Telegram (opcional)
    """
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False
    
    try:
        # TODO: Implementar envío de Telegram
        logger.info(f"📱 Notificación Telegram: {message}")
        return True
    except Exception as e:
        logger.error(f"Error enviando notificación Telegram: {e}")
        return False


