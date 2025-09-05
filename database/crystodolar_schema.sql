-- ========================================
-- CrystoAPIVzla - Estructura de Base de Datos
-- FastAPI + Supabase (PostgreSQL)
-- Migrado de Neon.tech a Supabase Transaction Mode
-- ========================================

-- Habilitar extensiones necesarias para Supabase
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" CASCADE;

-- ========================================
-- TABLAS PRINCIPALES
-- ========================================

-- Tabla de fuentes de datos (exchanges)
CREATE TABLE exchanges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(100) NOT NULL,
  code VARCHAR(20) UNIQUE NOT NULL,
  type VARCHAR(20) NOT NULL CHECK (type IN ('fiat', 'crypto')),
  base_url VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  operating_hours JSONB,
  update_frequency INTEGER DEFAULT 300,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de pares de monedas
CREATE TABLE currency_pairs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  base_currency VARCHAR(10) NOT NULL,
  quote_currency VARCHAR(10) NOT NULL,
  symbol VARCHAR(20) UNIQUE NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de cotizaciones actuales (adaptada para Supabase)
CREATE TABLE current_rates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_code VARCHAR(20) NOT NULL,
  currency_pair VARCHAR(20) NOT NULL,
  buy_price DECIMAL(15,4) NOT NULL,
  sell_price DECIMAL(15,4) NOT NULL,
  avg_price DECIMAL(15,4) GENERATED ALWAYS AS ((buy_price + sell_price) / 2) STORED,
  variation_24h DECIMAL(8,4) DEFAULT 0,
  volume_24h DECIMAL(20,4),
  source VARCHAR(50) DEFAULT 'api',
  market_status VARCHAR(20) DEFAULT 'active' CHECK (market_status IN ('active', 'inactive', 'maintenance')),
  last_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(exchange_code, currency_pair)
);

-- Tabla de histórico de cotizaciones (simplificada para Supabase)
CREATE TABLE rate_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_code VARCHAR(20) NOT NULL,
  currency_pair VARCHAR(20) NOT NULL,
  buy_price DECIMAL(15,4) NOT NULL,
  sell_price DECIMAL(15,4) NOT NULL,
  avg_price DECIMAL(15,4) NOT NULL,
  volume_24h DECIMAL(20,4),
  source VARCHAR(50) DEFAULT 'api',
  api_method VARCHAR(50) DEFAULT 'fetch',
  trade_type VARCHAR(50) DEFAULT 'general',
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de estado del mercado
CREATE TABLE market_status (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE CASCADE,
  is_open BOOLEAN DEFAULT false,
  status VARCHAR(50) DEFAULT 'unknown' CHECK (status IN ('open', 'closed', 'maintenance', 'unknown')),
  next_open TIMESTAMP WITH TIME ZONE,
  next_close TIMESTAMP WITH TIME ZONE,
  last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(exchange_id)
);

-- Tabla de logs de APIs externas
CREATE TABLE api_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exchange_id UUID REFERENCES exchanges(id) ON DELETE SET NULL,
  endpoint VARCHAR(255),
  status_code INTEGER,
  response_time_ms INTEGER,
  error_message TEXT,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ========================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ========================================

-- Índices para rate_history (consultas de gráficas) - corregidos para Supabase
CREATE INDEX idx_rate_history_timestamp ON rate_history(timestamp DESC);
CREATE INDEX idx_rate_history_exchange_pair ON rate_history(exchange_code, currency_pair);
CREATE INDEX idx_rate_history_timeframe ON rate_history(exchange_code, currency_pair, timestamp DESC);

-- Índices para current_rates - corregidos para Supabase
CREATE INDEX idx_current_rates_market_status ON current_rates(market_status) WHERE market_status = 'active';
CREATE INDEX idx_current_rates_last_update ON current_rates(last_update DESC);
CREATE INDEX idx_current_rates_exchange_pair ON current_rates(exchange_code, currency_pair);

-- Índices para api_logs
CREATE INDEX idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX idx_api_logs_exchange ON api_logs(exchange_id, timestamp DESC);

