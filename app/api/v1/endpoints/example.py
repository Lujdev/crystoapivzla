#!/usr/bin/env python3
"""
Endpoint de ejemplo que demuestra las reglas del proyecto
Copyright 2024 CrystoAPIVzla Team
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from datetime import datetime

from app.utils.response_helpers import (
    create_success_response,
    create_error_response,
    create_validation_error_response,
    create_not_found_response,
    create_server_error_response
)

router = APIRouter()

@router.get("/example/success")
async def example_success_response():
    """
    Ejemplo de respuesta exitosa estándar.
    
    Demuestra el uso de create_success_response con datos estructurados.
    """
    data = {
        "message": "Este es un ejemplo de respuesta exitosa",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "Respuestas JSON consistentes",
            "Manejo de errores estandarizado",
            "Documentación automática"
        ],
        "status_info": {
            "service": "crystoapivzla",
            "version": "1.0.0",
            "environment": "development"
        }
    }
    return create_success_response(data, "Ejemplo ejecutado exitosamente")

@router.get("/example/error")
async def example_error_response():
    """
    Ejemplo de respuesta de error estándar.
    
    Demuestra el uso de create_error_response para errores controlados.
    """
    return create_error_response(
        "EXAMPLE_ERROR",
        "Este es un ejemplo de error controlado",
        {"error_type": "demonstration", "recoverable": True},
        400
    )

@router.get("/example/validation/{item_id}")
async def example_validation_error(item_id: str):
    """
    Ejemplo de validación con respuesta de error.
    
    Demuestra validación de parámetros y respuesta de error apropiada.
    """
    if not item_id.isdigit():
        return create_validation_error_response(
            [{"field": "item_id", "error": "debe ser numérico", "provided_value": item_id}],
            "El ID del item debe ser numérico"
        )
    
    item_id_int = int(item_id)
    if item_id_int <= 0:
        return create_validation_error_response(
            [{"field": "item_id", "error": "debe ser mayor que 0", "provided_value": item_id}],
            "El ID del item debe ser mayor que 0"
        )
    
    # Simular que el item no existe si el ID es mayor a 100
    if item_id_int > 100:
        return create_not_found_response(
            "item",
            str(item_id_int)
        )
    
    # Respuesta exitosa para IDs válidos
    data = {
        "item_id": item_id_int,
        "name": f"Item de ejemplo {item_id_int}",
        "description": "Este es un item de demostración",
        "created_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    return create_success_response(data, f"Item {item_id_int} encontrado exitosamente")

@router.get("/example/server-error")
async def example_server_error():
    """
    Ejemplo de manejo de errores del servidor.
    
    Demuestra el uso de create_server_error_response para errores internos.
    """
    try:
        # Simular un error interno
        raise Exception("Error simulado para demostración")
    except Exception as e:
        return create_server_error_response(
            "INTERNAL_SERVER_ERROR",
            f"Error interno del servidor: {str(e)}"
        )

@router.get("/example/data-processing")
async def example_data_processing(limit: Optional[int] = 10):
    """
    Ejemplo de procesamiento de datos con parámetros opcionales.
    
    Demuestra el manejo de parámetros de consulta y respuestas estructuradas.
    """
    try:
        # Validar límite
        if limit <= 0 or limit > 1000:
            return create_validation_error_response(
                "INVALID_LIMIT",
                "El límite debe estar entre 1 y 1000",
                {"provided_limit": limit, "valid_range": "1-1000"}
            )
        
        # Simular procesamiento de datos
        processed_data = []
        for i in range(1, min(limit + 1, 11)):
            processed_data.append({
                "id": i,
                "value": f"Dato procesado {i}",
                "timestamp": datetime.utcnow().isoformat(),
                "processed": True
            })
        
        response_data = {
            "total_processed": len(processed_data),
            "requested_limit": limit,
            "data": processed_data,
            "processing_info": {
                "algorithm": "example_processor_v1",
                "execution_time_ms": 42,
                "success_rate": 100.0
            }
        }
        
        return create_success_response(
            response_data,
            f"Procesados {len(processed_data)} elementos exitosamente"
        )
        
    except Exception as e:
        return create_server_error_response(
            "DATA_PROCESSING_ERROR",
            f"Error durante el procesamiento de datos: {str(e)}"
        )