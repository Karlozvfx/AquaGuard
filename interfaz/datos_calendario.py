"""
Datos del Calendario (sección 6), sin tkinter: se puede probar sin abrir ventanas.

Reglas de honestidad:
- Solo se muestra lo que está guardado en SQLite. Un día sin registro se marca "SIN REGISTRO",
  nunca se rellena con valores inventados.
- Si el día viene de simulación/estimación se marca es_estimacion = True para que la interfaz lo diga.
- El pronóstico de un día es el que se guardó en su momento (con origen y fecha de actualización).
"""
import calendar
from dataclasses import dataclass
from datetime import date
from typing import Optional

MESES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
            "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
DIAS_SEMANA_LARGO = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# categoría del día -> (clave de color en estilos.COLORES, descripción para la leyenda)
CATEGORIAS = {
    "LLUVIA": ("lluvia", "Llovió"),
    "ALMACENADA": ("ahorro", "No llovió · riego con agua de lluvia guardada"),
    "MIXTO": ("alerta", "Riego mixto (lluvia + convencional)"),
    "CONVENCIONAL": ("convencional", "Solo agua convencional"),
    "SIN_REGISTRO": ("inactivo", "Sin registro"),
    "FUTURO": ("inactivo", "Fecha futura"),
}


@dataclass
class DiaInfo:
    fecha: str                              # 'YYYY-MM-DD'
    categoria: str = "SIN_REGISTRO"
    registrado: bool = False
    es_estimacion: bool = True
    llovio: Optional[bool] = None
    precipitacion_mm: Optional[float] = None
    recolectada_l: float = 0.0
    lluvia_usada_l: float = 0.0
    convencional_l: float = 0.0
    total_l: float = 0.0
    ahorrada_l: float = 0.0
    nivel_deposito_l: Optional[float] = None
    riego1: Optional[str] = None
    riego2: Optional[str] = None
    modo_lluvia: Optional[bool] = None
    motivo: Optional[str] = None
    # pronóstico guardado para ese día (si existe)
    pron_prob: Optional[float] = None
    pron_origen: Optional[str] = None
    pron_actualizado: Optional[str] = None
    pron_vigente: Optional[bool] = None

    @property
    def dia(self) -> int:
        return int(self.fecha[8:10])

    def titulo_largo(self) -> str:
        d = date.fromisoformat(self.fecha)
        return f"{DIAS_SEMANA_LARGO[d.weekday()]} {d.day} de {MESES_ES[d.month - 1].lower()} de {d.year}"


def _categoria(fila: dict) -> str:
    if fila["llovio"]:
        return "LLUVIA"
    usada, conv = fila["lluvia_usada_l"] or 0.0, fila["convencional_l"] or 0.0
    if usada > 0 and conv <= 0:
        return "ALMACENADA"
    if usada > 0 and conv > 0:
        return "MIXTO"
    return "CONVENCIONAL"


def info_dia(repo, fecha: str, hoy: Optional[str] = None) -> DiaInfo:
    """Toda la información guardada de un día (o un DiaInfo vacío marcado SIN_REGISTRO / FUTURO)."""
    hoy = hoy or date.today().isoformat()
    fila = repo.dia(fecha)
    info = DiaInfo(fecha=fecha)

    # Pronóstico guardado (puede existir aunque el día no tenga registro de consumo)
    p = repo.prediccion_dia(fecha)
    if p is not None:
        info.pron_prob, info.pron_origen = p["prob_lluvia"], p["origen"]
        info.pron_actualizado, info.pron_vigente = p["actualizado"], bool(p["vigente"])

    if fila is None:
        info.categoria = "FUTURO" if fecha > hoy else "SIN_REGISTRO"
        return info

    f = dict(fila)
    info.registrado = True
    info.es_estimacion = bool(f["es_estimacion"])
    info.llovio = bool(f["llovio"])
    info.precipitacion_mm = f["precipitacion_mm"]
    info.recolectada_l = f["agua_recolectada_l"] or 0.0
    info.lluvia_usada_l = f["lluvia_usada_l"] or 0.0
    info.convencional_l = f["convencional_l"] or 0.0
    info.total_l = f["total_consumido_l"] or 0.0
    info.ahorrada_l = f["agua_ahorrada_l"] or 0.0
    info.nivel_deposito_l = f["nivel_deposito_l"]
    info.riego1, info.riego2 = f["riego1"], f["riego2"]
    info.modo_lluvia = bool(f["modo_lluvia"])
    act = repo.ultima_activacion(fecha)
    info.motivo = act["motivo"] if act is not None else None
    info.categoria = _categoria(f)
    return info