-- ========================================
-- FUNCIONES Y TRIGGERS
-- ========================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER update_exchanges_updated_at
  BEFORE UPDATE ON exchanges
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_market_status_updated_at
  BEFORE UPDATE ON market_status
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Función para limpiar datos antiguos
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
  -- Eliminar histórico mayor a 90 días
  DELETE FROM rate_history 
  WHERE timestamp < NOW() - INTERVAL '90 days';
  
  -- Eliminar logs mayor a 30 días
  DELETE FROM api_logs 
  WHERE timestamp < NOW() - INTERVAL '30 days';
  
  -- Log de limpieza
  RAISE NOTICE 'Limpieza de datos antiguos completada en %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Función para calcular variación de precio (adaptada para Supabase)
CREATE OR REPLACE FUNCTION calculate_price_variation(
  p_exchange_code VARCHAR(20),
  p_currency_pair VARCHAR(20),
  p_current_price DECIMAL
)
RETURNS DECIMAL AS $$
DECLARE
  yesterday_price DECIMAL;
  variation DECIMAL;
BEGIN
  -- Obtener precio de hace 24 horas
  SELECT avg_price INTO yesterday_price
  FROM rate_history
  WHERE exchange_code = p_exchange_code
    AND currency_pair = p_currency_pair
    AND timestamp >= NOW() - INTERVAL '24 hours 30 minutes'
    AND timestamp <= NOW() - INTERVAL '23 hours 30 minutes'
  ORDER BY timestamp ASC
  LIMIT 1;
  
  -- Calcular variación porcentual
  IF yesterday_price IS NOT NULL AND yesterday_price > 0 THEN
    variation := ((p_current_price - yesterday_price) / yesterday_price) * 100;
  ELSE
    variation := 0;
  END IF;
  
  RETURN ROUND(variation, 4);
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- VISTAS PARA EL FRONTEND
-- ========================================

-- Vista principal para datos del mercado (simplificada para Supabase)
CREATE VIEW current_market_data AS
SELECT 
  cr.id,
  cr.exchange_code,
  cr.currency_pair,
  e.name as exchange_name,
  e.type as exchange_type,
  e.description,
  cp.base_currency,
  cp.quote_currency,
  cr.buy_price,
  cr.sell_price,
  cr.avg_price,
  cr.variation_24h,
  cr.volume_24h,
  cr.last_update,
  cr.market_status,
  ms.is_open as market_open,
  ms.status as market_status_detail,
  ms.next_open,
  ms.next_close
FROM current_rates cr
LEFT JOIN exchanges e ON cr.exchange_code = e.code
LEFT JOIN currency_pairs cp ON cr.currency_pair = cp.symbol
LEFT JOIN market_status ms ON e.id = ms.exchange_id
WHERE cr.market_status = 'active' AND (e.is_active IS NULL OR e.is_active = true)
ORDER BY cr.exchange_code, cr.currency_pair;

-- Vista para datos históricos optimizada (simplificada para Supabase)
CREATE VIEW historical_rates_view AS
SELECT 
  rh.id,
  rh.exchange_code,
  rh.currency_pair,
  e.name as exchange_name,
  e.type as exchange_type,
  cp.base_currency,
  cp.quote_currency,
  rh.buy_price,
  rh.sell_price,
  rh.avg_price,
  rh.volume_24h,
  rh.source,
  rh.trade_type,
  rh.timestamp,
  DATE_TRUNC('hour', rh.timestamp) as hour_bucket,
  DATE_TRUNC('day', rh.timestamp) as day_bucket
FROM rate_history rh
LEFT JOIN exchanges e ON rh.exchange_code = e.code
LEFT JOIN currency_pairs cp ON rh.currency_pair = cp.symbol
WHERE (e.is_active IS NULL OR e.is_active = true);

-- ========================================
-- POLÍTICAS RLS (Row Level Security)
-- ========================================
-- Nota: RLS deshabilitado para Supabase
-- Se manejará la seguridad desde FastAPI

-- ========================================
-- DATOS INICIALES
-- ========================================

