"""
Vista Dashboard (sección 5): panel principal de información.
Solo dibuja; los datos los prepara interfaz/datos_dashboard.py.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import estilos as E
from interfaz import graficos
from interfaz.datos_dashboard import obtener_estado
from servicios import acciones

REFRESCO_MS = 60_000   # el panel se actualiza solo cada minuto


class Tarjeta(ctk.CTkFrame):
    """Tarjeta con título, valor grande y una línea de detalle."""

    def __init__(self, master, titulo):
        super().__init__(master, fg_color=E.TARJETA, corner_radius=14, border_width=1, border_color=E.BORDE)
        ctk.CTkLabel(self, text=titulo.upper(), font=E.fuente(11, True), text_color=E.TEXTO_SUAVE
                     ).pack(anchor="w", padx=16, pady=(12, 0))
        self.valor = ctk.CTkLabel(self, text="—", font=E.fuente(28, True), text_color=E.TEXTO)
        self.valor.pack(anchor="w", padx=16, pady=(2, 0))
        self.detalle = ctk.CTkLabel(self, text="", font=E.fuente(11), text_color=E.TEXTO_SUAVE,
                                    justify="left", wraplength=230)
        self.detalle.pack(anchor="w", padx=16, pady=(0, 6))
        self.barra = None

    def con_barra(self):
        self.barra = ctk.CTkProgressBar(self, height=10, corner_radius=6, fg_color=E.BORDE)
        self.barra.set(0)
        self.barra.pack(fill="x", padx=16, pady=(0, 14))
        return self

    def poner(self, valor, detalle="", color=None, barra=None, color_barra=None):
        self.valor.configure(text=valor, text_color=E.COLORES.get(color, E.TEXTO) if color else E.TEXTO)
        self.detalle.configure(text=detalle)
        if self.barra is not None and barra is not None:
            self.barra.set(max(0.0, min(1.0, barra)))
            self.barra.configure(progress_color=E.COLORES.get(color_barra or "lluvia"))


class TarjetaSistema(ctk.CTkFrame):
    """Estado de un sistema (riego 1, riego 2, succión) con indicador de color."""

    def __init__(self, master, nombre):
        super().__init__(master, fg_color=E.TARJETA, corner_radius=14, border_width=1, border_color=E.BORDE)
        ctk.CTkLabel(self, text=nombre.upper(), font=E.fuente(11, True), text_color=E.TEXTO_SUAVE
                     ).pack(anchor="w", padx=16, pady=(12, 6))
        self.insignia = ctk.CTkLabel(self, text="SIN DATOS", font=E.fuente(14, True), corner_radius=10,
                                     fg_color=E.COLORES["inactivo"], text_color="#0b1220", height=34)
        self.insignia.pack(fill="x", padx=16, pady=(0, 14))

    def poner(self, clave_color, texto):
        self.insignia.configure(text=texto, fg_color=E.COLORES[clave_color])


class VistaDashboard(ctk.CTkScrollableFrame):
    def __init__(self, master, cfg, repo):
        super().__init__(master, fg_color=E.FONDO)
        self.cfg, self.repo = cfg, repo
        for c in range(4):
            self.grid_columnconfigure(c, weight=1, uniform="col")
        self._construir()
        self.refrescar()
        self._programar()

    # ---------------- Construcción ----------------
    def _construir(self):
        # Encabezado + botones
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(4, 6))
        ctk.CTkLabel(cab, text="Dashboard", font=E.fuente(24, True), text_color=E.TEXTO).pack(side="left")
        ctk.CTkButton(cab, text="Simular año…", width=120, fg_color=E.BORDE, hover_color="#33466b",
                      command=self._simular).pack(side="right", padx=(8, 0))
        ctk.CTkButton(cab, text="Evaluar hoy", width=120, command=self._evaluar_hoy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(cab, text="Actualizar", width=100, fg_color=E.BORDE, hover_color="#33466b",
                      command=self.refrescar).pack(side="right")

        # Banner de origen de datos (siempre visible: transparencia sobre qué es real y qué estimado)
        self.banner = ctk.CTkLabel(self, text="", font=E.fuente(12, True), corner_radius=10, height=34,
                                   anchor="w", padx=14, text_color="#0b1220", fg_color=E.COLORES["inactivo"])
        self.banner.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 10))

        # Fila 1: pronóstico
        self.t_prob = Tarjeta(self, "Probabilidad de lluvia (hoy)").con_barra()
        self.t_estado = Tarjeta(self, "Estado de la predicción")
        self.t_temp = Tarjeta(self, "Temperatura")
        self.t_lluvia = Tarjeta(self, "Precipitación registrada")
        for i, t in enumerate((self.t_prob, self.t_estado, self.t_temp, self.t_lluvia)):
            t.grid(row=2, column=i, sticky="nsew", padx=6, pady=6)

        # Fila 2: sistemas
        self.s_riego1 = TarjetaSistema(self, "Riego 1")
        self.s_riego2 = TarjetaSistema(self, "Riego 2")
        self.s_succion = TarjetaSistema(self, "Succión de lluvia")
        self.t_modo = Tarjeta(self, "Modo lluvia")
        for i, t in enumerate((self.s_riego1, self.s_riego2, self.s_succion, self.t_modo)):
            t.grid(row=3, column=i, sticky="nsew", padx=6, pady=6)

        # Fila 3: agua
        self.t_deposito = Tarjeta(self, "Agua en el depósito").con_barra()
        self.t_usada = Tarjeta(self, "Agua usada (aprox.)")
        self.t_ahorrada = Tarjeta(self, "Agua ahorrada (aprox.)")
        self.t_recolectada = Tarjeta(self, "Agua recolectada (aprox.)")
        for i, t in enumerate((self.t_deposito, self.t_usada, self.t_ahorrada, self.t_recolectada)):
            t.grid(row=4, column=i, sticky="nsew", padx=6, pady=6)

        # Fila 4: gráficos
        self.fig1, self.fig2 = Figure(figsize=(6.4, 3.2), dpi=100), Figure(figsize=(3.4, 3.2), dpi=100)
        self.c1 = FigureCanvasTkAgg(self.fig1, master=self)
        self.c2 = FigureCanvasTkAgg(self.fig2, master=self)
        self.c1.get_tk_widget().grid(row=5, column=0, columnspan=3, sticky="nsew", padx=6, pady=6)
        self.c2.get_tk_widget().grid(row=5, column=3, sticky="nsew", padx=6, pady=6)

    # ---------------- Actualización ----------------
    def refrescar(self):
        e = obtener_estado(self.cfg, self.repo)
        marca = "ESTIMADO/SIMULADO" if e.es_estimacion else "MEDIDO"

        # Banner
        if e.fecha_registro is None:
            self.banner.configure(text="  Sin datos registrados. Usa «Evaluar hoy» o «Simular año…».",
                                  fg_color=E.COLORES["inactivo"])
        else:
            col = E.COLORES["alerta"] if e.es_estimacion else E.COLORES["ok"]
            self.banner.configure(text=f"  Datos del {e.fecha_registro} · {marca} · "
                                       f"Localidad: {self.cfg.localidad} · Estación: {self.cfg.estacion_senamhi}",
                                  fg_color=col)

        # Pronóstico SENAMHI de hoy
        if e.prob_lluvia is not None:
            sobre = e.prob_lluvia >= e.umbral and e.estado_pronostico == "VIGENTE"
            self.t_prob.poner(f"{e.prob_lluvia:.0f} %", f"Umbral de activación: {e.umbral:.0f} %",
                              barra=e.prob_lluvia / 100, color_barra="lluvia" if sobre else "inactivo")
        else:
            self.t_prob.poner("—", f"Sin dato · Umbral: {e.umbral:.0f} %", barra=0)

        col_est = {"VIGENTE": "ok", "DESACTUALIZADO": "alerta"}.get(e.estado_pronostico, "error")
        self.t_estado.poner(e.estado_pronostico,
                            f"Origen: {e.pron_origen}\nActualizado: {e.pron_actualizado}", color=col_est)
        self.t_temp.poner("—" if e.temperatura_c is None else f"{e.temperatura_c:.1f} °C",
                          "Dato SENAMHI de hoy" if e.temperatura_c is not None else "No disponible")
        self.t_lluvia.poner(f"{e.precipitacion_mm:.1f} mm", f"Mes: {e.mes_mm:.1f} mm · {marca}",
                            color="lluvia" if e.precipitacion_mm > 0 else None)

        # Sistemas
        self.s_riego1.poner(*E.estado_riego(e.riego1))
        self.s_riego2.poner(*E.estado_riego(e.riego2))
        self.s_succion.poner(*E.estado_succion(e.succion, e.recolectada_l))
        if e.modo_lluvia is None:
            self.t_modo.poner("—", e.motivo)
        else:
            self.t_modo.poner("ACTIVO" if e.modo_lluvia else "INACTIVO", e.motivo,
                              color="lluvia" if e.modo_lluvia else "inactivo")

        # Agua
        frac = e.nivel_deposito_l / e.capacidad_l if e.capacidad_l else 0
        self.t_deposito.poner(f"{e.nivel_deposito_l:,.0f} L", f"de {e.capacidad_l:,.0f} L · {frac * 100:.0f} % · estimado",
                              barra=frac, color_barra="lluvia" if frac > 0.2 else "alerta")
        self.t_usada.poner(f"{e.total_l:,.0f} L", f"Convencional: {e.convencional_l:,.0f} L · Lluvia: {e.lluvia_usada_l:,.0f} L\n"
                                                  f"Mes: {e.mes_total_l:,.0f} L · Año: {e.anio_total_l:,.0f} L")
        self.t_ahorrada.poner(f"{e.ahorrada_l:,.0f} L", f"Mes: {e.mes_ahorrada_l:,.0f} L · Año: {e.anio_ahorrada_l:,.0f} L",
                              color="ahorro")
        self.t_recolectada.poner(f"{e.recolectada_l:,.0f} L", "Lluvia captada ese día (estimación por área de captación)")

        # Gráficos
        graficos.dibujar_serie(self.fig1, e.serie)
        graficos.dibujar_donut(self.fig2, e.anio_lluvia_usada_l, e.anio_convencional_l)
        self.c1.draw_idle(); self.c2.draw_idle()

    def _programar(self):
        self._job = self.after(REFRESCO_MS, self._tick)

    def _tick(self):
        self.refrescar()
        self._programar()

    # ---------------- Acciones de los botones ----------------
    def _aviso(self, titulo, texto):
        v = ctk.CTkToplevel(self)
        v.title(titulo); v.geometry("440x170"); v.attributes("-topmost", True)
        ctk.CTkLabel(v, text=texto, wraplength=400, font=E.fuente(13)).pack(expand=True, padx=20, pady=(20, 8))
        ctk.CTkButton(v, text="Aceptar", width=100, command=v.destroy).pack(pady=(0, 16))

    def _evaluar_hoy(self):
        _, msg = acciones.evaluar_hoy(self.cfg, self.repo)
        self.refrescar()
        self._aviso("Evaluar hoy", msg)

    def _simular(self):
        dlg = ctk.CTkInputDialog(text="Año a simular (los datos serán SIMULADOS, no de SENAMHI):",
                                 title="Simular año")
        txt = dlg.get_input()
        if not txt:
            return
        try:
            anio = int(txt)
            if not 1990 <= anio <= 2100:
                raise ValueError
        except ValueError:
            self._aviso("Año no válido", "Escribe un año entre 1990 y 2100, por ejemplo 2025.")
            return
        msg = acciones.simular_anio(self.cfg, self.repo, anio)
        self.refrescar()
        self._aviso("Simulación", msg)
