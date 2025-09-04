"""
Servicio para obtener datos de APIs externas
BCV, Binance P2P, y otras fuentes de cotizaciones
"""

import asyncio
import aiohttp
from loguru import logger
from typing import Dict, List, Optional
from datetime import datetime
import re
from bs4 import BeautifulSoup
from pprint import pprint

from app.core.config import settings
from app.core.database import get_db_session, execute_raw_sql
from app.core.database_optimized import optimized_db


async def update_all_rates() -> Dict[str, any]:
    """
    Actualizar todas las cotizaciones de todas las fuentes
    """
    results = {
        "bcv": {"status": "pending", "data": None, "error": None},
        "binance_p2p": {"status": "pending", "data": None, "error": None},
        "italcambios": {"status": "pending", "data": None, "error": None},
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        logger.info("🔄 Actualizando todas las cotizaciones...")
        
        # Actualizar BCV
        try:
            bcv_result = await update_bcv_rates()
            results["bcv"] = bcv_result
        except Exception as e:
            results["bcv"] = {"status": "error", "error": str(e)}
        
        # Actualizar Binance P2P
        try:
            binance_result = await update_binance_p2p_rates()
            results["binance_p2p"] = binance_result
        except Exception as e:
            results["binance_p2p"] = {"status": "error", "error": str(e)}
        
        # Actualizar Italcambios
        try:
            italcambios_result = await update_italcambios_rates()
            results["italcambios"] = italcambios_result
        except Exception as e:
            results["italcambios"] = {"status": "error", "error": str(e)}
        
        logger.info("✅ Todas las cotizaciones actualizadas")
        return results
        
    except Exception as e:
        logger.error(f"❌ Error actualizando cotizaciones: {e}")
        for source in results:
            if isinstance(results[source], dict):
                results[source]["status"] = "error"
                results[source]["error"] = str(e)
        
        return results


async def scrape_bcv_rates() -> Dict[str, any]:
    """
    Hacer web scraping de la página del BCV para obtener cotizaciones
    """
    try:
        logger.info("🏦 Iniciando scraping del BCV...")
        
        # URLs del BCV (probar tanto HTTP como HTTPS)
        urls = [
            "http://www.bcv.org.ve/",
            "https://www.bcv.org.ve/"
        ]
        
        # Headers para simular un navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        html_content = None
        used_url = None
        
        # Probar diferentes URLs y configuraciones SSL
        for url in urls:
            try:
                logger.info(f"🔗 Intentando conectar a: {url}")
                
                # Configuración del cliente HTTP
                connector = aiohttp.TCPConnector(ssl=False)  # Deshabilitar verificación SSL
                
                async with aiohttp.ClientSession(
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=connector
                ) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            used_url = url
                            logger.info(f"✅ Conexión exitosa a: {url}")
                            break
                        else:
                            logger.warning(f"⚠️ HTTP {response.status} para {url}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Error conectando a {url}: {e}")
                continue
        
        if not html_content:
            raise Exception("No se pudo conectar a ninguna URL del BCV")
        
        # Parsear el HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Buscar los divs con IDs específicos
        dolar_div = soup.find('div', id='dolar')
        euro_div = soup.find('div', id='euro')
        
        if not dolar_div or not euro_div:
            # Si no encuentra los IDs específicos, buscar por texto o estructura alternativa
            logger.warning("⚠️ No se encontraron los divs con IDs 'dolar' y 'euro', buscando alternativas...")
            
            # Buscar por texto que contenga "USD" o "Dólar"
            dolar_div = soup.find(string=re.compile(r'USD|Dólar|DOLAR', re.IGNORECASE))
            if dolar_div:
                dolar_div = dolar_div.find_parent()
            
            # Buscar por texto que contenga "EUR" o "Euro"
            euro_div = soup.find(string=re.compile(r'EUR|Euro', re.IGNORECASE))
            if euro_div:
                euro_div = euro_div.find_parent()
        
        # Extraer los valores
        usd_rate = None
        eur_rate = None
        
        if dolar_div:
            # Buscar el valor numérico en el div del dólar
            dolar_text = dolar_div.get_text()
            usd_match = re.search(r'(\d+[.,]\d+)', dolar_text.replace(',', '.'))
            if usd_match:
                usd_rate = float(usd_match.group(1).replace(',', '.'))
                logger.info(f"💵 Dólar encontrado: {usd_rate}")
            else:
                logger.warning("⚠️ No se pudo extraer el valor del dólar")
        
        if euro_div:
            # Buscar el valor numérico en el div del euro
            euro_text = euro_div.get_text()
            eur_match = re.search(r'(\d+[.,]\d+)', euro_text.replace(',', '.'))
            if eur_match:
                eur_rate = float(eur_match.group(1).replace(',', '.'))
                logger.info(f"💶 Euro encontrado: {eur_rate}")
            else:
                logger.warning("⚠️ No se pudo extraer el valor del euro")
        
        # Si no se encontraron los valores, intentar buscar en toda la página
        if not usd_rate or not eur_rate:
            logger.info("🔍 Buscando valores en toda la página...")
            
            # Buscar patrones de cotización en toda la página
            page_text = soup.get_text()
            
            # Patrón para USD
            if not usd_rate:
                usd_patterns = [
                    r'USD[:\s]*(\d+[.,]\d+)',
                    r'Dólar[:\s]*(\d+[.,]\d+)',
                    r'DOLAR[:\s]*(\d+[.,]\d+)',
                    r'(\d+[.,]\d+)[\s]*USD',
                    r'(\d+[.,]\d+)[\s]*Dólar'
                ]
                
                for pattern in usd_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        usd_rate = float(match.group(1).replace(',', '.'))
                        logger.info(f"💵 Dólar encontrado con patrón alternativo: {usd_rate}")
                        break
            
            # Patrón para EUR
            if not eur_rate:
                eur_patterns = [
                    r'EUR[:\s]*(\d+[.,]\d+)',
                    r'Euro[:\s]*(\d+[.,]\d+)',
                    r'(\d+[.,]\d+)[\s]*EUR',
                    r'(\d+[.,]\d+)[\s]*Euro'
                ]
                
                for pattern in eur_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        eur_rate = float(match.group(1).replace(',', '.'))
                        logger.info(f"💶 Euro encontrado con patrón alternativo: {eur_rate}")
                        break
        
        # Validar que se obtuvieron los valores
        if not usd_rate or not eur_rate:
            raise Exception(f"No se pudieron extraer las cotizaciones. USD: {usd_rate}, EUR: {eur_rate}")
        
        # Crear el resultado
        result = {
            "usd_ves": usd_rate,
            "eur_ves": eur_rate,
            "timestamp": datetime.now().isoformat(),
            "source": "bcv",
            "scraping_method": "web_scraping",
            "url": used_url
        }
        
        logger.info(f"✅ BCV scraping exitoso: USD/VES = {usd_rate}, EUR/VES = {eur_rate}")
        
        # Guardar en base de datos
        try:
            await optimized_db.upsert_current_rate_fast(data=result)
            logger.info("💾 BCV rates guardados en base de datos")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron guardar BCV rates en BD: {e}")
        
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error en scraping del BCV: {e}")
        return {"status": "error", "error": str(e)}


async def scrape_bcv_rates_no_save() -> Dict[str, any]:
    """
    Hacer web scraping de la página del BCV para obtener cotizaciones
    VERSIÓN SIN GUARDAR EN BD (para uso en comparaciones)
    """
    try:
        logger.info("🏦 Iniciando scraping del BCV (sin guardar en BD)...")
        
        # URLs del BCV (probar tanto HTTP como HTTPS)
        urls = [
            "http://www.bcv.org.ve/",
            "https://www.bcv.org.ve/"
        ]
        
        # Headers para simular un navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        html_content = None
        used_url = None
        
        # Probar diferentes URLs y configuraciones SSL
        for url in urls:
            try:
                logger.info(f"🔗 Intentando conectar a: {url}")
                
                # Configuración del cliente HTTP
                connector = aiohttp.TCPConnector(ssl=False)  # Deshabilitar verificación SSL
                
                async with aiohttp.ClientSession(
                    headers=headers, 
                    timeout=aiohttp.ClientTimeout(total=30),
                    connector=connector
                ) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            html_content = await response.text()
                            used_url = url
                            logger.info(f"✅ Conexión exitosa a: {url}")
                            break
                        else:
                            logger.warning(f"⚠️ HTTP {response.status} para {url}")
                            
            except Exception as e:
                logger.warning(f"⚠️ Error conectando a {url}: {e}")
                continue
        
        if not html_content:
            raise Exception("No se pudo conectar a ninguna URL del BCV")
        
        # Parsear el HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Buscar los divs con IDs específicos
        dolar_div = soup.find('div', id='dolar')
        euro_div = soup.find('div', id='euro')
        
        if not dolar_div or not euro_div:
            # Si no encuentra los IDs específicos, buscar por texto o estructura alternativa
            logger.warning("⚠️ No se encontraron los divs con IDs 'dolar' y 'euro', buscando alternativas...")
            
            # Buscar por texto que contenga "USD" o "Dólar"
            dolar_div = soup.find(string=re.compile(r'USD|Dólar|DOLAR', re.IGNORECASE))
            if dolar_div:
                dolar_div = dolar_div.find_parent()
            
            # Buscar por texto que contenga "EUR" o "Euro"
            euro_div = soup.find(string=re.compile(r'EUR|Euro', re.IGNORECASE))
            if euro_div:
                euro_div = euro_div.find_parent()
        
        # Extraer los valores
        usd_rate = None
        eur_rate = None
        
        if dolar_div:
            # Buscar el valor numérico en el div del dólar
            dolar_text = dolar_div.get_text()
            usd_match = re.search(r'(\d+[.,]\d+)', dolar_text.replace(',', '.'))
            if usd_match:
                usd_rate = float(usd_match.group(1).replace(',', '.'))
                logger.info(f"💵 Dólar encontrado: {usd_rate}")
            else:
                logger.warning("⚠️ No se pudo extraer el valor del dólar")
        
        if euro_div:
            # Buscar el valor numérico en el div del euro
            euro_text = euro_div.get_text()
            eur_match = re.search(r'(\d+[.,]\d+)', euro_text.replace(',', '.'))
            if eur_match:
                eur_rate = float(eur_match.group(1).replace(',', '.'))
                logger.info(f"💶 Euro encontrado: {eur_rate}")
            else:
                logger.warning("⚠️ No se pudo extraer el valor del euro")
        
        # Si no se encontraron los valores, intentar buscar en toda la página
        if not usd_rate or not eur_rate:
            logger.info("🔍 Buscando valores en toda la página...")
            
            # Buscar patrones de cotización en toda la página
            page_text = soup.get_text()
            
            # Patrón para USD
            if not usd_rate:
                usd_patterns = [
                    r'USD[:\s]*(\d+[.,]\d+)',
                    r'Dólar[:\s]*(\d+[.,]\d+)',
                    r'DOLAR[:\s]*(\d+[.,]\d+)',
                    r'(\d+[.,]\d+)[\s]*USD',
                    r'(\d+[.,]\d+)[\s]*Dólar'
                ]
                
                for pattern in usd_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        usd_rate = float(match.group(1).replace(',', '.'))
                        logger.info(f"💵 Dólar encontrado con patrón alternativo: {usd_rate}")
                        break
            
            # Patrón para EUR
            if not eur_rate:
                eur_patterns = [
                    r'EUR[:\s]*(\d+[.,]\d+)',
                    r'Euro[:\s]*(\d+[.,]\d+)',
                    r'(\d+[.,]\d+)[\s]*EUR',
                    r'(\d+[.,]\d+)[\s]*Euro'
                ]
                
                for pattern in eur_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        eur_rate = float(match.group(1).replace(',', '.'))
                        logger.info(f"💶 Euro encontrado con patrón alternativo: {eur_rate}")
                        break
        
        # Validar que se obtuvieron los valores
        if not usd_rate or not eur_rate:
            raise Exception(f"No se pudieron extraer las cotizaciones. USD: {usd_rate}, EUR: {eur_rate}")
        
        # Crear el resultado
        result = {
            "usd_ves": usd_rate,
            "eur_ves": eur_rate,
            "timestamp": datetime.now().isoformat(),
            "source": "bcv",
            "scraping_method": "web_scraping",
            "url": used_url
        }
        
        logger.info(f"✅ BCV scraping exitoso (sin guardar): USD/VES = {usd_rate}, EUR/VES = {eur_rate}")
        
        # IMPORTANTE: NO guardar en base de datos (para evitar duplicados en comparaciones)
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error en scraping del BCV (sin guardar): {e}")
        return {"status": "error", "error": str(e)}


async def update_bcv_rates() -> Dict[str, any]:
    """
    Actualizar cotizaciones del Banco Central de Venezuela
    """
    try:
        logger.info("🏦 Obteniendo cotizaciones del BCV...")
        
        # Usar la función de scraping real
        result = await scrape_bcv_rates()
        
        if result["status"] == "success":
            logger.info(f"✅ BCV obtenido: USD/VES = {result['data']['usd_ves']}, EUR/VES = {result['data']['eur_ves']}")
        else:
            logger.error(f"❌ Error obteniendo datos del BCV: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos del BCV: {e}")
        return {"status": "error", "error": str(e)}


async def _fetch_binance_p2p_sell_rates_no_save() -> Dict[str, any]:
    """
    Consultar la API de Binance P2P para obtener precios de venta de USDT por VES
    (Cuando quieres vender USDT y recibir bolívares)
    VERSIÓN SIN GUARDAR EN BD (para uso interno del endpoint complete)
    """
    try:
        logger.info("🟡 Consultando API de Binance P2P para venta de USDT (sin guardar en BD)...")
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Headers para la petición
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Payload para la consulta tus Bolivares por USDT
        payload = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "BUY",  # Para obtener el precio de USDT por tus Bolivares
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["PagoMovil"],
            "classifies": ["mass", "profession", "fiat_trade"],
            "tradedWith": False,
            "followed": False
        }
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error HTTP {response.status}: {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {response.reason}")
                
                binance_data = await response.json()
                
        # Log de debug para ver la estructura de la respuesta
        logger.info(f"🔍 Respuesta de Binance (Compra USDT) recibida: {len(binance_data.get('data', []))} anuncios")
        
        # Validar la respuesta de Binance
        if binance_data.get("code") == "000000" and binance_data.get("data") and len(binance_data["data"]) > 0:
            # Encontrar el precio más alto (mejor precio para vender USDT)
            highest_price = 0
            best_ad = None
            
            for i, item in enumerate(binance_data["data"]):
                try:
                    price = float(item["adv"]["price"])
                    logger.info(f"📊 Anuncio Compra {i+1}: Precio = {price} VES")
                    if price > highest_price:
                        highest_price = price
                        best_ad = item
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error procesando anuncio de venta {i+1}: {e}")
                    continue
            
            if highest_price > 0 and best_ad:
                # Calcular precio promedio y estadísticas
                prices = []
                volumes = []
                
                for item in binance_data["data"][:10]:  # Top 10 anuncios
                    try:
                        price = float(item["adv"]["price"])
                        volume = float(item["adv"]["surplusAmount"])
                        prices.append(price)
                        volumes.append(volume)
                    except (ValueError, KeyError):
                        continue
                
                # Calcular estadísticas
                avg_price = sum(prices) / len(prices) if prices else highest_price
                total_volume = sum(volumes) if volumes else 0
                
                # Extraer información del mejor anuncio de forma segura
                best_ad_info = {
                    "price": highest_price,
                    "min_amount": float(best_ad["adv"].get("minSingleTransAmount", 0)),
                    "max_amount": float(best_ad["adv"].get("maxSingleTransAmount", 0)),
                    "merchant": best_ad["advertiser"].get("nickName", "N/A"),
                    "pay_types": best_ad["adv"].get("payTypes", []),
                    "user_type": best_ad["advertiser"].get("userType", "N/A")
                }
                
                result = {
                    "usdt_ves_sell": highest_price,  # Mejor precio para comprar USDT
                    "usdt_ves_avg": round(avg_price, 4),
                    "volume_24h": round(total_volume, 2),
                    "best_ad": best_ad_info,
                    "total_ads": len(binance_data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "buy_usdt"  # Indicar que es para comprar USDT
                }
                
                logger.info(f"✅ Binance P2P COMPRA obtenido (sin guardar): USDT/VES = {highest_price} (mejor precio para comprar)")
                
                # IMPORTANTE: NO guardar en base de datos (para evitar duplicados)
                return {"status": "success", "data": result}
            else:
                raise Exception("No se encontraron precios válidos en la respuesta de Binance para venta")
        else:
            error_msg = binance_data.get("message", "Respuesta inválida de Binance")
            logger.error(f"❌ Error en respuesta de Binance (COMPRA): {error_msg}")
            logger.error(f"🔍 Código de respuesta: {binance_data.get('code')}")
            logger.error(f"🔍 Datos recibidos: {len(binance_data.get('data', []))}")
            raise Exception(f"Datos de Binance inválidos para compra: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ Error consultando Binance P2P para compra: {e}")
        return {"status": "error", "error": str(e)}


async def fetch_binance_p2p_sell_rates() -> Dict[str, any]:
    """
    Consultar la API de Binance P2P para obtener precios de venta de USDT por VES
    (Cuando quieres vender USDT y recibir bolívares)
    """
    try:
        logger.info("🟡 Consultando API de Binance P2P para venta de USDT...")
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Headers para la petición
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Payload para la consulta tus Bolivares por USDT
        payload = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "BUY",  # Para obtener el precio de USDT por tus Bolivares
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["PagoMovil"],
            "classifies": ["mass", "profession", "fiat_trade"],
            "tradedWith": False,
            "followed": False
        }
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error HTTP {response.status}: {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {response.reason}")
                
                binance_data = await response.json()
                
        # Log de debug para ver la estructura de la respuesta
        logger.info(f"🔍 Respuesta de Binance (Compra USDT) recibida: {len(binance_data.get('data', []))} anuncios")
        
        # Validar la respuesta de Binance
        if binance_data.get("code") == "000000" and binance_data.get("data") and len(binance_data["data"]) > 0:
            # Encontrar el precio más alto (mejor precio para vender USDT)
            highest_price = 0
            best_ad = None
            
            for i, item in enumerate(binance_data["data"]):
                try:
                    price = float(item["adv"]["price"])
                    logger.info(f"📊 Anuncio Compra {i+1}: Precio = {price} VES")
                    if price > highest_price:
                        highest_price = price
                        best_ad = item
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error procesando anuncio de venta {i+1}: {e}")
                    continue
            
            if highest_price > 0 and best_ad:
                # Calcular precio promedio y estadísticas
                prices = []
                volumes = []
                
                for item in binance_data["data"][:10]:  # Top 10 anuncios
                    try:
                        price = float(item["adv"]["price"])
                        volume = float(item["adv"]["surplusAmount"])
                        prices.append(price)
                        volumes.append(volume)
                    except (ValueError, KeyError):
                        continue
                
                # Calcular estadísticas
                avg_price = sum(prices) / len(prices) if prices else highest_price
                total_volume = sum(volumes) if volumes else 0
                
                # Extraer información del mejor anuncio de forma segura
                best_ad_info = {
                    "price": highest_price,
                    "min_amount": float(best_ad["adv"].get("minSingleTransAmount", 0)),
                    "max_amount": float(best_ad["adv"].get("maxSingleTransAmount", 0)),
                    "merchant": best_ad["advertiser"].get("nickName", "N/A"),
                    "pay_types": best_ad["adv"].get("payTypes", []),
                    "user_type": best_ad["advertiser"].get("userType", "N/A")
                }
                
                result = {
                    "usdt_ves_sell": highest_price,  # Mejor precio para comprar USDT
                    "usdt_ves_avg": round(avg_price, 4),
                    "volume_24h": round(total_volume, 2),
                    "best_ad": best_ad_info,
                    "total_ads": len(binance_data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "buy_usdt"  # Indicar que es para comprar USDT
                }
                
                logger.info(f"✅ Binance P2P COMPRA obtenido: USDT/VES = {highest_price} (mejor precio para comprar)")
                
                # Guardar en base de datos
                try:
                    await optimized_db.upsert_current_rate_fast(data=result)
                    logger.info("💾 Binance P2P sell rates guardados en base de datos")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudieron guardar Binance P2P sell rates en BD: {e}")
                
                return {"status": "success", "data": result}
            else:
                raise Exception("No se encontraron precios válidos en la respuesta de Binance para venta")
        else:
            error_msg = binance_data.get("message", "Respuesta inválida de Binance")
            logger.error(f"❌ Error en respuesta de Binance (COMPRA): {error_msg}")
            logger.error(f"🔍 Código de respuesta: {binance_data.get('code')}")
            logger.error(f"🔍 Datos recibidos: {len(binance_data.get('data', []))}")
            raise Exception(f"Datos de Binance inválidos para compra: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ Error consultando Binance P2P para compra: {e}")
        return {"status": "error", "error": str(e)}


async def _fetch_binance_p2p_rates_no_save() -> Dict[str, any]:
    """
    Consultar la API de Binance P2P para obtener precios de venta de USDT con VES
    VERSIÓN SIN GUARDAR EN BD (para uso interno del endpoint complete)
    """
    try:
        logger.info("🟡 Consultando API de Binance P2P (sin guardar en BD)...")
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Headers para la petición
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Payload para la consulta (Vendes USDT por Bolivares)
        payload = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "SELL",  # Obtienes el precio en Bs por tus USDT
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["PagoMovil"],
            "classifies": ["mass", "profession", "fiat_trade"],
            "tradedWith": False,
            "followed": False
        }
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error HTTP {response.status}: {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {response.reason}")
                
                binance_data = await response.json()
                
        # Log de debug para ver la estructura de la respuesta
        logger.info(f"🔍 Respuesta de Binance recibida: {len(binance_data.get('data', []))} anuncios")
        
        # Validar la respuesta de Binance
        if binance_data.get("code") == "000000" and binance_data.get("data") and len(binance_data["data"]) > 0:
            # Encontrar el precio más bajo (mejor precio para vender USDT)
            lowest_price = float('inf')
            best_ad = None
            
            for i, item in enumerate(binance_data["data"]):
                try:
                    price = float(item["adv"]["price"])
                    logger.info(f"📊 Anuncio {i+1}: Precio = {price} VES")
                    if price < lowest_price:
                        lowest_price = price
                        best_ad = item
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error procesando anuncio {i+1}: {e}")
                    continue
            
            if lowest_price != float('inf') and best_ad:
                # Calcular precio promedio y estadísticas
                prices = []
                volumes = []
                
                for item in binance_data["data"][:10]:  # Top 10 anuncios
                    try:
                        price = float(item["adv"]["price"])
                        volume = float(item["adv"]["surplusAmount"])
                        prices.append(price)
                        volumes.append(volume)
                    except (ValueError, KeyError):
                        continue
                
                # Calcular estadísticas
                avg_price = sum(prices) / len(prices) if prices else lowest_price
                total_volume = sum(volumes) if volumes else 0
                
                # Extraer información del mejor anuncio de forma segura
                best_ad_info = {
                    "price": lowest_price,
                    "min_amount": float(best_ad["adv"].get("minSingleTransAmount", 0)),
                    "max_amount": float(best_ad["adv"].get("maxSingleTransAmount", 0)),
                    "merchant": best_ad["advertiser"].get("nickName", "N/A"),
                    "pay_types": best_ad["adv"].get("payTypes", []),
                    "user_type": best_ad["advertiser"].get("userType", "N/A")
                }
                
                result = {
                    "usdt_ves_buy": lowest_price,  # Mejor precio para vender USDT
                    "usdt_ves_avg": round(avg_price, 4),
                    "volume_24h": round(total_volume, 2),
                    "best_ad": best_ad_info,
                    "total_ads": len(binance_data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "sell_usdt"  # Indicar que es para vender USDT
                }
                
                logger.info(f"✅ Binance P2P obtenido (sin guardar): USDT/VES = {lowest_price} (mejor precio)")
                
                # IMPORTANTE: NO guardar en base de datos (para evitar duplicados)
                return {"status": "success", "data": result}
            else:
                raise Exception("No se encontraron precios válidos en la respuesta de Binance")
        else:
            error_msg = binance_data.get("message", "Respuesta inválida de Binance")
            logger.error(f"❌ Error en respuesta de Binance: {error_msg}")
            logger.error(f"🔍 Código de respuesta: {binance_data.get('code')}")
            logger.error(f"🔍 Datos recibidos: {len(binance_data.get('data', []))}")
            raise Exception(f"Datos de Binance inválidos: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ Error consultando Binance P2P: {e}")
        return {"status": "error", "error": str(e)}


async def fetch_binance_p2p_rates() -> Dict[str, any]:
    """
    Consultar la API de Binance P2P para obtener precios de venta de USDT con VES
    """
    try:
        logger.info("🟡 Consultando API de Binance P2P...")
        
        # URL de la API de Binance P2P
        url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
        
        # Headers para la petición
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Payload para la consulta (Vendes USDT por Bolivares)
        payload = {
            "fiat": "VES",
            "page": 1,
            "rows": 10,
            "transAmount": 500,
            "tradeType": "SELL",  # Obtienes el precio en Bs por tus USDT
            "asset": "USDT",
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "all",
            "periods": [],
            "additionalKycVerifyFilter": 0,
            "publisherType": "merchant",
            "payTypes": ["PagoMovil"],
            "classifies": ["mass", "profession", "fiat_trade"],
            "tradedWith": False,
            "followed": False
        }
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error HTTP {response.status}: {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {response.reason}")
                
                binance_data = await response.json()
                
        # Log de debug para ver la estructura de la respuesta
        logger.info(f"🔍 Respuesta de Binance recibida: {len(binance_data.get('data', []))} anuncios")
        
        # Validar la respuesta de Binance
        if binance_data.get("code") == "000000" and binance_data.get("data") and len(binance_data["data"]) > 0:
            # Encontrar el precio más bajo (mejor precio para vender USDT)
            lowest_price = float('inf')
            best_ad = None
            
            for i, item in enumerate(binance_data["data"]):
                try:
                    price = float(item["adv"]["price"])
                    logger.info(f"📊 Anuncio {i+1}: Precio = {price} VES")
                    if price < lowest_price:
                        lowest_price = price
                        best_ad = item
                except (ValueError, KeyError) as e:
                    logger.warning(f"⚠️ Error procesando anuncio {i+1}: {e}")
                    continue
            
            if lowest_price != float('inf') and best_ad:
                # Calcular precio promedio y estadísticas
                prices = []
                volumes = []
                
                for item in binance_data["data"][:10]:  # Top 10 anuncios
                    try:
                        price = float(item["adv"]["price"])
                        volume = float(item["adv"]["surplusAmount"])
                        prices.append(price)
                        volumes.append(volume)
                    except (ValueError, KeyError):
                        continue
                
                # Calcular estadísticas
                avg_price = sum(prices) / len(prices) if prices else lowest_price
                total_volume = sum(volumes) if volumes else 0
                
                # Extraer información del mejor anuncio de forma segura
                best_ad_info = {
                    "price": lowest_price,
                    "min_amount": float(best_ad["adv"].get("minSingleTransAmount", 0)),
                    "max_amount": float(best_ad["adv"].get("maxSingleTransAmount", 0)),
                    "merchant": best_ad["advertiser"].get("nickName", "N/A"),
                    "pay_types": best_ad["adv"].get("payTypes", []),
                    "user_type": best_ad["advertiser"].get("userType", "N/A")
                }
                
                result = {
                    "usdt_ves_buy": lowest_price,  # Mejor precio para vender USDT
                    "usdt_ves_avg": round(avg_price, 4),
                    "volume_24h": round(total_volume, 2),
                    "best_ad": best_ad_info,
                    "total_ads": len(binance_data["data"]),
                    "timestamp": datetime.now().isoformat(),
                    "source": "binance_p2p",
                    "api_method": "official_api",
                    "trade_type": "sell_usdt"  # Indicar que es para vender USDT
                }
                
                logger.info(f"✅ Binance P2P obtenido: USDT/VES = {lowest_price} (mejor precio)")
                
                # Guardar en base de datos
                try:
                    await optimized_db.upsert_current_rate_fast(data=result)
                    logger.info("💾 Binance P2P rates guardados en base de datos")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudieron guardar Binance P2P rates en BD: {e}")
                
                return {"status": "success", "data": result}
            else:
                raise Exception("No se encontraron precios válidos en la respuesta de Binance")
        else:
            error_msg = binance_data.get("message", "Respuesta inválida de Binance")
            logger.error(f"❌ Error en respuesta de Binance: {error_msg}")
            logger.error(f"🔍 Código de respuesta: {binance_data.get('code')}")
            logger.error(f"🔍 Datos recibidos: {len(binance_data.get('data', []))}")
            raise Exception(f"Datos de Binance inválidos: {error_msg}")
            
    except Exception as e:
        logger.error(f"❌ Error consultando Binance P2P: {e}")
        return {"status": "error", "error": str(e)}


async def fetch_binance_p2p_complete() -> Dict[str, any]:
    """
    Obtener tanto precios de compra como de venta de USDT/VES en Binance P2P
    """
    try:
        logger.info("🟡 Obteniendo precios completos de Binance P2P...")
        
        # Obtener precios de venta (SELL en Binance = vender USDT por VES)
        # IMPORTANTE: NO guardar en BD, solo obtener datos
        sell_result = await _fetch_binance_p2p_rates_no_save()
        
        # Obtener precios de compra (BUY en Binance = comprar USDT con VES)
        # IMPORTANTE: NO guardar en BD, solo obtener datos
        buy_result = await _fetch_binance_p2p_sell_rates_no_save()
        
        if buy_result["status"] == "success" and sell_result["status"] == "success":
            buy_data = buy_result["data"]
            sell_data = sell_result["data"]
            
            # CORREGIR: Asignar precios correctamente
            # buy_price = precio para COMPRAR USDT (más alto)
            # sell_price = precio para VENDER USDT (más bajo)
            buy_price = buy_data["usdt_ves_sell"]  # Precio más alto para comprar USDT
            sell_price = sell_data["usdt_ves_buy"]  # Precio más bajo para vender USDT
            
            # Calcular spread interno de Binance P2P
            spread_internal = buy_price - sell_price
            spread_percentage = (spread_internal / sell_price) * 100 if sell_price > 0 else 0
            
            complete_result = {
                "buy_usdt": {
                    "price": buy_price,  # Precio para COMPRAR USDT
                    "avg_price": buy_data["usdt_ves_avg"],
                    "best_ad": buy_data["best_ad"],
                    "total_ads": buy_data["total_ads"]
                },
                "sell_usdt": {
                    "price": sell_price,  # Precio para VENDER USDT
                    "avg_price": sell_data["usdt_ves_avg"],
                    "best_ad": sell_data["best_ad"],
                    "total_ads": sell_data["total_ads"]
                },
                "market_analysis": {
                    "spread_internal": round(spread_internal, 4),
                    "spread_percentage": round(spread_percentage, 2),
                    "volume_24h": round(buy_data["volume_24h"] + sell_data["volume_24h"], 2),
                    "liquidity_score": "high" if spread_percentage < 2 else "medium" if spread_percentage < 5 else "low"
                },
                "timestamp": datetime.now().isoformat(),
                "source": "binance_p2p",
                "api_method": "official_api"
            }
            
            logger.info(f"✅ Binance P2P completo obtenido: Buy={buy_price} (comprar USDT), Sell={sell_price} (vender USDT)")
            
            # IMPORTANTE: Solo guardar UNA vez usando el método específico para datos completos
            # NO guardar usando las funciones individuales para evitar duplicados
            try:
                await optimized_db.upsert_current_rate_fast(data=complete_result)
                logger.info("💾 Binance P2P COMPLETE rates guardados en base de datos (UNA SOLA LÍNEA)")
            except Exception as e:
                logger.warning(f"⚠️ No se pudieron guardar Binance P2P COMPLETE rates en BD: {e}")
            
            return {"status": "success", "data": complete_result}
        else:
            errors = []
            if buy_result["status"] != "success":
                errors.append(f"Compra: {buy_result.get('error', 'Error desconocido')}")
            if sell_result["status"] != "success":
                errors.append(f"Venta: {sell_result.get('error', 'Error desconocido')}")
            
            raise Exception(f"Error obteniendo datos completos: {'; '.join(errors)}")
            
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos completos de Binance P2P: {e}")
        return {"status": "error", "error": str(e)}


async def update_binance_p2p_rates() -> Dict[str, any]:
    """
    Actualizar cotizaciones de Binance P2P Venezuela usando la API oficial
    """
    try:
        logger.info("🟡 Obteniendo cotizaciones de Binance P2P...")
        
        # Usar la función completa de Binance P2P que obtiene tanto compra como venta
        result = await fetch_binance_p2p_complete()
        
        if result["status"] == "success":
            data = result["data"]
            buy_price = data['buy_usdt']['price']
            sell_price = data['sell_usdt']['price']
            logger.info(f"✅ Binance P2P obtenido: Buy={buy_price}, Sell={sell_price}")
        else:
            logger.error(f"❌ Error obteniendo datos de Binance P2P: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de Binance P2P: {e}")
        return {"status": "error", "error": str(e)}


async def save_rate_to_database(exchange_code: str, symbol: str, buy_price: float, sell_price: float) -> bool:
    """
    Guardar cotización en la base de datos
    """
    try:
        # TODO: Implementar guardado real en BD
        logger.info(f"💾 Guardando {symbol} de {exchange_code}: {buy_price}/{sell_price}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error guardando en BD: {e}")
        return False


async def get_latest_rates() -> Dict[str, any]:
    """
    Obtener las últimas cotizaciones de la base de datos
    """
    try:
        # TODO: Implementar consulta real
        logger.info("📊 Obteniendo últimas cotizaciones...")
        
        mock_rates = {
            "bcv": {"usd_ves": 36.50, "last_update": "2024-01-01T12:00:00Z"},
            "binance_p2p": {"usdt_ves": {"buy": 37.20, "sell": 37.80}, "last_update": "2024-01-01T12:05:00Z"},
            "timestamp": datetime.now().isoformat()
        }
        
        return {"status": "success", "data": mock_rates}
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo cotizaciones: {e}")
        return {"status": "error", "error": str(e)}


# Funciones auxiliares para el scraping
def clean_rate_text(text: str) -> Optional[float]:
    """
    Limpiar y convertir texto de cotización a float
    """
    try:
        # Remover caracteres no numéricos excepto punto y coma
        cleaned = re.sub(r'[^\d.,]', '', text)
        # Reemplazar coma por punto para conversión a float
        cleaned = cleaned.replace(',', '.')
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def validate_rate_value(rate: float) -> bool:
    """
    Validar que el valor de la cotización sea razonable
    """
    # Para Venezuela, las cotizaciones típicamente están entre 1 y 1000
    return 0.1 <= rate <= 1000.0


# TODO: Implementar funciones específicas de cada API
# - fetch_binance_p2p_ads()
# - parse_binance_json()
# - calculate_spreads()
# - update_rate_history()


async def scrape_italcambios_rates() -> Dict[str, any]:
    """
    Hacer web scraping de la página de Italcambios para obtener cotizaciones USD/VES
    Siguiendo la estructura HTML específica:
    1. div con clases: container-fluid compra
    2. div con clase: slide-track
    3. div con clase: row mb-15
    4. div con clase: col-8 pl-0 y dentro de ese div esta encerrado: <p class="small">USD</p>
    5. Una vez consigas el <p> que diga USD. Regresas al <div> numero 2 con clase slide-track que dentro tiene una etiqueta <p> con clase small donde dice Compra y Venta.
    """
    try:
        logger.info("🏦 Iniciando scraping de Italcambios...")
        
        # URL de Italcambios
        url = "https://www.italcambio.com"
        
        # Headers para simular un navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Configuración del cliente HTTP
        connector = aiohttp.TCPConnector(ssl=False)  # Deshabilitar verificación SSL
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=aiohttp.ClientTimeout(total=30),
            connector=connector
        ) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ Error HTTP {response.status}: {error_text}")
                    raise Exception(f"Error HTTP {response.status}: {response.reason}")
                
                html_content = await response.text()
                logger.info(f"✅ Conexión exitosa a Italcambios")
        
        # Parsear el HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Paso 1: Buscar div con clases "container-fluid compra"
        container_fluid = soup.find('div', class_='container-fluid compra')
        if not container_fluid:
            raise Exception("No se encontró el div con clase 'container-fluid compra'")
        
        logger.info("✅ Paso 1: Encontrado div container-fluid compra")
        
        # Paso 2: Buscar div con clase "slide-track" dentro del container-fluid
        slide_track = container_fluid.find('div', class_='slide-track')
        if not slide_track:
            raise Exception("No se encontró el div con clase 'slide-track' dentro de container-fluid compra")
        
        logger.info("✅ Paso 2: Encontrado div slide-track")
        
        # Paso 3: Buscar div con clase "row mb-15" dentro de slide-track
        row_mb15 = slide_track.find('div', class_='row mb-15')
        if not row_mb15:
            raise Exception("No se encontró el div con clase 'row mb-15' dentro de slide-track")
        
        logger.info("✅ Paso 3: Encontrado div row mb-15")
        
        # Paso 4: Buscar div con clase "col-8 pl-0" dentro de row mb-15
        col_8_pl0 = row_mb15.find('div', class_='col-8 pl-0')
        if not col_8_pl0:
            raise Exception("No se encontró el div con clase 'col-8 pl-0' dentro de row mb-15")
        
        logger.info("✅ Paso 4: Encontrado div col-8 pl-0")
        
        # Buscar el párrafo con clase "small" que contenga "USD"
        usd_paragraph = col_8_pl0.find('p', class_='small', string=lambda text: text and 'USD' in text)
        if not usd_paragraph:
            # Buscar alternativamente por texto que contenga "USD" en cualquier párrafo small
            usd_paragraph = col_8_pl0.find('p', class_='small')
            if usd_paragraph and 'USD' not in usd_paragraph.get_text():
                usd_paragraph = None
        
        if not usd_paragraph:
            raise Exception("No se encontró el párrafo con clase 'small' que contenga 'USD' dentro de col-8 pl-0")
        
        logger.info("✅ Paso 5: Encontrado párrafo con USD")
        
        # Paso 5: Regresar al div slide-track (paso 2) y buscar el párrafo con clase "small" que contenga "Compra" y "Venta"
        # Buscar todos los párrafos con clase "small" dentro de slide-track
        price_paragraphs = slide_track.find_all('p', class_='small')
        
        price_paragraph = None
        for p in price_paragraphs:
            text = p.get_text()
            if 'Compra' in text and 'Venta' in text:
                price_paragraph = p
                break
        
        if not price_paragraph:
            raise Exception("No se encontró el párrafo con clase 'small' que contenga 'Compra' y 'Venta' dentro de slide-track")
        
        price_text = price_paragraph.get_text()
        logger.info(f"📊 Texto de precios encontrado: {price_text}")
        
        # Extraer precios usando regex
        # Patrón para encontrar "Compra: X.XXXXX" y "Venta: X.XXXXX"
        compra_pattern = r'Compra:\s*(\d+[.,]\d+)'
        venta_pattern = r'Venta:\s*(\d+[.,]\d+)'
        
        compra_match = re.search(compra_pattern, price_text)
        venta_match = re.search(venta_pattern, price_text)
        
        if not compra_match or not venta_match:
            raise Exception(f"No se pudieron extraer los precios del texto: {price_text}")
        
        # Convertir a float (reemplazar coma por punto)
        compra_price = float(compra_match.group(1).replace(',', '.'))
        venta_price = float(venta_match.group(1).replace(',', '.'))
        
        # Validar que los precios sean razonables
        if not validate_rate_value(compra_price) or not validate_rate_value(venta_price):
            raise Exception(f"Precios fuera del rango esperado: Compra={compra_price}, Venta={venta_price}")
        
        # Crear el resultado
        result = {
            "usd_ves_compra": compra_price,
            "usd_ves_venta": venta_price,
            "usd_ves_promedio": round((compra_price + venta_price) / 2, 4),
            "timestamp": datetime.now().isoformat(),
            "source": "italcambios",
            "scraping_method": "web_scraping",
            "url": url
        }
        
        logger.info(f"✅ Italcambios scraping exitoso: Compra={compra_price}, Venta={venta_price}")
        
        # Guardar en base de datos
        try:
            await optimized_db.upsert_current_rate_fast(data=result)
            logger.info("💾 Italcambios rates guardados en base de datos")
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron guardar Italcambios rates en BD: {e}")
        
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(f"❌ Error en scraping de Italcambios: {e}")
        return {"status": "error", "error": str(e)}


async def update_italcambios_rates() -> Dict[str, any]:
    """
    Actualizar cotizaciones de Italcambios
    """
    try:
        logger.info("🏦 Obteniendo cotizaciones de Italcambios...")
        
        # Usar la función de scraping real
        result = await scrape_italcambios_rates()
        
        if result["status"] == "success":
            data = result["data"]
            logger.info(f"✅ Italcambios obtenido: Compra={data['usd_ves_compra']}, Venta={data['usd_ves_venta']}")
        else:
            logger.error(f"❌ Error obteniendo datos de Italcambios: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos de Italcambios: {e}")
        return {"status": "error", "error": str(e)}
