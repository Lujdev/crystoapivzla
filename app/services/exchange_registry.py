"""
Registry de exchanges para manejo escalable y dinámico
Patrón Factory para agregar nuevos exchanges sin modificar código
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime

from app.core.database_optimized import optimized_db


class ExchangeType(Enum):
    """Tipos de exchanges soportados"""
    FIAT = "fiat"
    CRYPTO = "crypto"
    P2P = "p2p"


@dataclass
class ExchangeConfig:
    """Configuración de un exchange"""
    code: str
    name: str
    type: ExchangeType
    description: str
    is_active: bool = True
    update_frequency_minutes: int = 30
    fetcher_function: Optional[Callable] = None
    data_processor: Optional[Callable] = None
    icon: str = "🏦"  # Emoji para identificación visual


class ExchangeRegistry:
    """Registry centralizado para manejo de exchanges"""
    
    def __init__(self):
        self._exchanges: Dict[str, ExchangeConfig] = {}
        self._register_default_exchanges()
    
    def _register_default_exchanges(self):
        """Registrar exchanges por defecto"""
        # BCV
        self.register_exchange(ExchangeConfig(
            code="BCV",
            name="Banco Central de Venezuela",
            type=ExchangeType.FIAT,
            description="Cotizaciones oficiales del gobierno",
            icon="🏛️",
            update_frequency_minutes=60
        ))
        
        # Binance P2P
        self.register_exchange(ExchangeConfig(
            code="BINANCE_P2P",
            name="Binance P2P",
            type=ExchangeType.CRYPTO,
            description="Mercado P2P de criptomonedas",
            icon="🟡",
            update_frequency_minutes=15
        ))
        
        # Italcambios
        self.register_exchange(ExchangeConfig(
            code="ITALCAMBIOS",
            name="Italcambios",
            type=ExchangeType.FIAT,
            description="Casa de cambio Italcambios - Cotizaciones USD/VES",
            icon="🏦",
            update_frequency_minutes=30
        ))
    
    def register_exchange(self, config: ExchangeConfig):
        """Registrar un nuevo exchange"""
        self._exchanges[config.code.upper()] = config
        print(f"✅ Exchange registrado: {config.name} ({config.code})")
    
    def get_exchange(self, code: str) -> Optional[ExchangeConfig]:
        """Obtener configuración de un exchange"""
        return self._exchanges.get(code.upper())
    
    def get_all_exchanges(self) -> List[ExchangeConfig]:
        """Obtener todos los exchanges registrados"""
        return list(self._exchanges.values())
    
    def get_active_exchanges(self) -> List[ExchangeConfig]:
        """Obtener solo exchanges activos"""
        return [ex for ex in self._exchanges.values() if ex.is_active]
    
    def get_exchanges_by_type(self, exchange_type: ExchangeType) -> List[ExchangeConfig]:
        """Obtener exchanges por tipo"""
        return [ex for ex in self._exchanges.values() if ex.type == exchange_type and ex.is_active]
    
    def get_exchange_codes(self) -> List[str]:
        """Obtener códigos de todos los exchanges"""
        return list(self._exchanges.keys())
    
    def is_exchange_registered(self, code: str) -> bool:
        """Verificar si un exchange está registrado"""
        return code.upper() in self._exchanges


class ExchangeDataProcessor:
    """Procesador de datos para diferentes tipos de exchanges"""
    
    @staticmethod
    async def process_bcv_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar datos del BCV"""
        if data.get("status") != "success":
            return {"status": "error", "error": data.get("error", "Error desconocido")}
        
        result = {"status": "success", "processed_data": []}
        exchange_data = data.get("data", {})
        
        # USD/VES
        if exchange_data.get("usd_ves"):
            result["processed_data"].append({
                "exchange_code": "BCV",
                "currency_pair": "USD/VES",
                "buy_price": exchange_data["usd_ves"],
                "sell_price": exchange_data["usd_ves"],
                "avg_price": exchange_data["usd_ves"],
                "source": "bcv_web_scraping"
            })
        
        # EUR/VES
        if exchange_data.get("eur_ves", 0) > 0:
            result["processed_data"].append({
                "exchange_code": "BCV",
                "currency_pair": "EUR/VES",
                "buy_price": exchange_data["eur_ves"],
                "sell_price": exchange_data["eur_ves"],
                "avg_price": exchange_data["eur_ves"],
                "source": "bcv_web_scraping"
            })
        
        return result
    
    @staticmethod
    async def process_binance_p2p_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar datos de Binance P2P"""
        if data.get("status") != "success":
            return {"status": "error", "error": data.get("error", "Error desconocido")}
        
        result = {"status": "success", "processed_data": []}
        exchange_data = data.get("data", {})
        
        if exchange_data.get("buy_usdt") and exchange_data.get("sell_usdt"):
            buy_price = exchange_data["buy_usdt"]["price"]
            sell_price = exchange_data["sell_usdt"]["price"]
            
            result["processed_data"].append({
                "exchange_code": "BINANCE_P2P",
                "currency_pair": "USDT/VES",
                "buy_price": buy_price,
                "sell_price": sell_price,
                "avg_price": (buy_price + sell_price) / 2,
                "volume_24h": exchange_data.get("market_analysis", {}).get("volume_24h", 0),
                "source": "binance_p2p_api"
            })
        
        return result
    
    @staticmethod
    async def process_italcambios_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesar datos de Italcambios"""
        if data.get("status") != "success":
            return {"status": "error", "error": data.get("error", "Error desconocido")}
        
        result = {"status": "success", "processed_data": []}
        exchange_data = data.get("data", {})
        
        if exchange_data.get("usd_ves_compra") and exchange_data.get("usd_ves_venta"):
            compra_price = exchange_data["usd_ves_compra"]
            venta_price = exchange_data["usd_ves_venta"]
            
            result["processed_data"].append({
                "exchange_code": "ITALCAMBIOS",
                "currency_pair": "USD/VES",
                "buy_price": compra_price,
                "sell_price": venta_price,
                "avg_price": exchange_data.get("usd_ves_promedio", (compra_price + venta_price) / 2),
                "source": "italcambios_web_scraping"
            })
        
        return result


