"""Conexión SQLite y creación de tablas."""
import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS predicciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,              -- día pronosticado
    prob_lluvia REAL, precipitacion_mm REAL, temperatura_c REAL,
    origen TEXT NOT NULL,             -- SENAMHI / SIMULADO
    actualizado TEXT,                 -- cuándo se actualizó el dato
    vigente INTEGER NOT NULL,
    registrado_en TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS precipitaciones (
    fecha TEXT PRIMARY KEY, precipitacion_mm REAL, origen TEXT NOT NULL   -- SENAMHI / SENSOR / SIMULADO
);
CREATE TABLE IF NOT EXISTS historico_senamhi (
    fecha TEXT PRIMARY KEY, precipitacion_mm REAL NOT NULL, origen TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consumo_diario (
    fecha TEXT PRIMARY KEY,
    llovio INTEGER, precipitacion_mm REAL,
    agua_recolectada_l REAL, lluvia_usada_l REAL, convencional_l REAL,
    total_consumido_l REAL, agua_ahorrada_l REAL,
    nivel_deposito_l REAL, riego1 TEXT, riego2 TEXT, modo_lluvia INTEGER,
    es_estimacion INTEGER NOT NULL    -- 1 = valor simulado/estimado, 0 = medido
);
CREATE TABLE IF NOT EXISTS estado_sistemas (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    riego1 TEXT, riego2 TEXT, succion TEXT, nivel_deposito_l REAL, actualizado TEXT
);
CREATE TABLE IF NOT EXISTS activaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL, activo INTEGER NOT NULL, motivo TEXT,
    prob_lluvia REAL, umbral_efectivo REAL, registrado_en TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


def conectar(ruta: Path) -> sqlite3.Connection:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.executescript(ESQUEMA)
    return con
