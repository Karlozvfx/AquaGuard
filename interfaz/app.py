"""
Ventana principal: barra lateral + área de contenido.
Las vistas se registran en VISTAS (nombre del menú -> clase de la vista).
"""
import customtkinter as ctk

from base_datos.conexion import conectar
from base_datos.operaciones import Repositorio
from config import Config
from interfaz import estilos as E
from interfaz.calendario import VistaCalendario
from interfaz.comparacion import VistaComparacion
from interfaz.dashboard import VistaDashboard
from interfaz.estadisticas import VistaEstadisticas


class App(ctk.CTk):
    VISTAS = {"Dashboard": VistaDashboard, "Calendario": VistaCalendario,
              "Estadísticas": VistaEstadisticas, "Comparar años": VistaComparacion}

    def __init__(self):
        E.aplicar_tema()
        super().__init__(fg_color=E.FONDO)
        self.title("Sistema Inteligente de Predicción Climática y Gestión del Agua")
        self.geometry("1280x820"); self.minsize(1100, 700)

        self.cfg = Config.cargar()
        self.repo = Repositorio(conectar(self.cfg.ruta(self.cfg.ruta_bd)))

        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)
        self._menu()
        self.contenedor = ctk.CTkFrame(self, fg_color=E.FONDO)
        self.contenedor.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        self.contenedor.grid_columnconfigure(0, weight=1); self.contenedor.grid_rowconfigure(0, weight=1)
        self.vista_actual = None
        self.mostrar("Dashboard")
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _menu(self):
        lateral = ctk.CTkFrame(self, width=210, fg_color=E.PANEL, corner_radius=0)
        lateral.grid(row=0, column=0, sticky="ns")
        lateral.grid_propagate(False)
        ctk.CTkLabel(lateral, text="💧 AquaGuard", font=E.fuente(20, True), text_color=E.COLORES["lluvia"]
                     ).pack(padx=18, pady=(22, 2), anchor="w")
        ctk.CTkLabel(lateral, text="Modo simulación\n(sin hardware conectado)", font=E.fuente(11),
                     text_color=E.TEXTO_SUAVE, justify="left").pack(padx=18, pady=(0, 20), anchor="w")
        self.botones = {}
        for nombre in self.VISTAS:
            b = ctk.CTkButton(lateral, text=nombre, anchor="w", height=40, fg_color="transparent",
                              hover_color=E.BORDE, text_color=E.TEXTO, font=E.fuente(14),
                              command=lambda n=nombre: self.mostrar(n))
            b.pack(fill="x", padx=12, pady=3)
            self.botones[nombre] = b

    def mostrar(self, nombre):
        if self.vista_actual is not None:
            self.vista_actual.destroy()
        self.vista_actual = self.VISTAS[nombre](self.contenedor, self.cfg, self.repo)
        self.vista_actual.grid(row=0, column=0, sticky="nsew")
        for n, b in self.botones.items():
            b.configure(fg_color=E.BORDE if n == nombre else "transparent")

    def _cerrar(self):
        self.repo.con.close()
        self.destroy()


def iniciar():
    App().mainloop()
