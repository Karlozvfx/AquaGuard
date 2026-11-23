"""Motor: ejecuta un día completo (decisión -> actuadores -> cálculo -> base de datos)."""
from clima.prediccion import decidir
from clima.datos_historicos import estadisticas_mensuales
from servicios.ahorro import calcular_dia
from sistemas.riego import SistemaRiego
from sistemas.succion import SistemaSuccion
from sistemas.sensores import Deposito


class Motor:
    def __init__(self, cfg, repo, actuadores, sensor_lluvia, es_simulacion=True):
        self.cfg, self.repo, self.sensor = cfg, repo, sensor_lluvia
        self.es_estimacion = es_simulacion or getattr(sensor_lluvia, "es_estimacion", True)
        self.deposito = Deposito(cfg.capacidad_deposito_l, repo.ultimo_nivel_deposito())
        self.riego1 = SistemaRiego("Riego 1", "riego1", cfg.demanda_riego1_l_dia, actuadores)
        self.riego2 = SistemaRiego("Riego 2", "riego2", cfg.demanda_riego2_l_dia, actuadores)
        self.succion = SistemaSuccion(cfg.area_captacion_m2, cfg.coef_escorrentia, self.deposito, actuadores)
        self.act = actuadores
        self.recalcular_historial()

    def recalcular_historial(self):
        filas = [tuple(f) for f in self.repo.historico()]
        self.stats = estadisticas_mensuales(filas, self.cfg.umbral_lluvia_mm)
        self.dias_historial = len(filas)

    def ejecutar_dia(self, fecha: str, pron) -> dict:
        if pron:
            self.repo.guardar_prediccion(pron)
        mes = int(fecha[5:7])
        d = decidir(pron, self.stats.get(mes), self.dias_historial, self.cfg)
        self.repo.guardar_activacion(fecha, d.activar, d.motivo, d.prob_lluvia, d.umbral_efectivo)

        # --- Acciones del modo lluvia ---
        if d.activar:
            self.riego1.anular(); self.riego2.anular(); self.succion.armar()
        else:
            self.riego1.habilitar(); self.riego2.habilitar(); self.succion.desarmar()

        # --- Lo que realmente pasó (sensor de lluvia) ---
        mm = self.sensor.leer_mm(fecha)
        llovio = mm >= self.cfg.umbral_lluvia_mm
        recolectada, _ = self.succion.captar(mm, self.cfg.umbral_lluvia_mm)

        # --- Riego del día ---
        # Modo lluvia: se riega con agua guardada; si no alcanza, el convencional entra solo
        # como RESPALDO (la probabilidad no garantiza lluvia y no se deben dejar plantas sin agua).
        usar_dep = d.activar or self.cfg.usar_deposito_siempre
        dem1, dem2 = self.cfg.demanda_riego1_l_dia, self.cfg.demanda_riego2_l_dia
        c1 = calcular_dia(dem1, self.deposito, usar_dep)
        c2 = calcular_dia(dem2, self.deposito, usar_dep)

        def fuente(c, dem):
            if c["lluvia_usada_l"] >= dem: return "LLUVIA"
            if c["lluvia_usada_l"] > 0:    return "MIXTO"
            return "CONVENCIONAL"

        def etiqueta(c, dem):
            f = fuente(c, dem)
            if d.activar:
                return "ANULADO (riego con agua de lluvia)" if f == "LLUVIA" else f"{f} (respaldo)"
            return f

        e1, e2 = etiqueta(c1, dem1), etiqueta(c2, dem2)
        reg = {
            "fecha": fecha, "llovio": int(llovio), "precipitacion_mm": mm,
            "agua_recolectada_l": round(recolectada, 2),
            "lluvia_usada_l": round(c1["lluvia_usada_l"] + c2["lluvia_usada_l"], 2),
            "convencional_l": round(c1["convencional_l"] + c2["convencional_l"], 2),
            "total_consumido_l": round(c1["total_consumido_l"] + c2["total_consumido_l"], 2),
            "agua_ahorrada_l": round(c1["agua_ahorrada_l"] + c2["agua_ahorrada_l"], 2),
            "nivel_deposito_l": round(self.deposito.nivel_l, 2),
            "riego1": e1, "riego2": e2, "modo_lluvia": int(d.activar),
            "es_estimacion": int(self.es_estimacion),
        }
        self.repo.guardar_precipitacion(fecha, mm, "SIMULADO" if self.es_estimacion else "SENSOR")
        self.repo.guardar_dia(reg)
        self.repo.guardar_estado(e1, e2, "ARMADO" if self.succion.armado else "APAGADO", self.deposito.nivel_l)
        reg["decision"] = d
        return reg
