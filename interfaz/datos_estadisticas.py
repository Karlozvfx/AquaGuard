"""
Datos de Estadísticas y Comparación entre años (sección 7), sin tkinter:
se puede probar sin abrir ventanas.

Reglas de honestidad:
- Solo se usan días registrados en SQLite. Un mes sin registros queda como None ("sin datos"),
  NUNCA como 0, para no confundir "no hay dato" con "no llovió / no se ahorró".
- Si el año contiene días simulados/estimados se marca `hay_estimacion` y la interfaz lo avisa.
- Un mes con registro parcial (p. ej. año en curso) se avisa en `meses_incompletos`: su total
  no es comparable con el de un mes completo.
"""
import calendar
from dataclasses import dataclass, field
from typing import Optional

MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_LARGOS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
                "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# clave en la base -> (etiqueta, unidad)
METRICAS = {
    "ahorrada_l": ("Agua ahorrada", "L"),
    "convencional_l": ("Agua convencional usada", "L"),
    "recolectada_l": ("Agua de lluvia recolectada", "L"),
    "lluvia_usada_l": ("Lluvia usada en riego", "L"),
    "total_l": ("Agua total consumida", "L"),
    "dias_lluviosos": ("Días lluviosos", "días"),
    "precipitacion_mm": ("Precipitación", "mm"),
}


@dataclass
class SerieAnual:
    anio: int
    valores: dict = field(default_factory=dict)      # clave -> [12 valores, None = mes sin datos]
    dias_registrados: list = field(default_factory=lambda: [0] * 12)
    hay_estimacion: bool = False

    @property
    def tiene_datos(self) -> bool:
        return any(d > 0 for d in self.dias_registrados)

    @property
    def meses_sin_datos(self) -> list:
        return [i for i, d in enumerate(self.dias_registrados) if d == 0]

    @property
    def meses_incompletos(self) -> list:
        """[(índice_mes, días_registrados, días_del_mes)] de meses con datos parciales."""
        out = []
        for i, d in enumerate(self.dias_registrados):
            total = calendar.monthrange(self.anio, i + 1)[1]
            if 0 < d < total:
                out.append((i, d, total))
        return out

    def total(self, clave: str) -> float:
        return float(sum(v for v in self.valores.get(clave, []) if v is not None))

    @property
    def dias_totales_registrados(self) -> int:
        return sum(self.dias_registrados)

    @property
    def pct_cubierto_lluvia(self) -> Optional[float]:
        """% del agua total de riego que salió de lluvia (= ahorrada / total). None si no hubo consumo."""
        t = self.total("total_l")
        return self.total("ahorrada_l") / t * 100 if t > 0 else None


@dataclass
class Ranking:
    meses: list      # índices 0-11 (puede haber empate)
    valor: float

    def nombre(self) -> str:
        return " y ".join(MESES_LARGOS[m] for m in self.meses)


def anios_con_datos(repo) -> list:
    return repo.anios_disponibles()


def serie_anual(repo, anio: int) -> SerieAnual:
    """12 valores por métrica (una consulta SQL). Meses sin registros = None."""
    s = SerieAnual(anio=anio, hay_estimacion=repo.anio_tiene_estimacion(anio))
    filas = {r["mes"]: r for r in repo.resumen_mensual(anio)}
    for clave in METRICAS:
        s.valores[clave] = [None] * 12
    for mes, r in filas.items():
        s.dias_registrados[mes - 1] = r["dias_registrados"] or 0
        for clave in METRICAS:
            s.valores[clave][mes - 1] = float(r[clave] or 0.0)
    return s


def ranking(serie: SerieAnual, clave: str) -> Optional[Ranking]:
    """Mes(es) con el mayor valor de `clave`. None si no hay datos o el máximo es 0."""
    vals = [(i, v) for i, v in enumerate(serie.valores.get(clave, [])) if v is not None]
    if not vals:
        return None
    mx = max(v for _, v in vals)
    if mx <= 0:
        return None
    return Ranking([i for i, v in vals if abs(v - mx) < 1e-9], mx)


def rankings_principales(serie: SerieAnual) -> dict:
    """Los 4 rankings pedidos en la sección 7."""
    return {
        "ahorro": ranking(serie, "ahorrada_l"),          # mes que más agua ahorró
        "convencional": ranking(serie, "convencional_l"),  # mes que más agua convencional usó
        "dias_lluviosos": ranking(serie, "dias_lluviosos"),  # mes con más días lluviosos
        "recolectada": ranking(serie, "recolectada_l"),    # mes que más agua recolectó
    }


def resumen_anual(serie: SerieAnual) -> dict:
    """Totales de todo el año (agua usada, ahorrada, etc.)."""
    return {
        "total_l": serie.total("total_l"),
        "convencional_l": serie.total("convencional_l"),
        "lluvia_usada_l": serie.total("lluvia_usada_l"),
        "recolectada_l": serie.total("recolectada_l"),
        "ahorrada_l": serie.total("ahorrada_l"),
        "dias_lluviosos": int(serie.total("dias_lluviosos")),
        "precipitacion_mm": serie.total("precipitacion_mm"),
        "dias_registrados": serie.dias_totales_registrados,
        "pct_lluvia": serie.pct_cubierto_lluvia,
    }


def series_para_comparar(repo, anios: list) -> list:
    """SerieAnual de cada año pedido (solo los que realmente tienen datos), ordenadas."""
    return [s for s in (serie_anual(repo, a) for a in sorted(set(anios))) if s.tiene_datos]


def variacion_pct(valor: float, base: float) -> Optional[float]:
    """Cambio porcentual frente al año base. None si la base es 0 (no se puede dividir)."""
    return None if base <= 0 else (valor - base) / base * 100


def mejor_anio(series: list, clave: str) -> Optional[int]:
    """Año con mayor total de `clave` (None si todos valen 0)."""
    if not series:
        return None
    mejor = max(series, key=lambda s: s.total(clave))
    return mejor.anio if mejor.total(clave) > 0 else None


def texto_meses(indices: list) -> str:
    return ", ".join(MESES_CORTOS[i] for i in indices)
