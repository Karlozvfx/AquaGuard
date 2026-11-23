"""
Acceso a datos de SENAMHI.

IMPORTANTE: este módulo NO inventa ninguna API ni endpoint de SENAMHI.
Solo lee datos que TÚ le proporcionas:
  1) Un archivo CSV local (exportado/descargado de SENAMHI) -> config.archivo_pronostico
  2) Opcionalmente, una URL que devuelva ese mismo CSV -> config.url_pronostico_csv

Formato del CSV de pronóstico (con encabezado):
    fecha,prob_lluvia,precipitacion_mm,temperatura_c
    2026-11-23,80,4.5,17.2
(prob_lluvia en %, las demás columnas pueden ir vacías si el dato no existe)

Si no hay datos o no son del día pedido, se devuelve None (o un pronóstico NO vigente).
Nunca se rellena con datos históricos ni inventados.
"""
import csv
import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional


@dataclass
class Pronostico:
    fecha: str
    prob_lluvia: Optional[float]
    precipitacion_mm: Optional[float]
    temperatura_c: Optional[float]
    origen: str            # "SENAMHI (archivo)" / "SENAMHI (url)" / "SIMULADO"
    actualizado: str       # fecha/hora de actualización conocida
    vigente: bool          # False => no debe usarse para activar nada


def _num(txt):
    try:
        return float(txt) if txt not in (None, "") else None
    except ValueError:
        return None


class SenamhiCliente:
    def __init__(self, cfg):
        self.cfg = cfg

    def _leer_texto(self):
        """Devuelve (texto_csv, origen, actualizado) o None si no hay fuente."""
        if self.cfg.url_pronostico_csv:
            try:
                import requests
                r = requests.get(self.cfg.url_pronostico_csv, timeout=10)
                r.raise_for_status()
                return r.text, "SENAMHI (url)", datetime.now().isoformat(timespec="minutes")
            except Exception as e:  # sin conexión, etc.
                print(f"[SENAMHI] No se pudo consultar la URL ({e}). Se intentará el archivo local.")
        ruta = self.cfg.ruta(self.cfg.archivo_pronostico)
        if ruta.exists():
            mod = datetime.fromtimestamp(ruta.stat().st_mtime).isoformat(timespec="minutes")
            return ruta.read_text(encoding="utf-8-sig"), "SENAMHI (archivo)", mod
        return None

    def obtener_pronostico(self, fecha: str) -> Optional[Pronostico]:
        fuente = self._leer_texto()
        if fuente is None:
            return None
        texto, origen, actualizado = fuente
        for fila in csv.DictReader(io.StringIO(texto)):
            if fila.get("fecha", "").strip() == fecha:
                limite = datetime.now() - timedelta(hours=self.cfg.horas_vigencia_pronostico)
                vigente = datetime.fromisoformat(actualizado) >= limite
                return Pronostico(fecha, _num(fila.get("prob_lluvia")), _num(fila.get("precipitacion_mm")),
                                  _num(fila.get("temperatura_c")), origen, actualizado, vigente)
        return None
