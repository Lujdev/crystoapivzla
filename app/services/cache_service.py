"""Servicio de caché Redis para optimizar el rendimiento de la API
Maneja el almacenamiento y recuperación de datos de cotizaciones
"""

import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings


class CacheService:
    """
    Servicio para operaciones de caché con Redis
    Optimiza el rendimiento almacenando datos frecuentemente consultados
    """
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = settings.REDIS_ENABLED
        
    def connect(self) -> None:
        """
        Establecer conexión con Redis
        """
        if not self.enabled:
            logger.info("Redis está deshabilitado en la configuración")
            return
            
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            self.redis_client.ping()
            logger.info(f"Conexión a Redis establecida: {settings.REDIS_URL}")
            
        except Exception as e:
            logger.error(f"Error conectando a Redis: {e}")
            self.enabled = False
            self.redis_client = None
    
    def disconnect(self) -> None:
        """
        Cerrar conexión con Redis
        """
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Conexión a Redis cerrada")
            except Exception as e:
                logger.error(f"Error cerrando conexión Redis: {e}")
            finally:
                self.redis_client = None
    
    def _generate_key(self, prefix: str, identifier: str = "") -> str:
        """
        Generar clave única para Redis
        
        Args:
            prefix: Prefijo de la clave (ej: 'current_rates', 'latest_rates')
            identifier: Identificador adicional opcional
            
        Returns:
            Clave formateada para Redis
        """
        base_key = f"crystodolar:{prefix}"
        if identifier:
            base_key += f":{identifier}"
        return base_key
    
    def set_current_rates(self, rates_data: Dict[str, Any]) -> bool:
        """
        Almacenar cotizaciones actuales en caché
        
        Args:
            rates_data: Datos de cotizaciones a almacenar
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            key = self._generate_key("current_rates")
            
            # Agregar timestamp
            cache_data = {
                "data": rates_data,
                "timestamp": datetime.utcnow().isoformat(),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Almacenar con TTL
            self.redis_client.setex(
                key,
                settings.REDIS_TTL_CURRENT_RATES,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            logger.debug(f"Cotizaciones actuales almacenadas en caché: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error almacenando cotizaciones actuales en caché: {e}")
            return False
    
    def get_current_rates(self) -> Optional[Dict[str, Any]]:
        """
        Recuperar cotizaciones actuales del caché
        
        Returns:
            Datos de cotizaciones si están en caché, None en caso contrario
        """
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("current_rates")
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Cotizaciones actuales recuperadas del caché: {key}")
                return data["data"]
                
            return None
            
        except Exception as e:
            logger.error(f"Error recuperando cotizaciones actuales del caché: {e}")
            return None
    
    def set_latest_rates(self, rates_data: List[Dict[str, Any]]) -> bool:
        """
        Almacenar últimas cotizaciones en caché
        
        Args:
            rates_data: Lista de cotizaciones históricas
            
        Returns:
            True si se almacenó correctamente, False en caso contrario
        """
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            key = self._generate_key("latest_rates")
            
            # Agregar metadata
            cache_data = {
                "data": rates_data,
                "count": len(rates_data),
                "timestamp": datetime.utcnow().isoformat(),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Almacenar con TTL
            self.redis_client.setex(
                key,
                settings.REDIS_TTL_LATEST_RATES,
                json.dumps(cache_data, ensure_ascii=False)
            )
            
            logger.debug(f"Últimas cotizaciones almacenadas en caché: {key} ({len(rates_data)} registros)")
            return True
            
        except Exception as e:
            logger.error(f"Error almacenando últimas cotizaciones en caché: {e}")
            return False
    
    def get_latest_rates(self) -> Optional[List[Dict[str, Any]]]:
        """
        Recuperar últimas cotizaciones del caché
        
        Returns:
            Lista de cotizaciones si están en caché, None en caso contrario
        """
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            key = self._generate_key("latest_rates")
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Últimas cotizaciones recuperadas del caché: {key} ({data.get('count', 0)} registros)")
                return data["data"]
                
            return None
            
        except Exception as e:
            logger.error(f"Error recuperando últimas cotizaciones del caché: {e}")
            return None
    
    def invalidate_all(self) -> bool:
        """
        Invalidar todo el caché de cotizaciones
        
        Returns:
            True si se invalidó correctamente, False en caso contrario
        """
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            # Buscar todas las claves de CrystoDolar
            pattern = self._generate_key("*")
            keys = self.redis_client.keys(pattern)
            
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Caché invalidado: {deleted_count} claves eliminadas")
                return True
            else:
                logger.info("No hay claves de caché para invalidar")
                return True
                
        except Exception as e:
            logger.error(f"Error invalidando caché: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del caché
        
        Returns:
            Diccionario con estadísticas del caché
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "connected": False,
                "keys_count": 0,
                "memory_usage": "N/A"
            }
            
        try:
            # Contar claves de CrystoDolar
            pattern = self._generate_key("*")
            keys = self.redis_client.keys(pattern)
            
            # Obtener información de Redis
            info = self.redis_client.info()
            
            return {
                "enabled": True,
                "connected": True,
                "keys_count": len(keys),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "redis_version": info.get("redis_version", "N/A"),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del caché: {e}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e)
            }


# Instancia global del servicio de caché
cache_service = CacheService()