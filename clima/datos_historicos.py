"""Importación y estadísticas del historial de lluvias (SENAMHI)."""
import csv
from collections import defaultdict

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def importar_csv(cfg, repo) -> int:
    """Lee cfg.archivo_historico (fecha,precipitacion_mm) y lo guarda como origen SENAMHI."""
    ruta = cfg.ruta(cfg.archivo_historico)
    if not ruta.exists():
        print(f"[HISTÓRICO] No existe {ruta}. Descarga los datos de SENAMHI y colócalos ahí.")
        return 0
    filas = []
    with open(ruta, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                filas.append((r["fecha"].strip(), float(r["precipitacion_mm"])))
            except (KeyError, ValueError):
                continue   # se ignoran filas incompletas, no se rellenan
    repo.guardar_historico(filas, "SENAMHI")
    return len(filas)


def estadisticas_mensuales(filas, umbral_mm=0.5):
    """
    filas: [(fecha, mm)]. Devuelve dict mes(1-12) -> {
        dias_obs, dias_lluvia, frecuencia, mm_prom_mes, dias_lluvia_prom_mes, anios}
    """
    dias_obs = defaultdict(int)
    dias_lluvia = defaultdict(int)
    mm_por_anio_mes = defaultdict(float)
    anios = defaultdict(set)
    for fecha, mm in filas:
        anio, mes = int(fecha[:4]), int(fecha[5:7])
        dias_obs[mes] += 1
        anios[mes].add(anio)
        mm_por_anio_mes[(anio, mes)] += mm
        if mm >= umbral_mm:
            dias_lluvia[mes] += 1
    res = {}
    for mes in range(1, 13):
        n = dias_obs[mes]
        na = len(anios[mes])
        res[mes] = {
            "dias_obs": n, "dias_lluvia": dias_lluvia[mes],
            "frecuencia": (dias_lluvia[mes] / n) if n else None,
            "mm_prom_mes": (sum(v for (a, m), v in mm_por_anio_mes.items() if m == mes) / na) if na else None,
            "anios": na,
            "dias_lluvia_prom_mes": (dias_lluvia[mes] / na) if na else None,
        }
    return res


def estadisticas_anuales(filas, umbral_mm=0.5):
    tot = defaultdict(lambda: {"mm": 0.0, "dias_lluvia": 0, "dias": 0})
    for fecha, mm in filas:
        a = int(fecha[:4])
        tot[a]["mm"] += mm
        tot[a]["dias"] += 1
        tot[a]["dias_lluvia"] += mm >= umbral_mm
    return dict(tot)


def clasificar_temporada(stats_mes):
    """'lluviosa' | 'seca' | 'transicion' | None (sin datos). Basado en frecuencia de días con lluvia."""
    f = stats_mes.get("frecuencia")
    if f is None:
        return None
    return "lluviosa" if f >= 0.40 else "seca" if f <= 0.10 else "transicion"
