"""
Calendario (equivale a interfaz/calendario.py). Los datos los prepara interfaz/datos_calendario.py.

Cada día es un botón de Streamlit coloreado con CSS (clase st-key-<clave>), así se puede hacer clic
en él igual que en la versión de escritorio.
"""
from datetime import date

import streamlit as st
from matplotlib.figure import Figure

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_calendario as D
from interfaz_web import componentes as C

SIN_DATO = ("SIN_REGISTRO", "FUTURO")


# ---------------- Estado y callbacks ----------------
def _iniciar_estado(repo, hoy):
    if "cal_sel" in st.session_state:
        return
    ult = repo.ultimo_dia()
    sel = ult["fecha"] if ult is not None else hoy
    st.session_state.update(cal_sel=sel, cal_anio=int(sel[:4]), cal_mes=int(sel[5:7]), cal_anio_sel=int(sel[:4]))


def _seleccionar(fecha):
    st.session_state.cal_sel = fecha


def _mover(delta):
    ss = st.session_state
    ss.cal_anio, ss.cal_mes = D.mover_mes(ss.cal_anio, ss.cal_mes, delta)
    ss.cal_sel = D.ajustar_fecha(ss.cal_sel, ss.cal_anio, ss.cal_mes)
    ss.cal_anio_sel = ss.cal_anio


def _cambiar_anio():
    ss = st.session_state
    ss.cal_anio = int(ss.cal_anio_sel)
    ss.cal_sel = D.ajustar_fecha(ss.cal_sel, ss.cal_anio, ss.cal_mes)


def _ir_a_hoy(hoy):
    ss = st.session_state
    ss.cal_sel, ss.cal_anio, ss.cal_mes = hoy, int(hoy[:4]), int(hoy[5:7])
    ss.cal_anio_sel = ss.cal_anio


# ---------------- Dibujo ----------------
def _clave(fecha):
    return "dia_" + fecha.replace("-", "_")


def _css_celdas(semanas, sel, hoy):
    reglas = ["div.st-key-cal button{min-height:54px;padding:4px 2px;border-radius:8px;}"
              "div.st-key-cal button p{white-space:pre-line;line-height:1.25;font-weight:700;font-size:13px;}"]
    for semana in semanas:
        for info in semana:
            if info is None:
                continue
            clave_color, _ = D.CATEGORIAS[info.categoria]
            sin = info.categoria in SIN_DATO
            fondo = E.PANEL if sin else E.COLORES[clave_color]
            txt = E.TEXTO_SUAVE if sin else C.TEXTO_OSCURO
            if info.fecha == sel:
                borde = f"3px solid {E.TEXTO}"
            elif info.fecha == hoy:
                borde = f"1px solid {E.COLORES['alerta']}"
            else:
                borde = f"1px solid {E.BORDE}" if sin else "0"
            k = _clave(info.fecha)
            reglas.append(f"div.st-key-{k} button{{background:{fondo}!important;border:{borde}!important;}}"
                          f"div.st-key-{k} button p{{color:{txt}!important;}}")
    st.markdown("<style>" + "".join(reglas) + "</style>", unsafe_allow_html=True)


def _cuadricula(repo, anio, mes, sel, hoy):
    datos = D.construir_mes(repo, anio, mes, hoy)
    _css_celdas(datos["semanas"], sel, hoy)
    with st.container(key="cal"):
        for col, nombre in zip(st.columns(7), D.DIAS_SEMANA):
            col.markdown(f'<div style="text-align:center;color:{E.TEXTO_SUAVE};font-weight:700;font-size:12px">'
                         f'{nombre}</div>', unsafe_allow_html=True)
        for semana in datos["semanas"]:
            for col, info in zip(st.columns(7), semana):
                if info is None:
                    continue
                etiqueta = f"{info.dia}"
                if info.registrado and info.precipitacion_mm is not None:
                    etiqueta += f"\n{info.precipitacion_mm:.1f} mm"
                col.button(etiqueta, key=_clave(info.fecha), on_click=_seleccionar, args=(info.fecha,),
                           width="stretch")

    r = datos["resumen"]
    if r["dias_registrados"] == 0:
        C.nota("Este mes no tiene días registrados.")
    else:
        extra = " · incluye valores ESTIMADOS/SIMULADOS" if r["hay_estimacion"] else ""
        C.nota(f"Mes: {r['dias_registrados']} días registrados · {r['dias_lluviosos']} lluviosos · "
               f"{r['precipitacion_mm']:.1f} mm · recolectada {r['recolectada_l']:,.0f} L · "
               f"usada {r['total_l']:,.0f} L · ahorrada {r['ahorrada_l']:,.0f} L{extra}")


def _leyenda():
    items = []
    for clave in ("LLUVIA", "ALMACENADA", "MIXTO", "CONVENCIONAL", "SIN_REGISTRO"):
        color, texto = D.CATEGORIAS[clave]
        fondo = E.BORDE if clave == "SIN_REGISTRO" else E.COLORES[color]
        items.append(f'<span style="margin-right:14px;white-space:nowrap"><span class="ag-leyenda" '
                     f'style="background:{fondo}"></span>{C.esc(texto)}</span>')
    st.markdown(f'<div class="ag-nota" style="line-height:1.9">{"".join(items)}</div>', unsafe_allow_html=True)


