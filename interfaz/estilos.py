"""Estilos compartidos de la interfaz: colores, fuentes y estados (todo en Python)."""
# customtkinter se importa solo dentro de las funciones que lo necesitan,
# así colores y estados se pueden usar (y probar) sin abrir ventanas.

# ---- Paleta (tema oscuro) ----
FONDO = "#0b1220"
PANEL = "#111a2e"
TARJETA = "#16213a"
BORDE = "#243352"
TEXTO = "#e6edf7"
TEXTO_SUAVE = "#8da2c0"

COLORES = {
    "ok": "#22c55e",        # verde: funcionando / vigente
    "lluvia": "#38bdf8",    # celeste: agua de lluvia
    "alerta": "#f59e0b",    # ámbar: respaldo / desactualizado
    "inactivo": "#64748b",  # gris: sin datos / apagado
    "error": "#ef4444",     # rojo: problema
    "ahorro": "#34d399",    # verde agua: ahorro
    "convencional": "#f97316",  # naranja: agua convencional
}

FUENTE = "Segoe UI"


def aplicar_tema():
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


def fuente(tam=13, negrita=False):
    import customtkinter as ctk
    return ctk.CTkFont(family=FUENTE, size=tam, weight="bold" if negrita else "normal")


def estado_riego(texto):
    """Convierte el texto guardado por el motor en (clave_color, etiqueta corta)."""
    if not texto:
        return "inactivo", "SIN DATOS"
    t = texto.upper()
    if "RESPALDO" in t:
        return "alerta", "RESPALDO CONVENCIONAL" if t.startswith("CONVENCIONAL") else "RESPALDO MIXTO"
    if t.startswith("ANULADO"):
        return "lluvia", "ANULADO · USA LLUVIA"
    if t.startswith("LLUVIA"):
        return "lluvia", "AGUA DE LLUVIA"
    if t.startswith("MIXTO"):
        return "alerta", "MIXTO"
    if t.startswith("CONVENCIONAL"):
        return "ok", "CONVENCIONAL"
    return "inactivo", texto


def estado_succion(texto, recolectada_l=0.0):
    if not texto:
        return "inactivo", "SIN DATOS"
    if texto == "ARMADO":
        return ("lluvia", "CAPTANDO LLUVIA") if recolectada_l > 0 else ("alerta", "ARMADO · ESPERA LLUVIA")
    return "inactivo", "APAGADO"
