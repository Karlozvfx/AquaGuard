"""Configuración central. Se guarda en config.json (se crea sola la primera vez)."""
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path

RAIZ = Path(__file__).parent
RUTA_CONFIG = RAIZ / "config.json"


@dataclass
class Config:
    # --- Ubicación (configurable por el usuario) ---
    localidad: str = "Villa El Salvador, Lima"
    estacion_senamhi: str = "SIN CONFIGURAR"   # nombre/código de estación SENAMHI

    # --- Lógica de activación ---
    umbral_lluvia: float = 70.0      # % mínimo para activar el modo lluvia
    margen_estacional: float = 5.0   # puntos que se suben/bajan según temporada
    umbral_lluvia_mm: float = 0.5    # mm mínimos para considerar que "llovió"
    min_dias_historicos: int = 365   # días mínimos de historial para ajustar

    # --- Fuentes de datos SENAMHI (NO hay endpoint inventado) ---
    # Archivo CSV descargado/exportado de SENAMHI: fecha,prob_lluvia,precipitacion_mm,temperatura_c
    archivo_pronostico: str = "datos/senamhi/pronostico.csv"
    # Archivo CSV histórico: fecha,precipitacion_mm
    archivo_historico: str = "datos/senamhi/historico.csv"
    # URL opcional (solo si tú dispones de una fuente oficial que entregue ese CSV)
    url_pronostico_csv: str = ""
    horas_vigencia_pronostico: int = 24

    # --- Parámetros físicos (ESTIMACIONES hasta tener sensores reales) ---
    area_captacion_m2: float = 20.0
    coef_escorrentia: float = 0.80
    capacidad_deposito_l: float = 1000.0
    demanda_riego1_l_dia: float = 120.0
    demanda_riego2_l_dia: float = 80.0
    usar_deposito_siempre: bool = True   # usar agua guardada aunque no esté en modo lluvia

    # --- Base de datos ---
    ruta_bd: str = "datos/sistema.db"

    def guardar(self):
        RUTA_CONFIG.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def cargar() -> "Config":
        if RUTA_CONFIG.exists():
            datos = json.loads(RUTA_CONFIG.read_text(encoding="utf-8"))
            base = asdict(Config())
            base.update({k: v for k, v in datos.items() if k in base})
            return Config(**base)
        cfg = Config()
        cfg.guardar()
        return cfg

    def ruta(self, relativa: str) -> Path:
        return RAIZ / relativa
