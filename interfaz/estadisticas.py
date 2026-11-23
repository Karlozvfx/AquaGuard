"""
Vista Estadísticas (sección 7): comparación mensual y anual del consumo de agua.
Solo dibuja; los datos los prepara interfaz/datos_estadisticas.py.

- Tarjetas con los totales de TODO el año (agua usada, ahorrada, recolectada...).
- Tarjetas de ranking: mes que más ahorró, más convencional, más días lluviosos, más recolectó.
- Gráficos de barras y líneas por mes (pestañas) y tabla mensual.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_estadisticas as D

TEXTO_OSCURO = "#0b1220"
PESTANAS = ("Ahorro vs convencional", "Lluvia", "Recolección", "Tabla mensual")


class VistaEstadisticas(ctk.CTkFrame):
    def __init__(self, master, cfg, repo):
        super().__init__(master, fg_color=E.FONDO)
        self.cfg, self.repo = cfg, repo
        self.anios = D.anios_con_datos(repo)
        self.serie = None
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Estadísticas", font=E.fuente(24, True), text_color=E.TEXTO
                     ).grid(row=0, column=0, sticky="w", padx=6, pady=(4, 6))
        if not self.anios:
            ctk.CTkLabel(self, text="Aún no hay datos registrados.\nEn el Dashboard pulsa «Simular año…» "
                                    "(por ejemplo 2024 y 2025) y vuelve aquí.",
                         font=E.fuente(14), text_color=E.TEXTO_SUAVE, justify="center"
                         ).place(relx=0.5, rely=0.45, anchor="center")
            return
        self.grid_rowconfigure(4, weight=1)
        self.anio = self.anios[-1]
        self._cabecera()
        self.fr_anual = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_anual.grid(row=1, column=0, sticky="ew", padx=2)
        self.fr_rank = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_rank.grid(row=2, column=0, sticky="ew", padx=2, pady=(4, 0))
        self.lbl_nota = ctk.CTkLabel(self, text="", font=E.fuente(11), text_color=E.TEXTO_SUAVE,
                                     justify="left", anchor="w", wraplength=900)
        self.lbl_nota.grid(row=3, column=0, sticky="ew", padx=8, pady=(6, 2))
        self._pestanas()
        self.refrescar()

    # ---------------- Construcción ----------------
    def _cabecera(self):
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="e", padx=6, pady=(4, 6))
        ctk.CTkLabel(cab, text="Año:", font=E.fuente(12), text_color=E.TEXTO_SUAVE).pack(side="left", padx=(0, 4))
        self.menu_anio = ctk.CTkOptionMenu(cab, values=[str(a) for a in self.anios], width=90,
                                           fg_color=E.BORDE, button_color=E.BORDE, command=self._cambiar_anio)
        self.menu_anio.set(str(self.anio))
        self.menu_anio.pack(side="left")

    def _pestanas(self):
        self.tabs = ctk.CTkTabview(self, fg_color=E.TARJETA, corner_radius=14, border_width=1,
                                   border_color=E.BORDE, command=self._dibujar_activa)
        self.tabs.grid(row=4, column=0, sticky="nsew", padx=6, pady=(4, 6))
        self.figs, self.canvas = {}, {}
        for nombre in PESTANAS[:3]:
            tab = self.tabs.add(nombre)
            fig = Figure(figsize=(8, 3.4), dpi=100)
            cv = FigureCanvasTkAgg(fig, master=tab)
            cv.get_tk_widget().pack(fill="both", expand=True)
            self.figs[nombre], self.canvas[nombre] = fig, cv
        self.tab_tabla = ctk.CTkScrollableFrame(self.tabs.add(PESTANAS[3]), fg_color="transparent")
        self.tab_tabla.pack(fill="both", expand=True)

    # ---------------- Actualización ----------------
    def refrescar(self):
        self.serie = D.serie_anual(self.repo, self.anio)
        self._tarjetas_anuales()
        self._tarjetas_ranking()
        self._nota()
        self._dibujar_activa()

    def _cambiar_anio(self, valor):
        self.anio = int(valor)
        self.refrescar()

    def _tarjeta(self, padre, col, titulo, valor, sub, color):
        t = ctk.CTkFrame(padre, fg_color=E.TARJETA, corner_radius=12, border_width=1, border_color=E.BORDE)
        t.grid(row=0, column=col, sticky="nsew", padx=4, pady=3)
        padre.grid_columnconfigure(col, weight=1, uniform="tarjeta")
        ctk.CTkLabel(t, text=titulo.upper(), font=E.fuente(10, True), text_color=E.TEXTO_SUAVE
                     ).pack(anchor="w", padx=12, pady=(8, 0))
        ctk.CTkLabel(t, text=valor, font=E.fuente(18, True), text_color=color).pack(anchor="w", padx=12)
        ctk.CTkLabel(t, text=sub, font=E.fuente(10), text_color=E.TEXTO_SUAVE, wraplength=150, justify="left"
                     ).pack(anchor="w", padx=12, pady=(0, 8))

    def _limpiar(self, marco):
        for w in marco.winfo_children():
            w.destroy()

    def _tarjetas_anuales(self):
        self._limpiar(self.fr_anual)
        r = D.resumen_anual(self.serie)
        est = " (est.)" if self.serie.hay_estimacion else ""
        pct = "—" if r["pct_lluvia"] is None else f"{r['pct_lluvia']:.0f} % del riego con lluvia"
        datos = [
            ("Agua usada en el año", f"{r['total_l']:,.0f} L", f"total consumido{est}", E.TEXTO),
            ("Convencional", f"{r['convencional_l']:,.0f} L", f"agua de red/pozo{est}", E.COLORES["convencional"]),
            ("Ahorrada", f"{r['ahorrada_l']:,.0f} L", pct + est, E.COLORES["ahorro"]),
            ("Recolectada", f"{r['recolectada_l']:,.0f} L", f"agua de lluvia captada{est}", E.COLORES["lluvia"]),
            ("Días lluviosos", f"{r['dias_lluviosos']}", f"de {r['dias_registrados']} días registrados", E.TEXTO),
            ("Precipitación", f"{r['precipitacion_mm']:,.1f} mm", f"acumulada{est}", E.COLORES["lluvia"]),
        ]
        for i, d in enumerate(datos):
            self._tarjeta(self.fr_anual, i, *d)

    def _tarjetas_ranking(self):
        self._limpiar(self.fr_rank)
        rk = D.rankings_principales(self.serie)
        est = " (est.)" if self.serie.hay_estimacion else ""
        defs = [
            ("ahorro", "Mes que más ahorró", "L ahorrados", E.COLORES["ahorro"], "{:,.0f}"),
            ("convencional", "Más agua convencional", "L convencionales", E.COLORES["convencional"], "{:,.0f}"),
            ("dias_lluviosos", "Más días lluviosos", "días con lluvia", E.COLORES["lluvia"], "{:,.0f}"),
            ("recolectada", "Mayor recolección", "L recolectados", E.COLORES["lluvia"], "{:,.0f}"),
        ]
        for i, (clave, titulo, unidad, color, fmt) in enumerate(defs):
            r = rk[clave]
            if r is None:
                self._tarjeta(self.fr_rank, i, titulo, "Sin datos", "ningún mes con valores mayores a 0",
                              E.COLORES["inactivo"])
            else:
                self._tarjeta(self.fr_rank, i, titulo, r.nombre(), f"{fmt.format(r.valor)} {unidad}{est}", color)

    def _nota(self):
        s, partes = self.serie, []
        if s.hay_estimacion:
            partes.append("Los valores incluyen datos ESTIMADOS/SIMULADOS (no son mediciones de sensores ni de SENAMHI).")
        if s.meses_sin_datos:
            partes.append(f"Meses sin registros: {D.texto_meses(s.meses_sin_datos)} (se muestran vacíos, no como 0).")
        if s.meses_incompletos:
            det = ", ".join(f"{D.MESES_CORTOS[i]} {d}/{t} días" for i, d, t in s.meses_incompletos)
            partes.append(f"Meses incompletos: {det}; sus totales no son comparables con meses completos.")
        self.lbl_nota.configure(text="  ".join(partes))

    # ---------------- Gráficos ----------------
    def _dibujar_activa(self):
        actual = self.tabs.get()
        v, C = self.serie.valores, E.COLORES
        est = " · valores estimados" if self.serie.hay_estimacion else ""
        if actual == PESTANAS[0]:
            graficos.dibujar_mensual(
                self.figs[actual], f"Agua ahorrada vs convencional por mes · {self.anio}{est}",
                barras=[(v["ahorrada_l"], "Ahorrada (lluvia)", C["ahorro"]),
                        (v["convencional_l"], "Convencional", C["convencional"])],
                lineas=[(v["total_l"], "Total consumido", E.TEXTO)], etq_barras="litros", eje_comun=True)
        elif actual == PESTANAS[1]:
            graficos.dibujar_mensual(
                self.figs[actual], f"Días lluviosos y precipitación por mes · {self.anio}{est}",
                barras=[(v["dias_lluviosos"], "Días lluviosos", C["lluvia"])],
                lineas=[(v["precipitacion_mm"], "Precipitación (mm)", C["alerta"])],
                etq_barras="días", etq_lineas="mm")
        elif actual == PESTANAS[2]:
            graficos.dibujar_mensual(
                self.figs[actual], f"Recolección y uso del agua de lluvia · {self.anio}{est}",
                lineas=[(v["recolectada_l"], "Recolectada", C["lluvia"]),
                        (v["lluvia_usada_l"], "Lluvia usada en riego", C["ahorro"]),
                        (v["convencional_l"], "Convencional", C["convencional"])], etq_lineas="litros")
        else:
            self._dibujar_tabla()
            return
        self.canvas[actual].draw_idle()

    def _dibujar_tabla(self):
        self._limpiar(self.tab_tabla)
        cols = [("Mes", "mes"), ("Días reg.", "dias_registrados"), ("Días lluv.", "dias_lluviosos"),
                ("mm", "precipitacion_mm"), ("Recolect. L", "recolectada_l"), ("Lluvia usada L", "lluvia_usada_l"),
                ("Convenc. L", "convencional_l"), ("Total L", "total_l"), ("Ahorro L", "ahorrada_l")]
        for c, (nombre, _) in enumerate(cols):
            self.tab_tabla.grid_columnconfigure(c, weight=1)
            ctk.CTkLabel(self.tab_tabla, text=nombre, font=E.fuente(11, True), text_color=E.TEXTO_SUAVE
                         ).grid(row=0, column=c, padx=6, pady=(2, 6), sticky="e" if c else "w")
        s = self.serie
        for i in range(12):
            sin = s.dias_registrados[i] == 0
            celdas = [D.MESES_LARGOS[i], str(s.dias_registrados[i])] + [
                "—" if s.valores[k][i] is None else (f"{s.valores[k][i]:,.1f}" if k == "precipitacion_mm"
                                                    else f"{s.valores[k][i]:,.0f}")
                for _, k in cols[2:]]
            for c, txt in enumerate(celdas):
                ctk.CTkLabel(self.tab_tabla, text=txt, font=E.fuente(12),
                             text_color=E.TEXTO_SUAVE if sin else (E.COLORES["ahorro"] if c == 8 else E.TEXTO)
                             ).grid(row=i + 1, column=c, padx=6, pady=1, sticky="e" if c else "w")
        r = D.resumen_anual(s)
        tot = ["AÑO", str(r["dias_registrados"]), str(r["dias_lluviosos"]), f"{r['precipitacion_mm']:,.1f}",
               f"{r['recolectada_l']:,.0f}", f"{r['lluvia_usada_l']:,.0f}", f"{r['convencional_l']:,.0f}",
               f"{r['total_l']:,.0f}", f"{r['ahorrada_l']:,.0f}"]
        for c, txt in enumerate(tot):
            ctk.CTkLabel(self.tab_tabla, text=txt, font=E.fuente(12, True), text_color=E.TEXTO
                         ).grid(row=14, column=c, padx=6, pady=(8, 2), sticky="e" if c else "w")