class ExchangeFetcher:
    """Fetcher centralizado para todos los exchanges"""
    
    def __init__(self):
        self.registry = ExchangeRegistry()
        self.processor = ExchangeDataProcessor()
        self._fetcher_functions = self._setup_fetcher_functions()
        self._processor_functions = self._setup_processor_functions()
    
    def _setup_fetcher_functions(self) -> Dict[str, Callable]:
        """Configurar funciones de fetching para cada exchange"""
        return {
            "BCV": self._fetch_bcv_data,
            "BINANCE_P2P": self._fetch_binance_p2p_data,
            "ITALCAMBIOS": self._fetch_italcambios_data
        }
    
    def _setup_processor_functions(self) -> Dict[str, Callable]:
        """Configurar funciones de procesamiento para cada exchange"""
        return {
            "BCV": self.processor.process_bcv_data,
            "BINANCE_P2P": self.processor.process_binance_p2p_data,
            "ITALCAMBIOS": self.processor.process_italcambios_data
        }
    
    async def _fetch_bcv_data(self) -> Dict[str, Any]:
        """Fetch datos del BCV"""
        from app.services.data_fetcher import scrape_bcv_rates
        return await scrape_bcv_rates()
    
    async def _fetch_binance_p2p_data(self) -> Dict[str, Any]:
        """Fetch datos de Binance P2P"""
        from app.services.data_fetcher import fetch_binance_p2p_complete
        return await fetch_binance_p2p_complete()
    
    async def _fetch_italcambios_data(self) -> Dict[str, Any]:
        """Fetch datos de Italcambios"""
        from app.services.data_fetcher import scrape_italcambios_rates
        return await scrape_italcambios_rates()
    
    async def fetch_exchange_data(self, exchange_code: str) -> Dict[str, Any]:
        """Fetch datos de un exchange específico"""
        exchange = self.registry.get_exchange(exchange_code)
        if not exchange:
            return {"status": "error", "error": f"Exchange {exchange_code} no registrado"}
        
        if not exchange.is_active:
            return {"status": "skipped", "reason": "Exchange inactivo"}
        
        fetcher_func = self._fetcher_functions.get(exchange_code.upper())
        if not fetcher_func:
            return {"status": "error", "error": f"No hay fetcher configurado para {exchange_code}"}
        
        try:
            print(f"{exchange.icon} Obteniendo datos de {exchange.name}...")
            raw_data = await fetcher_func()
            
            # Procesar datos
            processor_func = self._processor_functions.get(exchange_code.upper())
            if processor_func:
                processed_data = await processor_func(raw_data)
                return processed_data
            else:
                return raw_data
                
        except Exception as e:
            print(f"❌ Error obteniendo datos de {exchange.name}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def fetch_all_exchanges(self, specific_exchange: Optional[str] = None) -> Dict[str, Any]:
        """Fetch datos de todos los exchanges o uno específico"""
        if specific_exchange:
            exchanges_to_fetch = [specific_exchange.upper()]
        else:
            exchanges_to_fetch = self.registry.get_exchange_codes()
        
        results = {}
        
        # Ejecutar en paralelo para mejor rendimiento
        tasks = []
        for exchange_code in exchanges_to_fetch:
            task = self.fetch_exchange_data(exchange_code)
            tasks.append((exchange_code, task))
        
        # Ejecutar todas las tareas en paralelo
        for exchange_code, task in tasks:
            try:
                result = await task
                results[exchange_code.lower()] = result
            except Exception as e:
                results[exchange_code.lower()] = {"status": "error", "error": str(e)}
        
        return results
    
    async def save_exchange_data(self, exchange_code: str, processed_data: Dict[str, Any]) -> bool:
        """Guardar datos procesados de un exchange en la base de datos"""
        if processed_data.get("status") != "success":
            return False
        
        try:
            for rate_data in processed_data.get("processed_data", []):
                await optimized_db.upsert_current_rate_fast(
                    rate_data["exchange_code"],
                    rate_data["currency_pair"],
                    rate_data["buy_price"],
                    rate_data["sell_price"],
                    volume_24h=rate_data.get("volume_24h", 0),
                    source=rate_data.get("source", "unknown")
                )
            return True
        except Exception as e:
            print(f"❌ Error guardando datos de {exchange_code}: {e}")
            return False
    
    def get_exchanges_info(self) -> List[Dict[str, Any]]:
        """Obtener información de todos los exchanges para el endpoint /exchanges"""
        return [
            {
                "name": ex.name,
                "code": ex.code,
                "type": ex.type.value,
                "description": ex.description,
                "is_active": ex.is_active,
                "icon": ex.icon
            }
            for ex in self.registry.get_all_exchanges()
        ]


# Instancia global del fetcher
exchange_fetcher = ExchangeFetcher()