def _detalle(repo, sel, hoy):
    d = D.info_dia(repo, sel, hoy)
    clave_color, desc = D.CATEGORIAS[d.categoria]
    with st.container(border=True):
        st.subheader(d.titulo_largo())
        sin = d.categoria in SIN_DATO
        C.banner(desc.upper(), "inactivo" if sin else clave_color)

        if d.registrado:
            est = " (est.)" if d.es_estimacion else ""
            origen = "ESTIMADO / SIMULADO (no es una medición)" if d.es_estimacion else "MEDIDO con sensores"
            st.markdown(f'<div class="ag-nota" style="color:{E.COLORES["alerta" if d.es_estimacion else "ok"]}">'
                        f'Origen de los datos: {origen}</div>', unsafe_allow_html=True)
            C.fila("¿Llovió?", "Sí" if d.llovio else "No")
            C.fila("Precipitación", "No disponible" if d.precipitacion_mm is None else f"{d.precipitacion_mm:.1f} mm{est}")
            C.fila("Agua recolectada", f"{d.recolectada_l:,.0f} L{est}")
            C.fila("Lluvia usada en riego", f"{d.lluvia_usada_l:,.0f} L{est}")
            C.fila("Agua convencional", f"{d.convencional_l:,.0f} L{est}")
            C.fila("Total consumido", f"{d.total_l:,.0f} L{est}")
            C.fila("Agua ahorrada", f"{d.ahorrada_l:,.0f} L{est}", E.COLORES["ahorro"])
            if d.nivel_deposito_l is not None:
                C.fila("Depósito al cierre", f"{d.nivel_deposito_l:,.0f} L{est}")
            C.fila_insignia("Riego 1", *E.estado_riego(d.riego1))
            C.fila_insignia("Riego 2", *E.estado_riego(d.riego2))
            C.fila("Modo lluvia", "Activo" if d.modo_lluvia else "Inactivo", E.COLORES["lluvia"] if d.modo_lluvia else None)
            if d.motivo:
                C.nota(f"Motivo: {d.motivo}")
        elif d.categoria == "FUTURO":
            C.nota("Esta fecha aún no llega: no hay registro.")
        else:
            C.nota("No hay registro de este día en la base de datos. (No se inventan valores para días sin registro.)")

        C.seccion("Pronóstico guardado")
        if d.pron_origen is None:
            C.fila("Pronóstico", "Sin pronóstico guardado")
        else:
            C.fila("Prob. de lluvia", "—" if d.pron_prob is None else f"{d.pron_prob:.0f} %")
            C.fila("Origen", d.pron_origen)
            C.fila("Actualizado", d.pron_actualizado or "—")
            C.fila("Vigente al usarse", "Sí" if d.pron_vigente else "No (no se usó para activar)")

        C.seccion("Mismo día en otros años")
        otros = D.mismo_dia_otros_anios(repo, sel)
        if not otros:
            C.nota("No hay otros años con datos para esta fecha.")
        for o in otros:
            mm = "s/d" if o.precipitacion_mm is None else f"{o.precipitacion_mm:.1f} mm"
            C.fila(o.fecha[:4], f"{mm} · ahorro {o.ahorrada_l:,.0f} L{' (est.)' if o.es_estimacion else ''}")


def mostrar(cfg, repo, hoy):
    st.title("Calendario")
    _iniciar_estado(repo, hoy)
    ss = st.session_state

    c_mes, c_anio, c_prev, c_next, c_hoy = st.columns([3, 1.4, 0.6, 0.6, 0.9], vertical_alignment="bottom")
    c_mes.subheader(f"{D.MESES_ES[ss.cal_mes - 1]} {ss.cal_anio}")
    c_anio.selectbox("Año", D.anios_con_datos(repo, extra=ss.cal_anio), key="cal_anio_sel",
                     on_change=_cambiar_anio)
    c_prev.button("‹", on_click=_mover, args=(-1,), width="stretch", help="Mes anterior")
    c_next.button("›", on_click=_mover, args=(1,), width="stretch", help="Mes siguiente")
    c_hoy.button("Hoy", on_click=_ir_a_hoy, args=(hoy,), width="stretch")

    izq, der = st.columns([3, 2])
    with izq:
        _cuadricula(repo, ss.cal_anio, ss.cal_mes, ss.cal_sel, hoy)
        _leyenda()
        fig = Figure(figsize=(6.4, 2.6), dpi=100)
        graficos.dibujar_mapa_anio(fig, ss.cal_anio, D.mm_por_dia_anio(repo, ss.cal_anio), ss.cal_sel)
        st.pyplot(fig)
        C.nota("El recuadro blanco marca el día elegido. Para cambiar de día usa la cuadrícula del mes.")
    with der:
        _detalle(repo, ss.cal_sel, hoy)
