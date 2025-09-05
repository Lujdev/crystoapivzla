"""
Ejemplos de cómo agregar nuevos exchanges al sistema
Este archivo muestra cómo el sistema es completamente escalable
"""

from app.services.exchange_registry import ExchangeConfig, ExchangeType, exchange_fetcher


def add_new_exchange_example():
    """
    EJEMPLO: Cómo agregar un nuevo exchange sin modificar código existente
    
    Para agregar un nuevo exchange, solo necesitas:
    1. Crear la función de fetching
    2. Crear la función de procesamiento
    3. Registrar el exchange
    4. ¡Listo! El sistema lo manejará automáticamente
    """
    
    # Ejemplo: Agregar AirTM
    async def fetch_airtm_data():
        """Función para obtener datos de AirTM"""
        # Aquí iría la lógica para obtener datos de AirTM
        # Por ejemplo, usando requests o aiohttp
        return {
            "status": "success",
            "data": {
                "usd_ves_compra": 36.50,
                "usd_ves_venta": 37.20,
                "usd_ves_promedio": 36.85
            }
        }
    
    async def process_airtm_data(data):
        """Función para procesar datos de AirTM"""
        if data.get("status") != "success":
            return {"status": "error", "error": data.get("error", "Error desconocido")}
        
        result = {"status": "success", "processed_data": []}
        exchange_data = data.get("data", {})
        
        if exchange_data.get("usd_ves_compra") and exchange_data.get("usd_ves_venta"):
            compra_price = exchange_data["usd_ves_compra"]
            venta_price = exchange_data["usd_ves_venta"]
            
            result["processed_data"].append({
                "exchange_code": "AIRTM",
                "currency_pair": "USD/VES",
                "buy_price": compra_price,
                "sell_price": venta_price,
                "avg_price": exchange_data.get("usd_ves_promedio", (compra_price + venta_price) / 2),
                "source": "airtm_api"
            })
        
        return result
    
    # Registrar el nuevo exchange
    airtm_config = ExchangeConfig(
        code="AIRTM",
        name="AirTM",
        type=ExchangeType.FIAT,
        description="Plataforma de intercambio AirTM",
        icon="✈️",
        update_frequency_minutes=15
    )
    
    # Agregar al registry
    exchange_fetcher.registry.register_exchange(airtm_config)
    
    # Agregar las funciones de fetching y procesamiento
    exchange_fetcher._fetcher_functions["AIRTM"] = fetch_airtm_data
    exchange_fetcher._processor_functions["AIRTM"] = process_airtm_data
    
    print("✅ AirTM agregado exitosamente al sistema!")


def add_crypto_exchange_example():
    """
    EJEMPLO: Cómo agregar un exchange de criptomonedas
    """
    
    # Ejemplo: Agregar LocalBitcoins
    async def fetch_localbitcoins_data():
        """Función para obtener datos de LocalBitcoins"""
        return {
            "status": "success",
            "data": {
                "btc_ves_compra": 2500000,
                "btc_ves_venta": 2550000,
                "btc_ves_promedio": 2525000
            }
        }
    
    async def process_localbitcoins_data(data):
        """Función para procesar datos de LocalBitcoins"""
        if data.get("status") != "success":
            return {"status": "error", "error": data.get("error", "Error desconocido")}
        
        result = {"status": "success", "processed_data": []}
        exchange_data = data.get("data", {})
        
        if exchange_data.get("btc_ves_compra") and exchange_data.get("btc_ves_venta"):
            compra_price = exchange_data["btc_ves_compra"]
            venta_price = exchange_data["btc_ves_venta"]
            
            result["processed_data"].append({
                "exchange_code": "LOCALBITCOINS",
                "currency_pair": "BTC/VES",
                "buy_price": compra_price,
                "sell_price": venta_price,
                "avg_price": exchange_data.get("btc_ves_promedio", (compra_price + venta_price) / 2),
                "source": "localbitcoins_api"
            })
        
        return result
    
    # Registrar el nuevo exchange
    localbitcoins_config = ExchangeConfig(
        code="LOCALBITCOINS",
        name="LocalBitcoins",
        type=ExchangeType.CRYPTO,
        description="Plataforma P2P de Bitcoin",
        icon="₿",
        update_frequency_minutes=10
    )
    
    # Agregar al registry
    exchange_fetcher.registry.register_exchange(localbitcoins_config)
    
    # Agregar las funciones de fetching y procesamiento
    exchange_fetcher._fetcher_functions["LOCALBITCOINS"] = fetch_localbitcoins_data
    exchange_fetcher._processor_functions["LOCALBITCOINS"] = process_localbitcoins_data
    
    print("✅ LocalBitcoins agregado exitosamente al sistema!")


def demonstrate_scalability():
    """
    Demostrar la escalabilidad del sistema
    """
    print("🚀 DEMOSTRACIÓN DE ESCALABILIDAD")
    print("=" * 50)
    
    # Mostrar exchanges actuales
    current_exchanges = exchange_fetcher.registry.get_all_exchanges()
    print(f"📊 Exchanges actuales: {len(current_exchanges)}")
    for ex in current_exchanges:
        print(f"  - {ex.icon} {ex.name} ({ex.code}) - {ex.type.value}")
    
    print("\n✅ Para agregar un nuevo exchange:")
    print("1. Crear función de fetching")
    print("2. Crear función de procesamiento") 
    print("3. Registrar con ExchangeConfig")
    print("4. ¡El sistema lo maneja automáticamente!")
    
    print("\n🎯 Beneficios del sistema escalable:")
    print("✅ No modificar código existente")
    print("✅ Agregar exchanges dinámicamente")
    print("✅ Procesamiento en paralelo")
    print("✅ Manejo de errores centralizado")
    print("✅ Configuración flexible por exchange")
    print("✅ Fácil mantenimiento")


if __name__ == "__main__":
    demonstrate_scalability()
