"""Dashboard (equivale a interfaz/dashboard.py). Los datos los prepara interfaz/datos_dashboard.py."""
import streamlit as st
from matplotlib.figure import Figure

from interfaz import estilos as E
from interfaz import graficos
from interfaz.datos_dashboard import obtener_estado
from servicios import acciones
from interfaz_web import componentes as C

ANIOS_DEMO = (2023, 2024, 2025)


def _barra_acciones(cfg, repo, hoy):
    permitido = C.acciones_permitidas()
    c0, c1, c2, c3 = st.columns([1, 1, 1.2, 3])
    if c0.button("Actualizar", width="stretch"):
        st.rerun()
    if c1.button("Evaluar hoy", type="primary", width="stretch", disabled=not permitido):
        with st.spinner("Evaluando…"):
            _, msg = acciones.evaluar_hoy(cfg, repo, hoy)
        C.avisar("info", msg)
        st.rerun()
    with c2.popover("Simular año…", width="stretch", disabled=not permitido):
        st.caption("Los datos serán SIMULADOS, no son de SENAMHI.")
        anio = st.number_input("Año a simular", min_value=1990, max_value=2100, value=int(hoy[:4]) - 1, step=1)
        if st.button("Simular", key="btn_simular"):
            with st.spinner(f"Simulando {int(anio)}…"):
                msg = acciones.simular_anio(cfg, repo, int(anio))
            C.avisar("ok", msg)
            st.rerun()
    if not permitido:
        st.caption("Las acciones que modifican datos están protegidas: ingresa la clave en la barra lateral.")


def _vacio(cfg, repo):
    st.info("Aún no hay datos registrados. Usa «Evaluar hoy» (requiere un pronóstico en "
            "`datos/senamhi/pronostico.csv`) o «Simular año…».")
    if st.button("Cargar demostración (2023–2025 simulados)", disabled=not C.acciones_permitidas()):
        with st.spinner("Simulando 3 años… puede tardar unos segundos."):
            for a in ANIOS_DEMO:
                acciones.simular_anio(cfg, repo, a)
        C.avisar("ok", f"Demostración cargada: años {', '.join(map(str, ANIOS_DEMO))} (SIMULADOS).")
        st.rerun()


def mostrar(cfg, repo, hoy):
    st.title("Dashboard")
    C.mostrar_aviso()
    _barra_acciones(cfg, repo, hoy)

    e = obtener_estado(cfg, repo, hoy)
    marca = "ESTIMADO/SIMULADO" if e.es_estimacion else "MEDIDO"

    if e.fecha_registro is None:
        C.banner("Sin datos registrados.", "inactivo")
        _vacio(cfg, repo)
        return
    C.banner(f"Datos del {e.fecha_registro} · {marca} · Localidad: {cfg.localidad} · "
             f"Estación: {cfg.estacion_senamhi}", "alerta" if e.es_estimacion else "ok")

    # Fila 1: pronóstico SENAMHI de hoy
    a, b, c, d = st.columns(4)
    with a:
        if e.prob_lluvia is not None:
            sobre = e.prob_lluvia >= e.umbral and e.estado_pronostico == "VIGENTE"
            C.tarjeta("Probabilidad de lluvia (hoy)", f"{e.prob_lluvia:.0f} %", f"Umbral de activación: {e.umbral:.0f} %",
                      barra=e.prob_lluvia / 100, clave_barra="lluvia" if sobre else "inactivo")
        else:
            C.tarjeta("Probabilidad de lluvia (hoy)", "—", f"Sin dato · Umbral: {e.umbral:.0f} %", barra=0)
    with b:
        col = {"VIGENTE": "ok", "DESACTUALIZADO": "alerta"}.get(e.estado_pronostico, "error")
        C.tarjeta("Estado de la predicción", e.estado_pronostico,
                  f"Origen: {e.pron_origen}\nActualizado: {e.pron_actualizado}", clave_color=col)
    with c:
        C.tarjeta("Temperatura", "—" if e.temperatura_c is None else f"{e.temperatura_c:.1f} °C",
                  "Dato SENAMHI de hoy" if e.temperatura_c is not None else "No disponible")
    with d:
        C.tarjeta("Precipitación registrada", f"{e.precipitacion_mm:.1f} mm", f"Mes: {e.mes_mm:.1f} mm · {marca}",
                  clave_color="lluvia" if e.precipitacion_mm > 0 else None)

    # Fila 2: sistemas
    a, b, c, d = st.columns(4)
    with a:
        C.tarjeta_sistema("Riego 1", *E.estado_riego(e.riego1))
    with b:
        C.tarjeta_sistema("Riego 2", *E.estado_riego(e.riego2))
    with c:
        C.tarjeta_sistema("Succión de lluvia", *E.estado_succion(e.succion, e.recolectada_l))
    with d:
        if e.modo_lluvia is None:
            C.tarjeta("Modo lluvia", "—", e.motivo)
        else:
            C.tarjeta("Modo lluvia", "ACTIVO" if e.modo_lluvia else "INACTIVO", e.motivo,
                      clave_color="lluvia" if e.modo_lluvia else "inactivo")

    # Fila 3: agua
    frac = e.nivel_deposito_l / e.capacidad_l if e.capacidad_l else 0
    a, b, c, d = st.columns(4)
    with a:
        C.tarjeta("Agua en el depósito", f"{e.nivel_deposito_l:,.0f} L",
                  f"de {e.capacidad_l:,.0f} L · {frac * 100:.0f} % · estimado",
                  barra=frac, clave_barra="lluvia" if frac > 0.2 else "alerta")
    with b:
        C.tarjeta("Agua usada (aprox.)", f"{e.total_l:,.0f} L",
                  f"Convencional: {e.convencional_l:,.0f} L · Lluvia: {e.lluvia_usada_l:,.0f} L\n"
                  f"Mes: {e.mes_total_l:,.0f} L · Año: {e.anio_total_l:,.0f} L")
    with c:
        C.tarjeta("Agua ahorrada (aprox.)", f"{e.ahorrada_l:,.0f} L",
                  f"Mes: {e.mes_ahorrada_l:,.0f} L · Año: {e.anio_ahorrada_l:,.0f} L", clave_color="ahorro")
    with d:
        C.tarjeta("Agua recolectada (aprox.)", f"{e.recolectada_l:,.0f} L",
                  "Lluvia captada ese día (estimación por área de captación)")

    # Gráficos (los mismos de la app de escritorio)
    g1, g2 = st.columns([2, 1])
    fig1, fig2 = Figure(figsize=(6.4, 3.2), dpi=100), Figure(figsize=(3.4, 3.2), dpi=100)
    graficos.dibujar_serie(fig1, e.serie)
    graficos.dibujar_donut(fig2, e.anio_lluvia_usada_l, e.anio_convencional_l)
    g1.pyplot(fig1)
    g2.pyplot(fig2)