-- Insertar exchanges iniciales (simplificado para Supabase)
INSERT INTO exchanges (name, code, type, description, operating_hours, update_frequency) VALUES
(
  'Banco Central de Venezuela', 
  'BCV', 
  'fiat', 
  'Tasa oficial del Banco Central de Venezuela',
  '{"start": "09:00", "end": "16:00", "timezone": "VET", "days": [1,2,3,4,5]}'::jsonb,
  3600
),
(
  'Binance P2P Venezuela', 
  'BINANCE_P2P', 
  'crypto', 
  'Mercado P2P de Binance para Venezuela',
  '{"start": "00:00", "end": "23:59", "timezone": "UTC", "days": [0,1,2,3,4,5,6]}'::jsonb,
  300
),
(
  'Italcambios', 
  'ITALCAMBIOS', 
  'fiat', 
  'Casa de cambio Italcambios - Cotizaciones USD/VES',
  '{"start": "08:00", "end": "18:00", "timezone": "VET", "days": [1,2,3,4,5,6]}'::jsonb,
  600
);

-- Insertar pares de monedas
INSERT INTO currency_pairs (base_currency, quote_currency, symbol) VALUES
('USDT', 'VES', 'USDT/VES'),
('USD', 'VES', 'USD/VES'),
('EUR', 'VES', 'EUR/VES');

-- Insertar estado inicial del mercado
INSERT INTO market_status (exchange_id, is_open, status) 
SELECT id, true, 'open' FROM exchanges;

-- Insertar datos iniciales en current_rates para evitar errores
INSERT INTO current_rates (exchange_code, currency_pair, buy_price, sell_price, source) VALUES
('BCV', 'USD/VES', 36.50, 36.50, 'initial_data'),
('BCV', 'EUR/VES', 39.50, 39.50, 'initial_data'),
('BINANCE_P2P', 'USDT/VES', 37.20, 37.80, 'initial_data'),
('ITALCAMBIOS', 'USD/VES', 150.00, 155.00, 'initial_data')
ON CONFLICT (exchange_code, currency_pair) DO NOTHING;

-- ========================================
-- DATOS MOCK PARA DESARROLLO (ELIMINADO)
-- ========================================
-- Nota: Los datos mock fueron eliminados porque usaban el esquema viejo
-- Los datos iniciales ya están insertados arriba usando el esquema correcto de Supabase

-- ========================================
-- TAREAS AUTOMÁTICAS
-- ========================================
-- Nota: Supabase incluye pg_cron, pero usaremos APScheduler desde FastAPI
-- La limpieza se ejecutará desde FastAPI con un scheduler
-- Ejemplo: APScheduler para ejecutar cleanup_old_data() diariamente

-- ========================================
-- COMENTARIOS FINALES
-- ========================================

-- COMMENT ON DATABASE postgres IS 'CrystoAPIVzla - Base de datos para cotizaciones USDT/VES migrada a Supabase';
-- Nota: Migrado de Neon.tech a Supabase Transaction Mode
COMMENT ON TABLE exchanges IS 'Fuentes de datos de cotizaciones (BCV, Binance, etc.)';
COMMENT ON TABLE currency_pairs IS 'Pares de monedas soportados';
COMMENT ON TABLE current_rates IS 'Cotizaciones actuales en tiempo real (compatible con Supabase)';
COMMENT ON TABLE rate_history IS 'Histórico de cotizaciones para gráficas (simplificado)';
COMMENT ON TABLE market_status IS 'Estado actual de cada mercado';
COMMENT ON TABLE api_logs IS 'Logs de llamadas a APIs externas';

-- ========================================
-- VERSIÓN Y METADATOS
-- ========================================

CREATE TABLE IF NOT EXISTS schema_version (
  version VARCHAR(10) PRIMARY KEY,
  applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  description TEXT
);

INSERT INTO schema_version (version, description) VALUES 
('1.0.0', 'Schema inicial de CrystoAPIVzla con soporte para BCV y Binance P2P'),
('2.0.0', 'Schema migrado a Supabase con Transaction Mode, sin prepared statements');

-- Fin del archivo
