"""
Configuración de la aplicación
Manejo de variables de entorno con Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os
import json


class Settings(BaseSettings):
    """
    Configuración de la aplicación usando variables de entorno
    Compatible con Neon.tech y despliegue en producción
    """
    
    # Database (Supabase) - CREDENCIALES EN .env
    DATABASE_URL: str = Field(
        default="",
        description="URL de conexión a Supabase (Transaction Mode - puerto 6543)"
    )
    SUPABASE_URL: Optional[str] = Field(
        default=None,
        description="URL de Supabase para API"
    )
    SUPABASE_ANON_KEY: Optional[str] = Field(
        default=None,
        description="Clave anónima de Supabase"
    )
    # Connection for migrations (Session mode)
    DIRECT_DATABASE_URL: str = Field(
        default="",
        description="URL de conexión directa a Supabase (Session Mode - puerto 5432)"
    )
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    API_RELOAD: bool = True
    ENVIRONMENT: str = "development"
    
    # Security
    SECRET_KEY: str = Field(
        default="",
        description="Clave secreta para JWT (OBLIGATORIO en producción)"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # External APIs
    BCV_API_URL: str = "http://www.bcv.org.ve/"
    BINANCE_API_URL: str = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Redis Cache Configuration
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="URL de conexión a Redis para caché"
    )
    REDIS_ENABLED: bool = Field(
        default=True,
        description="Habilitar/deshabilitar caché Redis"
    )
    REDIS_TTL_CURRENT_RATES: int = Field(
        default=600,
        description="TTL en segundos para cotizaciones actuales (10 minutos)"
    )
    REDIS_TTL_LATEST_RATES: int = Field(
        default=300,
        description="TTL en segundos para historial de cotizaciones (5 minutos)"
    )
    
    # Rate Limiting
    REQUESTS_PER_MINUTE: int = 60
    BURST_LIMIT: int = 10
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:3001,https://crystoapivzla.site,https://www.crystoapivzla.site",
        description="Lista de orígenes permitidos para CORS separados por comas"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convertir CORS_ORIGINS string a lista"""
        if not self.CORS_ORIGINS:
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "https://crystoapivzla.site",
                "https://www.crystoapivzla.site"
            ]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]
    
    # Background Tasks
    SCHEDULER_ENABLED: bool = True
    CLEANUP_HOUR: int = 2
    UPDATE_FREQUENCY_SECONDS: int = 300
    
    # Notifications
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    EMAIL_ENABLED: bool = False
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Data Sources Config
    BCV_UPDATE_INTERVAL: int = 3600  # 1 hora
    BINANCE_UPDATE_INTERVAL: int = 3600  # 1 hora
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 30
    
    # Computed properties
    @property
    def is_production(self) -> bool:
        """Verificar si estamos en producción"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Verificar si estamos en desarrollo"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def database_url_sync(self) -> str:
        """URL de base de datos para conexiones síncronas"""
        return self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    
    @property
    def database_url_async(self) -> str:
        """URL de base de datos para conexiones asíncronas (Transaction Mode para serverless)"""
        # Supabase Transaction Mode - NO soporta prepared statements
        # Eliminar cualquier parámetro SSL explícito para evitar conflictos
        base_url = self.DATABASE_URL.split('?')[0]  # Quitar parámetros existentes
        return base_url + "?pgbouncer=true"
    
    @property
    def database_url_direct(self) -> str:
        """URL de base de datos para conexiones directas (Session Mode para migraciones)"""
        # Supabase Session Mode - soporta prepared statements
        # Eliminar cualquier parámetro SSL explícito para evitar conflictos
        return self.DIRECT_DATABASE_URL.split('?')[0]  # Limpiar parámetros
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Instancia global de configuración
settings = Settings()


def get_settings() -> Settings:
    """
    Dependency injection para obtener configuración
    Útil para testing y override de configuración
    """
    return settings
