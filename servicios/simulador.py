"""
Simulación (TODO lo generado aquí se marca como SIMULADO; NO son datos de SENAMHI).
Perfil estacional de ejemplo: cámbialo a tu zona.
"""
import random
from datetime import date, datetime, timedelta
from clima.senamhi import Pronostico

# Probabilidad diaria de lluvia por mes (ejemplo genérico tipo sierra: lluvias dic-mar)
PROB_MENSUAL = [0.55, 0.60, 0.55, 0.30, 0.10, 0.03, 0.02, 0.04, 0.12, 0.25, 0.30, 0.45]


def generar_anio(anio: int, semilla: int = 42):
    """Devuelve (lluvia_real{fecha:mm}, pronosticos{fecha:Pronostico})."""
    rnd = random.Random(semilla + anio)
    lluvia, pron = {}, {}
    d = date(anio, 1, 1)
    while d.year == anio:
        f = d.isoformat()
        p = PROB_MENSUAL[d.month - 1]
        llueve = rnd.random() < p
        mm = round(rnd.expovariate(1 / 6) + 0.5, 1) if llueve else 0.0
        lluvia[f] = mm
        # pronóstico simulado ruidoso (no acierta siempre)
        prob = max(0, min(100, (80 if llueve else 25) + rnd.gauss(0, 18) + (p - 0.3) * 40))
        pron[f] = Pronostico(f, round(prob), None, None, "SIMULADO",
                             datetime.now().isoformat(timespec="minutes"), True)
        d += timedelta(days=1)
    return lluvia, pron


def historial_simulado(anios, semilla=7):
    filas = []
    for a in anios:
        lluvia, _ = generar_anio(a, semilla)
        filas += list(lluvia.items())
    return filas
