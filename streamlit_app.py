"""
AquaGuard — versión web (Streamlit).

  Local:   streamlit run streamlit_app.py
  Nube:    sube el repositorio a GitHub y despliega este archivo en Streamlit Community Cloud.

La lógica (clima/, servicios/, sistemas/, base_datos/) y los gráficos son los mismos de la app de
escritorio; aquí solo cambia la interfaz.
"""
import streamlit as st

st.set_page_config(page_title="AquaGuard · Gestión del agua", page_icon="💧", layout="wide")

from interfaz_web import componentes as C                                   # noqa: E402
from interfaz_web import pagina_calendario, pagina_comparacion            # noqa: E402
from interfaz_web import pagina_dashboard, pagina_estadisticas            # noqa: E402

PAGINAS = {
    "Dashboard": pagina_dashboard,
    "Calendario": pagina_calendario,
    "Estadísticas": pagina_estadisticas,
    "Comparar años": pagina_comparacion,
}


def _acceso_admin():
    """Si hay ADMIN_PASSWORD en los secretos, pide la clave para poder modificar datos."""
    try:
        clave = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        clave = ""
    if not clave:
        return
    if st.session_state.get("admin_ok"):
        st.sidebar.success("Modo administrador")
        return
    ingreso = st.sidebar.text_input("Clave de administrador", type="password",
                                    help="Necesaria para evaluar hoy, simular años o cargar la demostración.")
    if ingreso:
        if ingreso == clave:
            st.session_state["admin_ok"] = True
            st.rerun()
        st.sidebar.error("Clave incorrecta")


def main():
    C.inyectar_css()
    st.sidebar.markdown("## 💧 AquaGuard")
    st.sidebar.caption("Modo simulación (sin hardware conectado)")
    pagina = st.sidebar.radio("Menú", list(PAGINAS), label_visibility="collapsed")
    _acceso_admin()
    st.sidebar.divider()
    st.sidebar.caption("Los datos simulados se marcan siempre como ESTIMADO/SIMULADO; "
                       "un día sin registro se muestra como «sin registro», no como 0.")

    with C.abrir_repo() as (cfg, repo):
        PAGINAS[pagina].mostrar(cfg, repo, C.hoy_lima())


main()
