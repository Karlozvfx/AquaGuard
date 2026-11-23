"""
Vista Calendario (sección 6): consulta de todos los días del año.
Solo dibuja; los datos los prepara interfaz/datos_calendario.py.

- Cuadrícula del mes con color por tipo de día y los mm de lluvia.
- Selector de año (solo años con datos) y botones de mes anterior/siguiente.
- Mapa del año completo (12 x 31) con clic para elegir un día.
- Panel de detalle del día elegido + mismo día en otros años.
"""
from datetime import date

import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from interfaz import estilos as E
from interfaz import graficos
from interfaz import datos_calendario as D

TEXTO_OSCURO = "#0b1220"


class VistaCalendario(ctk.CTkFrame):
    def __init__(self, master, cfg, repo):
        super().__init__(master, fg_color=E.FONDO)
        self.cfg, self.repo = cfg, repo
        self.hoy = date.today().isoformat()

        # Punto de partida: el último día registrado (si hay) o hoy
        ult = repo.ultimo_dia()
        self.sel = ult["fecha"] if ult is not None else self.hoy
        self.anio, self.mes = int(self.sel[:4]), int(self.sel[5:7])

        self.grid_columnconfigure(0, weight=3); self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)
        self._construir()
        self.refrescar()

    # ---------------- Construcción ----------------
    def _construir(self):
        # Encabezado: título, año, navegación de mes
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 6))
        ctk.CTkLabel(cab, text="Calendario", font=E.fuente(24, True), text_color=E.TEXTO).pack(side="left")

        ctk.CTkButton(cab, text="Hoy", width=60, fg_color=E.BORDE, hover_color="#33466b",
                      command=self._ir_a_hoy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(cab, text="›", width=36, fg_color=E.BORDE, hover_color="#33466b",
                      command=lambda: self._mover(1)).pack(side="right", padx=(4, 0))
        self.lbl_mes = ctk.CTkLabel(cab, text="", width=150, font=E.fuente(15, True), text_color=E.TEXTO)
        self.lbl_mes.pack(side="right")
        ctk.CTkButton(cab, text="‹", width=36, fg_color=E.BORDE, hover_color="#33466b",
                      command=lambda: self._mover(-1)).pack(side="right", padx=(0, 4))
        self.menu_anio = ctk.CTkOptionMenu(cab, values=["—"], width=90, fg_color=E.BORDE,
                                           button_color=E.BORDE, command=self._cambiar_anio)
        self.menu_anio.pack(side="right", padx=(0, 12))
        ctk.CTkLabel(cab, text="Año:", font=E.fuente(12), text_color=E.TEXTO_SUAVE).pack(side="right", padx=(0, 4))

        # Columna izquierda: cuadrícula + resumen + leyenda + mapa del año
        izq = ctk.CTkFrame(self, fg_color="transparent")
        izq.grid(row=1, column=0, sticky="nsew", padx=(6, 3), pady=(0, 6))
        izq.grid_columnconfigure(0, weight=1)
        self.cuadricula = ctk.CTkFrame(izq, fg_color=E.TARJETA, corner_radius=14, border_width=1,
                                       border_color=E.BORDE)
        self.cuadricula.grid(row=0, column=0, sticky="ew")
        for c in range(7):
            self.cuadricula.grid_columnconfigure(c, weight=1, uniform="dia")

        self.lbl_resumen = ctk.CTkLabel(izq, text="", font=E.fuente(11), text_color=E.TEXTO_SUAVE,
                                        justify="left", anchor="w", wraplength=640)
        self.lbl_resumen.grid(row=1, column=0, sticky="ew", padx=6, pady=(6, 2))
        self._leyenda(izq).grid(row=2, column=0, sticky="ew", pady=(0, 6))

        self.fig = Figure(figsize=(6.4, 2.6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=izq)
        self.canvas.get_tk_widget().grid(row=3, column=0, sticky="nsew")
        self.canvas.mpl_connect("button_press_event", self._clic_mapa)
        izq.grid_rowconfigure(3, weight=1)

        # Columna derecha: detalle del día
        self.detalle = ctk.CTkScrollableFrame(self, fg_color=E.TARJETA, corner_radius=14, border_width=1,
                                              border_color=E.BORDE)
        self.detalle.grid(row=1, column=1, sticky="nsew", padx=(3, 6), pady=(0, 6))

    def _leyenda(self, master):
        f = ctk.CTkFrame(master, fg_color="transparent")
        for i, clave in enumerate(("LLUVIA", "ALMACENADA", "MIXTO", "CONVENCIONAL", "SIN_REGISTRO")):
            color, texto = D.CATEGORIAS[clave]
            ctk.CTkLabel(f, text="  ", width=14, height=14, corner_radius=4,
                         fg_color=E.COLORES[color] if clave != "SIN_REGISTRO" else E.BORDE
                         ).grid(row=i // 2, column=(i % 2) * 2, padx=(6, 4), pady=1, sticky="w")
            ctk.CTkLabel(f, text=texto, font=E.fuente(10), text_color=E.TEXTO_SUAVE
                         ).grid(row=i // 2, column=(i % 2) * 2 + 1, padx=(0, 14), sticky="w")
        return f

    # ---------------- Actualización ----------------
    def refrescar(self):
        # Selector de año: solo años con datos (+ el que se está viendo)
        anios = D.anios_con_datos(self.repo, extra=self.anio)
        self.menu_anio.configure(values=[str(a) for a in anios])
        self.menu_anio.set(str(self.anio))
        self.lbl_mes.configure(text=f"{D.MESES_ES[self.mes - 1]} {self.anio}")

        self._dibujar_cuadricula()
        self._dibujar_mapa()
        self._dibujar_detalle()

    def _dibujar_cuadricula(self):
        for w in self.cuadricula.winfo_children():
            w.destroy()
        for c, nombre in enumerate(D.DIAS_SEMANA):
            ctk.CTkLabel(self.cuadricula, text=nombre, font=E.fuente(11, True), text_color=E.TEXTO_SUAVE
                         ).grid(row=0, column=c, pady=(8, 2))

        datos = D.construir_mes(self.repo, self.anio, self.mes, self.hoy)
        for r, semana in enumerate(datos["semanas"], start=1):
            for c, info in enumerate(semana):
                if info is None:
                    continue
                self._celda(info).grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
        ctk.CTkLabel(self.cuadricula, text="", height=4).grid(row=len(datos["semanas"]) + 1, column=0)

        r = datos["resumen"]
        if r["dias_registrados"] == 0:
            self.lbl_resumen.configure(text="Este mes no tiene días registrados.")
        else:
            nota = " · incluye valores ESTIMADOS/SIMULADOS" if r["hay_estimacion"] else ""
            self.lbl_resumen.configure(
                text=f"Mes: {r['dias_registrados']} días registrados · {r['dias_lluviosos']} lluviosos · "
                     f"{r['precipitacion_mm']:.1f} mm · recolectada {r['recolectada_l']:,.0f} L · "
                     f"usada {r['total_l']:,.0f} L · ahorrada {r['ahorrada_l']:,.0f} L{nota}")

    def _celda(self, info):
        color_clave, _ = D.CATEGORIAS[info.categoria]
        sin_dato = info.categoria in ("SIN_REGISTRO", "FUTURO")
        fondo = E.PANEL if sin_dato else E.COLORES[color_clave]
        texto = f"{info.dia}"
        if info.registrado and info.precipitacion_mm is not None:
            texto += f"\n{info.precipitacion_mm:.1f} mm"
        elegido = info.fecha == self.sel
        return ctk.CTkButton(
            self.cuadricula, text=texto, height=52, corner_radius=8, font=E.fuente(12, True),
            fg_color=fondo, hover_color=E.BORDE if sin_dato else fondo,
            text_color=E.TEXTO_SUAVE if sin_dato else TEXTO_OSCURO,
            border_width=3 if elegido else (1 if info.fecha == self.hoy else 0),
            border_color=E.TEXTO if elegido else E.COLORES["alerta"],
            command=lambda f=info.fecha: self._seleccionar(f))

    def _dibujar_mapa(self):
        graficos.dibujar_mapa_anio(self.fig, self.anio, D.mm_por_dia_anio(self.repo, self.anio), self.sel)
        self.canvas.draw_idle()

    def _dibujar_detalle(self):
        for w in self.detalle.winfo_children():
            w.destroy()
        d = D.info_dia(self.repo, self.sel, self.hoy)
        color_clave, desc = D.CATEGORIAS[d.categoria]

        ctk.CTkLabel(self.detalle, text=d.titulo_largo(), font=E.fuente(16, True), text_color=E.TEXTO,
                     wraplength=330, justify="left", anchor="w").pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(self.detalle, text=desc.upper(), font=E.fuente(11, True), corner_radius=8, height=26,
                     fg_color=E.BORDE if d.categoria in ("SIN_REGISTRO", "FUTURO") else E.COLORES[color_clave],
                     text_color=E.TEXTO if d.categoria in ("SIN_REGISTRO", "FUTURO") else TEXTO_OSCURO
                     ).pack(fill="x", padx=14, pady=(0, 8))

        if d.registrado:
            marca = "ESTIMADO / SIMULADO (no es una medición)" if d.es_estimacion else "MEDIDO con sensores"
            ctk.CTkLabel(self.detalle, text=f"Origen de los datos: {marca}", font=E.fuente(11),
                         text_color=E.COLORES["alerta"] if d.es_estimacion else E.COLORES["ok"],
                         wraplength=330, justify="left", anchor="w").pack(fill="x", padx=14, pady=(0, 6))
            est = " (est.)" if d.es_estimacion else ""
            mm = "No disponible" if d.precipitacion_mm is None else f"{d.precipitacion_mm:.1f} mm{est}"
            self._fila("¿Llovió?", "Sí" if d.llovio else "No")
            self._fila("Precipitación", mm)
            self._fila("Agua recolectada", f"{d.recolectada_l:,.0f} L{est}")
            self._fila("Lluvia usada en riego", f"{d.lluvia_usada_l:,.0f} L{est}")
            self._fila("Agua convencional", f"{d.convencional_l:,.0f} L{est}")
            self._fila("Total consumido", f"{d.total_l:,.0f} L{est}")
            self._fila("Agua ahorrada", f"{d.ahorrada_l:,.0f} L{est}", E.COLORES["ahorro"])
            if d.nivel_deposito_l is not None:
                self._fila("Depósito al cierre", f"{d.nivel_deposito_l:,.0f} L{est}")
            self._insignia("Riego 1", d.riego1)
            self._insignia("Riego 2", d.riego2)
            self._fila("Modo lluvia", "Activo" if d.modo_lluvia else "Inactivo",
                       E.COLORES["lluvia"] if d.modo_lluvia else None)
            if d.motivo:
                ctk.CTkLabel(self.detalle, text=f"Motivo: {d.motivo}", font=E.fuente(11), text_color=E.TEXTO_SUAVE,
                             wraplength=330, justify="left", anchor="w").pack(fill="x", padx=14, pady=(2, 4))
        elif d.categoria == "FUTURO":
            ctk.CTkLabel(self.detalle, text="Esta fecha aún no llega: no hay registro.", font=E.fuente(12),
                         text_color=E.TEXTO_SUAVE).pack(anchor="w", padx=14, pady=4)
        else:
            ctk.CTkLabel(self.detalle, text="No hay registro de este día en la base de datos.\n"
                                            "(No se inventan valores para días sin registro.)",
                         font=E.fuente(12), text_color=E.TEXTO_SUAVE, justify="left", wraplength=330
                         ).pack(anchor="w", padx=14, pady=4)

        # Pronóstico guardado de ese día
        self._titulo("Pronóstico guardado")
        if d.pron_origen is None:
            self._fila("Pronóstico", "Sin pronóstico guardado")
        else:
            prob = "—" if d.pron_prob is None else f"{d.pron_prob:.0f} %"
            self._fila("Prob. de lluvia", prob)
            self._fila("Origen", d.pron_origen)
            self._fila("Actualizado", d.pron_actualizado or "—")
            self._fila("Vigente al usarse", "Sí" if d.pron_vigente else "No (no se usó para activar)")

        # Mismo día en otros años
        otros = D.mismo_dia_otros_anios(self.repo, self.sel)
        self._titulo("Mismo día en otros años")
        if not otros:
            ctk.CTkLabel(self.detalle, text="No hay otros años con datos para esta fecha.", font=E.fuente(11),
                         text_color=E.TEXTO_SUAVE).pack(anchor="w", padx=14, pady=(0, 8))
        for o in otros:
            mm = "s/d" if o.precipitacion_mm is None else f"{o.precipitacion_mm:.1f} mm"
            etq = " (est.)" if o.es_estimacion else ""
            self._fila(o.fecha[:4], f"{mm} · ahorro {o.ahorrada_l:,.0f} L{etq}")

    # ---------------- Piezas del panel de detalle ----------------
    def _titulo(self, texto):
        ctk.CTkLabel(self.detalle, text=texto.upper(), font=E.fuente(11, True), text_color=E.TEXTO_SUAVE
                     ).pack(anchor="w", padx=14, pady=(14, 4))

    def _fila(self, nombre, valor, color=None):
        f = ctk.CTkFrame(self.detalle, fg_color="transparent")
        f.pack(fill="x", padx=14, pady=1)
        ctk.CTkLabel(f, text=nombre, font=E.fuente(12), text_color=E.TEXTO_SUAVE).pack(side="left")
        ctk.CTkLabel(f, text=valor, font=E.fuente(12, True), text_color=color or E.TEXTO).pack(side="right")

    def _insignia(self, nombre, texto_estado):
        clave, etiqueta = E.estado_riego(texto_estado)
        f = ctk.CTkFrame(self.detalle, fg_color="transparent")
        f.pack(fill="x", padx=14, pady=2)
        ctk.CTkLabel(f, text=nombre, font=E.fuente(12), text_color=E.TEXTO_SUAVE).pack(side="left")
        ctk.CTkLabel(f, text=etiqueta, font=E.fuente(11, True), corner_radius=8, height=24,
                     fg_color=E.COLORES[clave], text_color=TEXTO_OSCURO, padx=10).pack(side="right")

    # ---------------- Interacción ----------------
    def _seleccionar(self, fecha):
        self.sel = fecha
        self.refrescar()

    def _mover(self, delta):
        self.anio, self.mes = D.mover_mes(self.anio, self.mes, delta)
        self.sel = D.ajustar_fecha(self.sel, self.anio, self.mes)
        self.refrescar()

    def _cambiar_anio(self, valor):
        self.anio = int(valor)
        self.sel = D.ajustar_fecha(self.sel, self.anio, self.mes)
        self.refrescar()

    def _ir_a_hoy(self):
        self.hoy = date.today().isoformat()
        self.sel = self.hoy
        self.anio, self.mes = int(self.hoy[:4]), int(self.hoy[5:7])
        self.refrescar()

    def _clic_mapa(self, evento):
        """Clic en el mapa anual: columna = día, fila = mes."""
        if evento.xdata is None or evento.ydata is None:
            return
        dia, mes = int(round(evento.xdata)) + 1, int(round(evento.ydata)) + 1
        if not (1 <= mes <= 12 and 1 <= dia <= 31):
            return
        try:
            fecha = date(self.anio, mes, dia).isoformat()
        except ValueError:          # p. ej. 30 de febrero
            return
        self.mes, self.sel = mes, fecha
        self.refrescar()
