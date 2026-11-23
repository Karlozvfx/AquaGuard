"""Estadísticas (equivale a interfaz/estadisticas.py). Datos: interfaz/datos_estadisticas.py."""
import pandas as pd
import streamlit as st
from matplotlib.figure import Figure

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_estadisticas as D
from interfaz_web import componentes as C

PESTANAS = ("Ahorro vs convencional", "Lluvia", "Recolección", "Tabla mensual")


def _nota(s):
    partes = []
    if s.hay_estimacion:
        partes.append("Los valores incluyen datos ESTIMADOS/SIMULADOS (no son mediciones de sensores ni de SENAMHI).")
    if s.meses_sin_datos:
        partes.append(f"Meses sin registros: {D.texto_meses(s.meses_sin_datos)} (se muestran vacíos, no como 0).")
    if s.meses_incompletos:
        det = ", ".join(f"{D.MESES_CORTOS[i]} {d}/{t} días" for i, d, t in s.meses_incompletos)
        partes.append(f"Meses incompletos: {det}; sus totales no son comparables con meses completos.")
    C.nota("  ".join(partes))


def _tabla(s):
    cols = [("Días reg.", "dias_registrados"), ("Días lluv.", "dias_lluviosos"), ("mm", "precipitacion_mm"),
            ("Recolect. L", "recolectada_l"), ("Lluvia usada L", "lluvia_usada_l"),
            ("Convenc. L", "convencional_l"), ("Total L", "total_l"), ("Ahorro L", "ahorrada_l")]
    filas = []
    for i in range(12):
        fila = {"Mes": D.MESES_LARGOS[i], "Días reg.": str(s.dias_registrados[i])}
        for nombre, k in cols[1:]:
            v = s.valores[k][i]
            fila[nombre] = "—" if v is None else (f"{v:,.1f}" if k == "precipitacion_mm" else f"{v:,.0f}")
        filas.append(fila)
    r = D.resumen_anual(s)
    filas.append({"Mes": "AÑO", "Días reg.": str(r["dias_registrados"]), "Días lluv.": str(r["dias_lluviosos"]),
                  "mm": f"{r['precipitacion_mm']:,.1f}", "Recolect. L": f"{r['recolectada_l']:,.0f}",
                  "Lluvia usada L": f"{r['lluvia_usada_l']:,.0f}", "Convenc. L": f"{r['convencional_l']:,.0f}",
                  "Total L": f"{r['total_l']:,.0f}", "Ahorro L": f"{r['ahorrada_l']:,.0f}"})
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")


def mostrar(cfg, repo, hoy):
    st.title("Estadísticas")
    anios = D.anios_con_datos(repo)
    if not anios:
        C.sin_datos("Aún no hay datos registrados. En el Dashboard pulsa «Simular año…» "
                    "(por ejemplo 2024 y 2025) o «Cargar demostración», y vuelve aquí.")
        return

    anio = st.selectbox("Año", anios, index=len(anios) - 1)
    s = D.serie_anual(repo, anio)
    r = D.resumen_anual(s)
    est = " (est.)" if s.hay_estimacion else ""
    pct = "—" if r["pct_lluvia"] is None else f"{r['pct_lluvia']:.0f} % del riego con lluvia"

    datos = [("Agua usada en el año", f"{r['total_l']:,.0f} L", f"total consumido{est}", None),
             ("Convencional", f"{r['convencional_l']:,.0f} L", f"agua de red/pozo{est}", "convencional"),
             ("Ahorrada", f"{r['ahorrada_l']:,.0f} L", pct + est, "ahorro"),
             ("Recolectada", f"{r['recolectada_l']:,.0f} L", f"agua de lluvia captada{est}", "lluvia"),
             ("Días lluviosos", f"{r['dias_lluviosos']}", f"de {r['dias_registrados']} días registrados", None),
             ("Precipitación", f"{r['precipitacion_mm']:,.1f} mm", f"acumulada{est}", "lluvia")]
    for col, (t, v, sub, c) in zip(st.columns(6), datos):
        with col:
            C.tarjeta(t, v, sub, clave_color=c, chico=True)

    rk = D.rankings_principales(s)
    defs = [("ahorro", "Mes que más ahorró", "L ahorrados", "ahorro"),
            ("convencional", "Más agua convencional", "L convencionales", "convencional"),
            ("dias_lluviosos", "Más días lluviosos", "días con lluvia", "lluvia"),
            ("recolectada", "Mayor recolección", "L recolectados", "lluvia")]
    for col, (clave, titulo, unidad, c) in zip(st.columns(4), defs):
        with col:
            if rk[clave] is None:
                C.tarjeta(titulo, "Sin datos", "ningún mes con valores mayores a 0", clave_color="inactivo", chico=True)
            else:
                C.tarjeta(titulo, rk[clave].nombre(), f"{rk[clave].valor:,.0f} {unidad}{est}", clave_color=c, chico=True)
    _nota(s)

    v, K = s.valores, E.COLORES
    sufijo = " · valores estimados" if s.hay_estimacion else ""
    tabs = st.tabs(list(PESTANAS))
    with tabs[0]:
        fig = Figure(figsize=(8, 3.4), dpi=100)
        graficos.dibujar_mensual(fig, f"Agua ahorrada vs convencional por mes · {anio}{sufijo}",
                                 barras=[(v["ahorrada_l"], "Ahorrada (lluvia)", K["ahorro"]),
                                         (v["convencional_l"], "Convencional", K["convencional"])],
                                 lineas=[(v["total_l"], "Total consumido", E.TEXTO)],
                                 etq_barras="litros", eje_comun=True)
        st.pyplot(fig)
    with tabs[1]:
        fig = Figure(figsize=(8, 3.4), dpi=100)
        graficos.dibujar_mensual(fig, f"Días lluviosos y precipitación por mes · {anio}{sufijo}",
                                 barras=[(v["dias_lluviosos"], "Días lluviosos", K["lluvia"])],
                                 lineas=[(v["precipitacion_mm"], "Precipitación (mm)", K["alerta"])],
                                 etq_barras="días", etq_lineas="mm")
        st.pyplot(fig)
    with tabs[2]:
        fig = Figure(figsize=(8, 3.4), dpi=100)
        graficos.dibujar_mensual(fig, f"Recolección y uso del agua de lluvia · {anio}{sufijo}",
                                 lineas=[(v["recolectada_l"], "Recolectada", K["lluvia"]),
                                         (v["lluvia_usada_l"], "Lluvia usada en riego", K["ahorro"]),
                                         (v["convencional_l"], "Convencional", K["convencional"])],
                                 etq_lineas="litros")
        st.pyplot(fig)
    with tabs[3]:
        _tabla(s)