def anios_con_datos(repo, extra: Optional[int] = None) -> list:
    """Años que tienen registros (más `extra` si se está mirando un año sin datos)."""
    anios = set(repo.anios_disponibles())
    if not anios:
        anios.add(date.today().year)
    if extra is not None:
        anios.add(extra)
    return sorted(anios)


def construir_mes(repo, anio: int, mes: int, hoy: Optional[str] = None) -> dict:
    """
    Devuelve {'semanas': [[DiaInfo|None]*7, ...], 'resumen': {...}} con la semana empezando en lunes.
    Usa UNA consulta por mes (no una por día).
    """
    hoy = hoy or date.today().isoformat()
    filas = {r["fecha"]: dict(r) for r in repo.dias_mes(anio, mes)}
    semanas, dias = [], []
    for semana in calendar.Calendar(firstweekday=0).monthdayscalendar(anio, mes):
        fila_sem = []
        for d in semana:
            if d == 0:
                fila_sem.append(None)
                continue
            fecha = f"{anio:04d}-{mes:02d}-{d:02d}"
            info = info_dia(repo, fecha, hoy) if fecha in filas or fecha <= hoy else \
                DiaInfo(fecha=fecha, categoria="FUTURO")
            dias.append(info)
            fila_sem.append(info)
        semanas.append(fila_sem)

    reg = [d for d in dias if d.registrado]
    resumen = {
        "dias_registrados": len(reg),
        "dias_lluviosos": sum(1 for d in reg if d.llovio),
        "precipitacion_mm": sum(d.precipitacion_mm or 0 for d in reg),
        "recolectada_l": sum(d.recolectada_l for d in reg),
        "lluvia_usada_l": sum(d.lluvia_usada_l for d in reg),
        "convencional_l": sum(d.convencional_l for d in reg),
        "total_l": sum(d.total_l for d in reg),
        "ahorrada_l": sum(d.ahorrada_l for d in reg),
        "hay_estimacion": any(d.es_estimacion for d in reg),
    }
    return {"semanas": semanas, "resumen": resumen}


def mm_por_dia_anio(repo, anio: int) -> dict:
    """{'YYYY-MM-DD': mm o None} de los días registrados del año (para el mapa anual)."""
    return {r["fecha"]: r["precipitacion_mm"] for r in repo.dias_anio(anio)}


def mismo_dia_otros_anios(repo, fecha: str) -> list:
    """Mismo día (mes-día) en OTROS años que tengan registro: sirve para comparar resultados históricos."""
    otros = []
    for r in repo.mismo_dia_otros_anios(fecha[5:10]):
        if r["fecha"] != fecha:
            otros.append(info_dia(repo, r["fecha"], hoy="9999-12-31"))
    return otros


def mover_mes(anio: int, mes: int, delta: int):
    """Avanza/retrocede meses cruzando años."""
    n = anio * 12 + (mes - 1) + delta
    return n // 12, n % 12 + 1


def ajustar_fecha(fecha: str, anio: int, mes: int) -> str:
    """Mantiene el mismo día al cambiar de mes/año (recorta a fin de mes: 31 → 28/29/30)."""
    dia = min(int(fecha[8:10]), calendar.monthrange(anio, mes)[1])
    return f"{anio:04d}-{mes:02d}-{dia:02d}"
