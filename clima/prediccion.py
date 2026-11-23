"""
Algoritmo de decisión.

1. La BASE es el pronóstico oficial vigente de SENAMHI (prob_lluvia).
2. El historial mensual NO sustituye al pronóstico: solo ajusta el umbral unos puntos:
      temporada lluviosa -> umbral - margen
      temporada seca     -> umbral + margen
      transición / historial insuficiente -> umbral sin cambios
3. Sin pronóstico vigente => NO se activa el modo lluvia (no se inventa nada).
Activa si prob_lluvia >= umbral_efectivo.
"""
from dataclasses import dataclass
from typing import Optional
from clima.datos_historicos import clasificar_temporada


@dataclass
class Decision:
    activar: bool
    motivo: str
    prob_lluvia: Optional[float]
    umbral_efectivo: float
    temporada: Optional[str]


def decidir(pron, stats_mes: Optional[dict], dias_historial: int, cfg) -> Decision:
    umbral = cfg.umbral_lluvia
    temporada = None
    if stats_mes and dias_historial >= cfg.min_dias_historicos:
        temporada = clasificar_temporada(stats_mes)
        if temporada == "lluviosa":
            umbral -= cfg.margen_estacional
        elif temporada == "seca":
            umbral += cfg.margen_estacional
    umbral = max(0.0, min(100.0, umbral))

    if pron is None:
        return Decision(False, "Sin pronóstico disponible: no se activa el modo lluvia", None, umbral, temporada)
    if not pron.vigente:
        return Decision(False, "Pronóstico desactualizado: no se usa", pron.prob_lluvia, umbral, temporada)
    if pron.prob_lluvia is None:
        return Decision(False, "El pronóstico no incluye probabilidad de lluvia", None, umbral, temporada)
    if pron.prob_lluvia >= umbral:
        return Decision(True, f"Probabilidad {pron.prob_lluvia:.0f}% >= umbral {umbral:.0f}%",
                        pron.prob_lluvia, umbral, temporada)
    return Decision(False, f"Probabilidad {pron.prob_lluvia:.0f}% < umbral {umbral:.0f}%",
                    pron.prob_lluvia, umbral, temporada)
