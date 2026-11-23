"""
Piezas visuales reutilizables de la versión web (Streamlit).
Usan la misma paleta que la app de escritorio (interfaz/estilos.py).
"""
import html
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from base_datos.conexion import conectar
from base_datos.operaciones import Repositorio
from config import Config
from interfaz import estilos as E

ZONA = ZoneInfo("America/Lima")
TEXTO_OSCURO = "#0b1220"

CSS = f"""
<style>
.ag-tarjeta {{background:{E.TARJETA}; border:1px solid {E.BORDE}; border-radius:14px;
              padding:12px 16px 12px 16px; margin-bottom:12px; height:calc(100% - 12px);}}
.ag-titulo {{font-size:11px; font-weight:700; letter-spacing:.04em; color:{E.TEXTO_SUAVE}; text-transform:uppercase;}}
.ag-valor  {{font-size:28px; font-weight:700; line-height:1.25; color:{E.TEXTO};}}
.ag-valor.chico {{font-size:19px;}}
.ag-detalle {{font-size:12px; color:{E.TEXTO_SUAVE}; white-space:pre-line;}}
.ag-barra  {{height:10px; border-radius:6px; background:{E.BORDE}; margin-top:8px; overflow:hidden;}}
.ag-barra > div {{height:100%; border-radius:6px;}}
.ag-insignia {{display:block; text-align:center; font-weight:700; font-size:14px; border-radius:10px;
               padding:7px 10px; color:{TEXTO_OSCURO};}}
.ag-banner {{font-weight:700; font-size:13px; border-radius:10px; padding:8px 14px; margin-bottom:12px;
             color:{TEXTO_OSCURO};}}
.ag-fila {{display:flex; justify-content:space-between; gap:12px; padding:3px 0; font-size:14px;}}
.ag-fila span:first-child {{color:{E.TEXTO_SUAVE};}}
.ag-fila span:last-child {{font-weight:700; text-align:right;}}
.ag-seccion {{font-size:11px; font-weight:700; letter-spacing:.04em; color:{E.TEXTO_SUAVE};
              text-transform:uppercase; margin:14px 0 4px 0;}}
.ag-nota {{font-size:12px; color:{E.TEXTO_SUAVE};}}
.ag-leyenda {{display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:6px;
              vertical-align:middle;}}
</style>
"""


def esc(x) -> str:
    return html.escape(str(x))


def inyectar_css():
    st.markdown(CSS, unsafe_allow_html=True)


def hoy_lima() -> str:
    """Fecha de hoy en Lima (el servidor web suele estar en UTC)."""
    return datetime.now(ZONA).date().isoformat()


@contextmanager
def abrir_repo():
    """
    Conexión SQLite nueva por ejecución. Streamlit corre cada sesión en un hilo distinto y
    SQLite no permite compartir una conexión entre hilos, por eso no se guarda en caché.
    """
    cfg = Config.cargar()
    repo = Repositorio(conectar(cfg.ruta(cfg.ruta_bd)))
    try:
        yield cfg, repo
    finally:
        repo.con.close()


def color(clave: str) -> str:
    return E.COLORES[clave]


def tarjeta(titulo, valor, detalle="", clave_color=None, barra=None, clave_barra="lluvia", chico=False):
    """Tarjeta con título, valor grande, detalle y barra de progreso opcional (0 a 1)."""
    c = f"color:{color(clave_color)};" if clave_color else ""
    b = ""
    if barra is not None:
        pct = max(0.0, min(1.0, barra)) * 100
        b = f'<div class="ag-barra"><div style="width:{pct:.0f}%; background:{color(clave_barra)};"></div></div>'
    st.markdown(
        f'<div class="ag-tarjeta"><div class="ag-titulo">{esc(titulo)}</div>'
        f'<div class="ag-valor{" chico" if chico else ""}" style="{c}">{esc(valor)}</div>'
        f'<div class="ag-detalle">{esc(detalle)}</div>{b}</div>', unsafe_allow_html=True)


def tarjeta_sistema(nombre, clave_color, texto):
    st.markdown(
        f'<div class="ag-tarjeta"><div class="ag-titulo" style="margin-bottom:8px">{esc(nombre)}</div>'
        f'<span class="ag-insignia" style="background:{color(clave_color)}">{esc(texto)}</span></div>',
        unsafe_allow_html=True)


def banner(texto, clave_color):
    st.markdown(f'<div class="ag-banner" style="background:{color(clave_color)}">{esc(texto)}</div>',
                unsafe_allow_html=True)


def fila(nombre, valor, color_hex=None):
    c = f' style="color:{color_hex}"' if color_hex else ""
    st.markdown(f'<div class="ag-fila"><span>{esc(nombre)}</span><span{c}>{esc(valor)}</span></div>',
                unsafe_allow_html=True)


def fila_insignia(nombre, clave_color, texto):
    st.markdown(
        f'<div class="ag-fila"><span>{esc(nombre)}</span>'
        f'<span class="ag-insignia" style="background:{color(clave_color)}; font-size:12px; padding:3px 10px">'
        f'{esc(texto)}</span></div>', unsafe_allow_html=True)


def seccion(texto):
    st.markdown(f'<div class="ag-seccion">{esc(texto)}</div>', unsafe_allow_html=True)


def nota(texto):
    if texto:
        st.markdown(f'<div class="ag-nota">{esc(texto)}</div>', unsafe_allow_html=True)


def sin_datos(mensaje):
    st.info(mensaje)


# ---------------- Acciones que escriben en la base de datos ----------------
def acciones_permitidas() -> bool:
    """
    Si defines ADMIN_PASSWORD en los secretos de Streamlit, los botones que modifican la base
    (Evaluar hoy, Simular año, Cargar demostración) piden esa clave. Sin secreto = abiertos (uso local).
    """
    try:
        clave = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:           # no hay archivo de secretos
        clave = ""
    if not clave:
        return True
    return st.session_state.get("admin_ok", False)


def avisar(tipo: str, texto: str):
    """Guarda un mensaje para mostrarlo tras el st.rerun() siguiente."""
    st.session_state["aviso"] = (tipo, texto)


def mostrar_aviso():
    aviso = st.session_state.pop("aviso", None)
    if aviso:
        {"ok": st.success, "error": st.error}.get(aviso[0], st.info)(aviso[1])
