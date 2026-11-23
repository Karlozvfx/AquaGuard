"""
Prepara TODOS los datos que muestra el Dashboard (sin tkinter, fácil de probar).

Reglas de honestidad:
- El pronóstico mostrado es SOLO el de SENAMHI para HOY; si no hay, se dice "SIN PRONÓSTICO".
- Los datos de consumo/ahorro vienen de lo registrado; si es simulación se marca como ESTIMACIÓN.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from clima.senamhi import SenamhiCliente


@dataclass
class EstadoDashboard:
    hoy: str
    umbral: float
    # --- Pronóstico SENAMHI de hoy ---
    estado_pronostico: str = "SIN PRONÓSTICO"     # VIGENTE / DESACTUALIZADO / SIN PRONÓSTICO
    prob_lluvia: Optional[float] = None
    temperatura_c: Optional[float] = None
    pron_origen: str = "—"
    pron_actualizado: str = "—"
    # --- Último día registrado ---
    fecha_registro: Optional[str] = None
    es_estimacion: bool = True
    modo_lluvia: Optional[bool] = None
    motivo: str = "Aún no se ha evaluado ningún día"
    precipitacion_mm: float = 0.0
    recolectada_l: float = 0.0
    lluvia_usada_l: float = 0.0
    convencional_l: float = 0.0
    total_l: float = 0.0
    ahorrada_l: float = 0.0
    riego1: Optional[str] = None
    riego2: Optional[str] = None
    succion: Optional[str] = None
    nivel_deposito_l: float = 0.0
    capacidad_l: float = 0.0
    # --- Acumulados del mes y año del último día registrado ---
    mes_mm: float = 0.0
    mes_total_l: float = 0.0
    mes_ahorrada_l: float = 0.0
    anio_lluvia_usada_l: float = 0.0
    anio_convencional_l: float = 0.0
    anio_total_l: float = 0.0
    anio_ahorrada_l: float = 0.0
    serie: list = field(default_factory=list)


def obtener_estado(cfg, repo, hoy: Optional[str] = None) -> EstadoDashboard:
    hoy = hoy or date.today().isoformat()
    e = EstadoDashboard(hoy=hoy, umbral=cfg.umbral_lluvia, capacidad_l=cfg.capacidad_deposito_l)

    # 1) Pronóstico oficial de HOY (archivo/URL de SENAMHI configurado)
    pron = SenamhiCliente(cfg).obtener_pronostico(hoy)
    if pron is not None:
        e.pron_origen, e.pron_actualizado = pron.origen, pron.actualizado
        e.temperatura_c = pron.temperatura_c
        if pron.vigente:
            e.estado_pronostico, e.prob_lluvia = "VIGENTE", pron.prob_lluvia
        else:
            e.estado_pronostico = "DESACTUALIZADO"   # se muestra el dato, pero no se usa para activar nada
            e.prob_lluvia = pron.prob_lluvia

    # 2) Último día registrado en la base de datos
    d = repo.ultimo_dia()
    if d is not None:
        e.fecha_registro = d["fecha"]
        e.es_estimacion = bool(d["es_estimacion"])
        e.modo_lluvia = bool(d["modo_lluvia"])
        act = repo.ultima_activacion(d["fecha"])
        if act is not None:
            e.motivo = act["motivo"]
        e.precipitacion_mm = d["precipitacion_mm"] or 0.0
        e.recolectada_l = d["agua_recolectada_l"] or 0.0
        e.lluvia_usada_l = d["lluvia_usada_l"] or 0.0
        e.convencional_l = d["convencional_l"] or 0.0
        e.total_l = d["total_consumido_l"] or 0.0
        e.ahorrada_l = d["agua_ahorrada_l"] or 0.0
        e.riego1, e.riego2 = d["riego1"], d["riego2"]
        e.nivel_deposito_l = d["nivel_deposito_l"] or 0.0
        est = repo.estado_sistemas()
        e.succion = est["succion"] if est is not None else None

        anio, mes = int(d["fecha"][:4]), int(d["fecha"][5:7])
        m = repo.totales_mes(anio, mes)
        e.mes_mm, e.mes_total_l, e.mes_ahorrada_l = m["precipitacion_mm"], m["total_l"], m["ahorrada_l"]
        a = repo.resumen_anual(anio)
        e.anio_lluvia_usada_l = a["lluvia_usada_l"] or 0.0
        e.anio_convencional_l = a["convencional_l"] or 0.0
        e.anio_total_l = a["total_l"] or 0.0
        e.anio_ahorrada_l = a["ahorrada_l"] or 0.0
        e.serie = repo.ultimos_dias(30)
    return e
