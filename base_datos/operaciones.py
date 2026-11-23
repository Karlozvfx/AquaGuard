"""Operaciones de lectura/escritura sobre la base de datos."""
import sqlite3
from datetime import datetime


class Repositorio:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    # ---------- Escritura ----------
    def guardar_prediccion(self, p):
        self.con.execute(
            "INSERT INTO predicciones(fecha,prob_lluvia,precipitacion_mm,temperatura_c,origen,actualizado,vigente)"
            " VALUES(?,?,?,?,?,?,?)",
            (p.fecha, p.prob_lluvia, p.precipitacion_mm, p.temperatura_c, p.origen, p.actualizado, int(p.vigente)))
        self.con.commit()

    def guardar_precipitacion(self, fecha, mm, origen):
        self.con.execute("INSERT OR REPLACE INTO precipitaciones VALUES(?,?,?)", (fecha, mm, origen))
        self.con.commit()

    def guardar_historico(self, filas, origen):
        """filas: iterable de (fecha 'YYYY-MM-DD', mm)."""
        self.con.executemany("INSERT OR REPLACE INTO historico_senamhi VALUES(?,?,?)",
                             [(f, mm, origen) for f, mm in filas])
        self.con.commit()

    def guardar_dia(self, r: dict):
        cols = ",".join(r.keys())
        marcas = ",".join("?" * len(r))
        self.con.execute(f"INSERT OR REPLACE INTO consumo_diario({cols}) VALUES({marcas})", tuple(r.values()))
        self.con.commit()

    def guardar_estado(self, riego1, riego2, succion, nivel):
        self.con.execute("INSERT OR REPLACE INTO estado_sistemas VALUES(1,?,?,?,?,?)",
                         (riego1, riego2, succion, nivel, datetime.now().isoformat(timespec="seconds")))
        self.con.commit()

    def guardar_activacion(self, fecha, activo, motivo, prob, umbral):
        self.con.execute("INSERT INTO activaciones(fecha,activo,motivo,prob_lluvia,umbral_efectivo) VALUES(?,?,?,?,?)",
                         (fecha, int(activo), motivo, prob, umbral))
        self.con.commit()

    # ---------- Lectura ----------
    def historico(self, origen=None):
        q, a = "SELECT fecha, precipitacion_mm FROM historico_senamhi", ()
        if origen:
            q, a = q + " WHERE origen=?", (origen,)
        return self.con.execute(q + " ORDER BY fecha", a).fetchall()

    def ultimo_nivel_deposito(self, defecto=0.0):
        fila = self.con.execute("SELECT nivel_deposito_l FROM consumo_diario ORDER BY fecha DESC LIMIT 1").fetchone()
        return fila[0] if fila else defecto

    def dia(self, fecha):
        return self.con.execute("SELECT * FROM consumo_diario WHERE fecha=?", (fecha,)).fetchone()

    def anios_disponibles(self):
        return [int(f[0]) for f in self.con.execute(
            "SELECT DISTINCT substr(fecha,1,4) FROM consumo_diario ORDER BY 1")]

    def resumen_mensual(self, anio: int):
        """Una fila por mes con totales (base para las gráficas de la segunda mitad)."""
        return self.con.execute("""
            SELECT CAST(substr(fecha,6,2) AS INTEGER) AS mes,
                   COUNT(*) AS dias_registrados,
                   SUM(llovio) AS dias_lluviosos, SUM(precipitacion_mm) AS precipitacion_mm,
                   SUM(agua_recolectada_l) AS recolectada_l, SUM(lluvia_usada_l) AS lluvia_usada_l,
                   SUM(convencional_l) AS convencional_l, SUM(total_consumido_l) AS total_l,
                   SUM(agua_ahorrada_l) AS ahorrada_l
            FROM consumo_diario WHERE substr(fecha,1,4)=? GROUP BY mes ORDER BY mes""", (str(anio),)).fetchall()

    def resumen_anual(self, anio: int):
        return self.con.execute("""
            SELECT SUM(llovio) AS dias_lluviosos, SUM(precipitacion_mm) AS precipitacion_mm,
                   SUM(agua_recolectada_l) AS recolectada_l, SUM(lluvia_usada_l) AS lluvia_usada_l,
                   SUM(convencional_l) AS convencional_l, SUM(total_consumido_l) AS total_l,
                   SUM(agua_ahorrada_l) AS ahorrada_l
            FROM consumo_diario WHERE substr(fecha,1,4)=?""", (str(anio),)).fetchone()

    # ---------- Lecturas para el Dashboard ----------
    def ultimo_dia(self):
        """Último día registrado en consumo_diario (o None)."""
        return self.con.execute("SELECT * FROM consumo_diario ORDER BY fecha DESC LIMIT 1").fetchone()

    def ultimos_dias(self, n: int = 30):
        """Últimos n días registrados, en orden cronológico (para gráficos)."""
        filas = self.con.execute("SELECT * FROM consumo_diario ORDER BY fecha DESC LIMIT ?", (n,)).fetchall()
        return list(reversed(filas))

    def estado_sistemas(self):
        return self.con.execute("SELECT * FROM estado_sistemas WHERE id=1").fetchone()

    def ultima_activacion(self, fecha: str):
        return self.con.execute("SELECT * FROM activaciones WHERE fecha=? ORDER BY id DESC LIMIT 1",
                                (fecha,)).fetchone()

    def totales_mes(self, anio: int, mes: int):
        """Totales de un mes concreto (precipitación, consumo y ahorro)."""
        return self.con.execute("""
            SELECT COALESCE(SUM(precipitacion_mm),0) AS precipitacion_mm,
                   COALESCE(SUM(agua_recolectada_l),0) AS recolectada_l,
                   COALESCE(SUM(lluvia_usada_l),0) AS lluvia_usada_l,
                   COALESCE(SUM(convencional_l),0) AS convencional_l,
                   COALESCE(SUM(total_consumido_l),0) AS total_l,
                   COALESCE(SUM(agua_ahorrada_l),0) AS ahorrada_l
            FROM consumo_diario WHERE substr(fecha,1,7)=?""", (f"{anio:04d}-{mes:02d}",)).fetchone()

    # ---------- Lecturas para el Calendario (sección 6) ----------
    def dias_mes(self, anio: int, mes: int):
        """Todas las filas registradas de un mes (para pintar el calendario)."""
        return self.con.execute("SELECT * FROM consumo_diario WHERE substr(fecha,1,7)=? ORDER BY fecha",
                                (f"{anio:04d}-{mes:02d}",)).fetchall()

    def dias_anio(self, anio: int):
        """Todas las filas registradas de un año (para el mapa anual)."""
        return self.con.execute("SELECT * FROM consumo_diario WHERE substr(fecha,1,4)=? ORDER BY fecha",
                                (str(anio),)).fetchall()

    def mismo_dia_otros_anios(self, mes_dia: str):
        """Filas de consumo_diario con el mismo 'MM-DD' en cualquier año (comparación entre años)."""
        return self.con.execute("SELECT * FROM consumo_diario WHERE substr(fecha,6,5)=? ORDER BY fecha",
                                (mes_dia,)).fetchall()

    def prediccion_dia(self, fecha: str):
        """Última predicción guardada para ese día (o None). Es la que se guardó, no se inventa otra."""
        return self.con.execute("SELECT * FROM predicciones WHERE fecha=? ORDER BY id DESC LIMIT 1",
                                (fecha,)).fetchone()

    # ---------- Lecturas para Estadísticas y Comparación (sección 7) ----------
    def anio_tiene_estimacion(self, anio: int) -> bool:
        """True si ALGÚN día de ese año es simulado/estimado (no medido con sensores)."""
        fila = self.con.execute("SELECT MAX(es_estimacion) FROM consumo_diario WHERE substr(fecha,1,4)=?",
                                (str(anio),)).fetchone()
        return bool(fila[0]) if fila and fila[0] is not None else False
