"""
Vista Comparar años (sección 7): compara el año elegido con los demás años que tengan datos.
Solo dibuja; los datos los prepara interfaz/datos_estadisticas.py.

- Año base + casillas para elegir con qué años compararlo.
- Métrica y tipo de gráfico (barras o líneas) mes a mes.
- Totales anuales por año y resumen por año con la variación frente al año base.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_estadisticas as D

TEXTO_OSCURO = "#0b1220"


class VistaComparacion(ctk.CTkFrame):
    def __init__(self, master, cfg, repo):
        super().__init__(master, fg_color=E.FONDO)
        self.cfg, self.repo = cfg, repo
        self.anios = D.anios_con_datos(repo)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="Comparar años", font=E.fuente(24, True), text_color=E.TEXTO
                     ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(4, 6))
        if not self.anios:
            ctk.CTkLabel(self, text="Aún no hay datos registrados.\nEn el Dashboard pulsa «Simular año…» "
                                    "para dos o más años y vuelve aquí.",
                         font=E.fuente(14), text_color=E.TEXTO_SUAVE, justify="center"
                         ).place(relx=0.5, rely=0.45, anchor="center")
            return
        self.base = self.anios[-1]
        self.metricas = {f"{et} ({un})": clave for clave, (et, un) in D.METRICAS.items()}
        self.checks = {}
        self._panel_izquierdo()
        self._panel_graficos()
        self.refrescar()

    # ---------------- Construcción ----------------
    def _panel_izquierdo(self):
        izq = ctk.CTkFrame(self, fg_color=E.TARJETA, corner_radius=14, border_width=1, border_color=E.BORDE, width=300)
        izq.grid(row=1, column=0, sticky="nsew", padx=(6, 3), pady=(0, 6))
        izq.grid_propagate(False); izq.grid_rowconfigure(5, weight=1)

        def etiqueta(texto, fila):
            ctk.CTkLabel(izq, text=texto.upper(), font=E.fuente(10, True), text_color=E.TEXTO_SUAVE
                         ).grid(row=fila, column=0, sticky="w", padx=14, pady=(10, 2))

        etiqueta("Año base", 0)
        self.menu_base = ctk.CTkOptionMenu(izq, values=[str(a) for a in self.anios], fg_color=E.BORDE,
                                           button_color=E.BORDE, command=self._cambiar_base)
        self.menu_base.set(str(self.base)); self.menu_base.grid(row=1, column=0, sticky="ew", padx=14)
        etiqueta("Comparar con", 2)
        self.fr_checks = ctk.CTkFrame(izq, fg_color="transparent")
        self.fr_checks.grid(row=3, column=0, sticky="ew", padx=14)
        self.fr_ajustes = ctk.CTkFrame(izq, fg_color="transparent")
        self.fr_ajustes.grid(row=4, column=0, sticky="ew", padx=14, pady=(6, 0))
        ctk.CTkLabel(self.fr_ajustes, text="MÉTRICA MENSUAL", font=E.fuente(10, True), text_color=E.TEXTO_SUAVE
                     ).pack(anchor="w", pady=(4, 2))
        self.menu_metrica = ctk.CTkOptionMenu(self.fr_ajustes, values=list(self.metricas), fg_color=E.BORDE,
                                              button_color=E.BORDE, command=lambda _: self._dibujar())
        self.menu_metrica.set(next(iter(self.metricas))); self.menu_metrica.pack(fill="x")
        self.modo = ctk.CTkSegmentedButton(self.fr_ajustes, values=["Barras", "Líneas"], command=lambda _: self._dibujar())
        self.modo.set("Barras"); self.modo.pack(fill="x", pady=(8, 0))
        self.resumen = ctk.CTkScrollableFrame(izq, fg_color="transparent", label_text="Resumen por año",
                                              label_font=E.fuente(11, True), label_text_color=E.TEXTO_SUAVE,
                                              label_fg_color="transparent")
        self.resumen.grid(row=5, column=0, sticky="nsew", padx=6, pady=(10, 8))
        izq.grid_columnconfigure(0, weight=1)
        self._armar_checks()

    def _panel_graficos(self):
        der = ctk.CTkFrame(self, fg_color=E.TARJETA, corner_radius=14, border_width=1, border_color=E.BORDE)
        der.grid(row=1, column=1, sticky="nsew", padx=(3, 6), pady=(0, 6))
        der.grid_columnconfigure(0, weight=1); der.grid_rowconfigure((1, 2), weight=1)
        self.lbl_nota = ctk.CTkLabel(der, text="", font=E.fuente(11), text_color=E.TEXTO_SUAVE, justify="left",
                                     anchor="w", wraplength=820)
        self.lbl_nota.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 0))
        self.fig_mes, self.fig_tot = Figure(figsize=(7, 3), dpi=100), Figure(figsize=(7, 2.6), dpi=100)
        self.cv_mes = FigureCanvasTkAgg(self.fig_mes, master=der)
        self.cv_tot = FigureCanvasTkAgg(self.fig_tot, master=der)
        self.cv_mes.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=6, pady=(4, 0))
        self.cv_tot.get_tk_widget().grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 6))

    def _armar_checks(self):
        """Casillas de los demás años (todos marcados al inicio). Se rehace al cambiar el año base."""
        previas = {a: cb.get() for a, cb in self.checks.items()}
        for w in self.fr_checks.winfo_children():
            w.destroy()
        self.checks = {}
        otros = [a for a in self.anios if a != self.base]
        if not otros:
            ctk.CTkLabel(self.fr_checks, text="Solo hay un año con datos.\nSimula otro año en el Dashboard.",
                         font=E.fuente(11), text_color=E.COLORES["alerta"], justify="left").pack(anchor="w")
        for a in otros:
            cb = ctk.CTkCheckBox(self.fr_checks, text=str(a), command=self._dibujar, checkbox_width=18,
                                 checkbox_height=18, text_color=graficos.color_anio(self.anios.index(a)))
            if previas.get(a, 1):
                cb.select()
            cb.pack(anchor="w", pady=2)
            self.checks[a] = cb

    # ---------------- Actualización ----------------
    def refrescar(self):
        self._dibujar()

    def _cambiar_base(self, valor):
        self.base = int(valor)
        self._armar_checks()
        self._dibujar()

    def _series(self):
        elegidos = [self.base] + [a for a, cb in self.checks.items() if cb.get()]
        return D.series_para_comparar(self.repo, elegidos)

    def _dibujar(self):
        series = self._series()
        clave = self.metricas[self.menu_metrica.get()]
        etiqueta, unidad = D.METRICAS[clave]
        modo = "lineas" if self.modo.get() == "Líneas" else "barras"
        datos = [(s.anio, s.valores[clave], graficos.color_anio(self.anios.index(s.anio))) for s in series]
        graficos.dibujar_comparacion(self.fig_mes, f"{etiqueta} por mes", datos, unidad, modo)
        graficos.dibujar_totales_anios(self.fig_tot, [dict(anio=s.anio, **{k: s.total(k) for k in (
            "total_l", "convencional_l", "ahorrada_l", "recolectada_l")}) for s in series])
        self.cv_mes.draw_idle(); self.cv_tot.draw_idle()
        self._nota(series)
        self._resumen(series)

    def _nota(self, series):
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
        self.lbl_nota.configure(text="  ".join(partes))

    def _resumen(self, series):
        for w in self.resumen.winfo_children():
            w.destroy()
        base = next((s for s in series if s.anio == self.base), None)
        mejor = D.mejor_anio(series, "ahorrada_l")
        for s in series:
            color = graficos.color_anio(self.anios.index(s.anio))
            f = ctk.CTkFrame(self.resumen, fg_color=E.PANEL, corner_radius=10, border_width=1, border_color=E.BORDE)
            f.pack(fill="x", padx=2, pady=4)
            etiqueta = f"{s.anio}" + ("  · base" if s.anio == self.base else "") + \
                       ("  · más ahorro" if s.anio == mejor and len(series) > 1 else "")
            ctk.CTkLabel(f, text=etiqueta, font=E.fuente(13, True), text_color=color).pack(anchor="w", padx=10, pady=(6, 2))
            est = " (est.)" if s.hay_estimacion else ""
            filas = [("Total consumido", s.total("total_l"), "total_l"), ("Convencional", s.total("convencional_l"), "convencional_l"),
                     ("Recolectada", s.total("recolectada_l"), "recolectada_l"), ("Ahorrada", s.total("ahorrada_l"), "ahorrada_l")]
            for nombre, valor, clave in filas:
                fila = ctk.CTkFrame(f, fg_color="transparent"); fila.pack(fill="x", padx=10)
                ctk.CTkLabel(fila, text=nombre, font=E.fuente(11), text_color=E.TEXTO_SUAVE).pack(side="left")
                txt = f"{valor:,.0f} L{est}"
                if base is not None and s.anio != self.base:
                    v = D.variacion_pct(valor, base.total(clave))
                    txt += "" if v is None else f"  ({v:+.0f} %)"
                ctk.CTkLabel(fila, text=txt, font=E.fuente(11, True),
                             text_color=E.COLORES["ahorro"] if clave == "ahorrada_l" else E.TEXTO).pack(side="right")
            fila = ctk.CTkFrame(f, fg_color="transparent"); fila.pack(fill="x", padx=10, pady=(0, 6))
            ctk.CTkLabel(fila, text="Días lluviosos", font=E.fuente(11), text_color=E.TEXTO_SUAVE).pack(side="left")
            ctk.CTkLabel(fila, text=f"{s.total('dias_lluviosos'):.0f} · {s.total('precipitacion_mm'):,.0f} mm",
                         font=E.fuente(11, True), text_color=E.TEXTO).pack(side="right")
        if base is not None and len(series) > 1:
            ctk.CTkLabel(self.resumen, text="Entre paréntesis: cambio frente al año base.", font=E.fuente(10),
                         text_color=E.TEXTO_SUAVE).pack(anchor="w", padx=6)
