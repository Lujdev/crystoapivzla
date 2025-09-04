"""
Endpoints para cotizaciones USDT/VES
BCV (fiat), Binance P2P (crypto) y ITALCAMBIOS (fiat)
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta

from app.services.data_fetcher import scrape_bcv_rates, scrape_italcambios_rates
from app.core.database_optimized import optimized_db
from app.utils.response_helpers import create_success_response, create_error_response, format_currency_response

router = APIRouter()


@router.get("/")
async def get_current_rates(
    exchange_code: Optional[str] = Query(None, description="Filtrar por exchange (bcv, binance_p2p, italcambios)"),
    currency_pair: Optional[str] = Query(None, description="Filtrar por par (USDT/VES, USD/VES)")
):
    """
    Obtener cotizaciones actuales de USDT/VES
    
    - **exchange_code**: Filtrar por exchange específico
    - **currency_pair**: Filtrar por par de monedas
    """
    try:
        # Usar la base de datos optimizada directamente
        rates_data = await optimized_db.get_current_rates_fast(
            exchange_code=exchange_code,
            currency_pair=currency_pair
        )
        
        # Formatear respuestas usando el helper existente
        formatted_rates = [format_currency_response(rate) for rate in rates_data]
        
        return create_success_response(
            data=formatted_rates,
            message=f"Se encontraron {len(formatted_rates)} cotizaciones"
        )
    except Exception as e:
        return create_error_response(
            error_code="RATES_FETCH_ERROR",
            message=f"Error obteniendo cotizaciones: {str(e)}",
            status_code=500
        )


@router.get("/scrape-bcv")
async def scrape_bcv_live():
    """
    Hacer scraping en tiempo real del BCV
    
    Endpoint para probar el web scraping del BCV
    """
    try:
        result = await scrape_bcv_rates()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en scraping del BCV: {str(e)}")


@router.get("/bcv")
async def get_bcv_rate():
    """
    Obtener cotización oficial del BCV
    
    Tasa oficial del Banco Central de Venezuela
    """
    try:
        # Obtener cotización de BCV usando la base de datos optimizada
        rates_data = await optimized_db.get_current_rates_fast(
            exchange_code="BCV",
            currency_pair="USD/VES"
        )
        
        if not rates_data:
            return create_error_response(
                error_code="RATE_NOT_FOUND",
                message="Cotización BCV no encontrada",
                status_code=404
            )
        
        # Formatear respuesta
        formatted_rate = format_currency_response(rates_data[0])
        
        return create_success_response(
            data=formatted_rate,
            message="Cotización BCV obtenida exitosamente"
        )
    except Exception as e:
        return create_error_response(
            error_code="BCV_FETCH_ERROR",
            message=f"Error obteniendo BCV: {str(e)}",
            status_code=500
        )


@router.get("/binance")
async def get_binance_rate():
    """
    Obtener cotización de Binance P2P Venezuela
    
    Mercado crypto peer-to-peer
    """
    try:
        # Obtener cotización de Binance P2P usando la base de datos optimizada
        rates_data = await optimized_db.get_current_rates_fast(
            exchange_code="BINANCE_P2P",
            currency_pair="USDT/VES"
        )
        
        if not rates_data:
            return create_error_response(
                error_code="RATE_NOT_FOUND",
                message="Cotización Binance P2P no encontrada",
                status_code=404
            )
        
        # Formatear respuesta
        formatted_rate = format_currency_response(rates_data[0])
        
        return create_success_response(
            data=formatted_rate,
            message="Cotización Binance P2P obtenida exitosamente"
        )
    except Exception as e:
        return create_error_response(
            error_code="BINANCE_FETCH_ERROR",
            message=f"Error obteniendo Binance P2P: {str(e)}",
            status_code=500
        )


@router.get("/italcambios")
async def get_italcambios_rate():
    """
    Obtener cotización de Italcambios
    
    Casa de cambio Italcambios - Cotizaciones USD/VES
    """
    try:
        # Obtener cotización de ITALCAMBIOS usando la base de datos optimizada
        rates_data = await optimized_db.get_current_rates_fast(
            exchange_code="ITALCAMBIOS",
            currency_pair="USD/VES"
        )
        
        if not rates_data:
            return create_error_response(
                error_code="RATE_NOT_FOUND",
                message="Cotización Italcambios no encontrada",
                status_code=404
            )
        
        # Formatear respuesta
        formatted_rate = format_currency_response(rates_data[0])
        
        return create_success_response(
            data=formatted_rate,
            message="Cotización Italcambios obtenida exitosamente"
        )
    except Exception as e:
        return create_error_response(
            error_code="ITALCAMBIOS_FETCH_ERROR",
            message=f"Error obteniendo Italcambios: {str(e)}",
            status_code=500
        )


@router.get("/scrape-italcambios")
async def scrape_italcambios_live():
    """
    Hacer scraping en tiempo real de Italcambios
    
    Endpoint para probar el web scraping de Italcambios
    Retorna las cotizaciones USD/VES obtenidas directamente del sitio web
    """
    try:
        # Obtener datos del scraping de Italcambios
        result = await scrape_italcambios_rates()
        
        if result.get("status") == "success":
            return create_success_response(
                data=result["data"],
                message="Scraping de Italcambios exitoso"
            )
        else:
            return create_error_response(
                error_code="SCRAPING_ERROR",
                message=f"Error en scraping: {result.get('error', 'Error desconocido')}",
                status_code=500
            )
    except Exception as e:
        return create_error_response(
            error_code="SCRAPING_EXCEPTION",
            message=f"Error en scraping de Italcambios: {str(e)}",
            status_code=500
        )


@router.get("/status")
async def get_rates_status():
    """
    Estado de las fuentes de datos
    
    Verifica el estado de:
    - BCV (web scraping)
    - Binance P2P (API)
    - ITALCAMBIOS (web scraping)
    - Última actualización
    """
    try:
        # Obtener estado de todas las fuentes
        bcv_data = await optimized_db.get_current_rates_fast(exchange_code="BCV", currency_pair="USD/VES")
        binance_data = await optimized_db.get_current_rates_fast(exchange_code="BINANCE_P2P", currency_pair="USDT/VES")
        italcambios_data = await optimized_db.get_current_rates_fast(exchange_code="ITALCAMBIOS", currency_pair="USD/VES")
        
        status = {
            "bcv": {
                "status": "active" if bcv_data else "inactive",
                "last_update": bcv_data[0]["timestamp"] if bcv_data else None,
                "rate": bcv_data[0]["buy_price"] if bcv_data else None
            },
            "binance_p2p": {
                "status": "active" if binance_data else "inactive", 
                "last_update": binance_data[0]["timestamp"] if binance_data else None,
                "rate": binance_data[0]["buy_price"] if binance_data else None
            },
            "italcambios": {
                "status": "active" if italcambios_data else "inactive",
                "last_update": italcambios_data[0]["timestamp"] if italcambios_data else None,
                "rate": italcambios_data[0]["buy_price"] if italcambios_data else None
            },
            "overall_status": "healthy" if all([bcv_data, binance_data, italcambios_data]) else "degraded"
        }
        
        return create_success_response(
            data=status,
            message="Estado de fuentes de datos obtenido"
        )
    except Exception as e:
        return create_error_response(
            error_code="STATUS_FETCH_ERROR",
            message=f"Error obteniendo estado: {str(e)}",
            status_code=500
        )