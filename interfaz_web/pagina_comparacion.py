"""Comparar años (equivale a interfaz/comparacion.py). Datos: interfaz/datos_estadisticas.py."""
import streamlit as st
from matplotlib.figure import Figure

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_estadisticas as D
from interfaz_web import componentes as C


def _notas(series):
    partes = []
    est = [str(s.anio) for s in series if s.hay_estimacion]
    if est:
        partes.append(f"Años con valores ESTIMADOS/SIMULADOS: {', '.join(est)} (no son mediciones).")
    inc = [f"{s.anio} ({D.texto_meses([i for i, _, _ in s.meses_incompletos])})" for s in series if s.meses_incompletos]
    if inc:
        partes.append("Meses incompletos: " + "; ".join(inc) + ". No son comparables con meses completos.")
    sin = [f"{s.anio} ({D.texto_meses(s.meses_sin_datos)})" for s in series if s.meses_sin_datos]
    if sin:
        partes.append("Meses sin registros (vacíos, no 0): " + "; ".join(sin) + ".")
    C.nota("  ".join(partes))


def _resumen_uno(s, base, mejor, hay_varios, base_anio):
    """Tarjeta de un año, con la variación frente al año base."""
    etiqueta = f"{s.anio}" + ("  · base" if s.anio == base_anio else "") + \
               ("  · más ahorro" if s.anio == mejor and hay_varios else "")
    est = " (est.)" if s.hay_estimacion else ""
    with st.container(border=True):
        st.markdown(f'<div style="font-weight:700;font-size:16px;color:{graficos.color_anio(s.anio_idx)}">'
                    f'{C.esc(etiqueta)}</div>', unsafe_allow_html=True)
        for nombre, clave in (("Total consumido", "total_l"), ("Convencional", "convencional_l"),
                              ("Recolectada", "recolectada_l"), ("Ahorrada", "ahorrada_l")):
            valor = s.total(clave)
            txt = f"{valor:,.0f} L{est}"
            if base is not None and s.anio != base_anio:
                v = D.variacion_pct(valor, base.total(clave))
                txt += "" if v is None else f"  ({v:+.0f} %)"
            C.fila(nombre, txt, E.COLORES["ahorro"] if clave == "ahorrada_l" else None)
        C.fila("Días lluviosos", f"{s.total('dias_lluviosos'):.0f} · {s.total('precipitacion_mm'):,.0f} mm")


def _resumen(series, base_anio):
    base = next((x for x in series if x.anio == base_anio), None)
    mejor = D.mejor_anio(series, "ahorrada_l")
    cols = st.columns(max(1, min(len(series), 4)))
    for i, s in enumerate(series):
        with cols[i % len(cols)]:
            _resumen_uno(s, base, mejor, len(series) > 1, base_anio)
    if base is not None and len(series) > 1:
        C.nota("Entre paréntesis: cambio frente al año base.")


def mostrar(cfg, repo, hoy):
    st.title("Comparar años")
    anios = D.anios_con_datos(repo)
    if not anios:
        C.sin_datos("Aún no hay datos registrados. En el Dashboard pulsa «Simular año…» para dos o más años "
                    "(o «Cargar demostración») y vuelve aquí.")
        return

    metricas = {f"{et} ({un})": clave for clave, (et, un) in D.METRICAS.items()}
    izq, der = st.columns([1, 3])
    with izq:
        base = st.selectbox("Año base", anios, index=len(anios) - 1)
        otros = [a for a in anios if a != base]
        if otros:
            elegidos = st.multiselect("Comparar con", otros, default=otros)
        else:
            elegidos = []
            st.warning("Solo hay un año con datos. Simula otro año en el Dashboard.")
        metrica = st.selectbox("Métrica mensual", list(metricas))
        modo = st.radio("Gráfico", ["Barras", "Líneas"], horizontal=True)

    series = D.series_para_comparar(repo, [base] + list(elegidos))
    for s in series:                         # índice fijo por año => mismo color que en la app de escritorio
        s.anio_idx = anios.index(s.anio)
    clave = metricas[metrica]
    etiqueta, unidad = D.METRICAS[clave]

    with der:
        _notas(series)
        fig1, fig2 = Figure(figsize=(7, 3), dpi=100), Figure(figsize=(7, 2.6), dpi=100)
        graficos.dibujar_comparacion(fig1, f"{etiqueta} por mes",
                                     [(s.anio, s.valores[clave], graficos.color_anio(s.anio_idx)) for s in series],
                                     unidad, "lineas" if modo == "Líneas" else "barras")
        graficos.dibujar_totales_anios(fig2, [dict(anio=s.anio, **{k: s.total(k) for k in (
            "total_l", "convencional_l", "ahorrada_l", "recolectada_l")}) for s in series])
        st.pyplot(fig1)
        st.pyplot(fig2)

    st.subheader("Resumen por año")
    _resumen(series, base)
