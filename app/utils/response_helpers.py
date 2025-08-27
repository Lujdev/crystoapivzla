"""Funciones helper para respuestas JSON consistentes

Este módulo proporciona funciones utilitarias para crear respuestas
JSON estandarizadas en toda la aplicación FastAPI.
"""

from datetime import datetime
from fastapi.responses import JSONResponse
from typing import Any, Optional


def create_success_response(
    data: Any, 
    message: str = "Operación exitosa", 
    status_code: int = 200
) -> JSONResponse:
    """
    Crear respuesta exitosa estándar
    
    Args:
        data: Datos a incluir en la respuesta
        message: Mensaje descriptivo de la operación
        status_code: Código de estado HTTP (por defecto 200)
    
    Returns:
        JSONResponse: Respuesta JSON estandarizada
    
    Example:
        >>> create_success_response({"id": 1, "name": "Test"}, "Usuario creado")
        JSONResponse con estructura estándar de éxito
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


def create_error_response(
    error_code: str, 
    message: str, 
    details: Optional[dict] = None, 
    status_code: int = 400
) -> JSONResponse:
    """
    Crear respuesta de error estándar
    
    Args:
        error_code: Código identificador del error
        message: Mensaje descriptivo del error
        details: Detalles adicionales del error (opcional)
        status_code: Código de estado HTTP (por defecto 400)
    
    Returns:
        JSONResponse: Respuesta JSON estandarizada de error
    
    Example:
        >>> create_error_response("USER_NOT_FOUND", "Usuario no encontrado", status_code=404)
        JSONResponse con estructura estándar de error
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    )


def create_validation_error_response(
    validation_errors: list, 
    message: str = "Error de validación"
) -> JSONResponse:
    """
    Crear respuesta de error de validación
    
    Args:
        validation_errors: Lista de errores de validación
        message: Mensaje principal del error
    
    Returns:
        JSONResponse: Respuesta JSON de error de validación
    
    Example:
        >>> create_validation_error_response([{"field": "email", "error": "formato inválido"}])
        JSONResponse con errores de validación
    """
    return create_error_response(
        error_code="VALIDATION_ERROR",
        message=message,
        details={"validation_errors": validation_errors},
        status_code=422
    )


def create_not_found_response(resource: str, identifier: str = "") -> JSONResponse:
    """
    Crear respuesta estándar para recurso no encontrado
    
    Args:
        resource: Tipo de recurso no encontrado
        identifier: Identificador del recurso (opcional)
    
    Returns:
        JSONResponse: Respuesta JSON de recurso no encontrado
    
    Example:
        >>> create_not_found_response("usuario", "123")
        JSONResponse con error de recurso no encontrado
    """
    message = f"{resource.capitalize()} no encontrado"
    if identifier:
        message += f" con ID: {identifier}"
    
    return create_error_response(
        error_code="RESOURCE_NOT_FOUND",
        message=message,
        details={"resource": resource, "identifier": identifier},
        status_code=404
    )


def create_server_error_response(
    error_message: str = "Error interno del servidor"
) -> JSONResponse:
    """
    Crear respuesta estándar para errores del servidor
    
    Args:
        error_message: Mensaje descriptivo del error
    
    Returns:
        JSONResponse: Respuesta JSON de error del servidor
    
    Example:
        >>> create_server_error_response("Error en la base de datos")
        JSONResponse con error del servidor
    """
    return create_error_response(
        error_code="INTERNAL_SERVER_ERROR",
        message=error_message,
        status_code=500
    )


def format_rate_data(rate_data: dict) -> dict:
    """
    Formatear datos de cotización para respuesta consistente
    
    Args:
        rate_data: Datos de cotización sin procesar
    
    Returns:
        dict: Datos de cotización formateados
    
    Example:
        >>> format_rate_data({"rate": 36.5, "source": "bcv"})
        Datos formateados con estructura estándar
    """
    return {
        "exchange_code": rate_data.get("exchange_code", "unknown"),
        "currency_pair": rate_data.get("currency_pair", "USD/VES"),
        "rate": float(rate_data.get("rate", 0)),
        "bid": rate_data.get("bid"),
        "ask": rate_data.get("ask"),
        "spread": rate_data.get("spread"),
        "volume_24h": rate_data.get("volume_24h"),
        "change_24h": rate_data.get("change_24h"),
        "last_updated": rate_data.get("last_updated"),
        "source": rate_data.get("source", "api"),
        "status": rate_data.get("status", "active")
    }


def format_market_summary(summary_data: dict) -> dict:
    """
    Formatear datos de resumen de mercado
    
    Args:
        summary_data: Datos de resumen sin procesar
    
    Returns:
        dict: Datos de resumen formateados
    
    Example:
        >>> format_market_summary({"bcv_rate": 36.5, "binance_rate": 37.2})
        Resumen de mercado formateado
    """
    return {
        "market_status": summary_data.get("market_status", "active"),
        "rates": summary_data.get("rates", {}),
        "spread_analysis": summary_data.get("spread_analysis", {}),
        "volume_24h": summary_data.get("volume_24h", {}),
        "price_changes": summary_data.get("price_changes", {}),
        "last_updated": summary_data.get("last_updated"),
        "data_sources": summary_data.get("data_sources", [])
    }


def format_currency_response(rate_data: dict) -> dict:
    """
    Formatear datos de cotización según formato específico solicitado
    
    Args:
        rate_data: Datos de cotización sin procesar
    
    Returns:
        dict: Datos de cotización formateados con campos específicos
    
    Example:
        >>> format_currency_response({"exchange_code": "binance_p2p", "buy_price": 207.84, ...})
        Datos formateados con estructura específica solicitada
    """
    return {
        "id": rate_data.get("id", 0),
        "exchange_code": rate_data.get("exchange_code", ""),
        "currency_pair": rate_data.get("currency_pair", ""),
        "base_currency": rate_data.get("base_currency", ""),
        "quote_currency": rate_data.get("quote_currency", ""),
        "buy_price": float(rate_data.get("buy_price", 0)) if rate_data.get("buy_price") is not None else 0.0,
        "sell_price": float(rate_data.get("sell_price", 0)) if rate_data.get("sell_price") is not None else 0.0,
        "avg_price": float(rate_data.get("avg_price", 0)) if rate_data.get("avg_price") is not None else 0.0,
        "volume_24h": float(rate_data.get("volume_24h", 0)) if rate_data.get("volume_24h") is not None else 0.0,
        "source": rate_data.get("source", ""),
        "trade_type": rate_data.get("trade_type", ""),
        "timestamp": rate_data.get("timestamp", ""),
        "variation_percentage": rate_data.get("variation_percentage", "0.00%"),
        "trend_main": rate_data.get("trend_main", "stable")
    }