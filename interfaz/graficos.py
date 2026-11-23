"""
Gráficos del Dashboard con matplotlib (sin tkinter): reciben una Figure y la dibujan.
Así se pueden probar sin abrir ventanas.
"""
from interfaz.estilos import TARJETA, TEXTO, TEXTO_SUAVE, BORDE, COLORES


def _base(fig):
    fig.clear()
    fig.patch.set_facecolor(TARJETA)
    ax = fig.add_subplot(111)
    ax.set_facecolor(TARJETA)
    for s in ax.spines.values():
        s.set_color(BORDE)
    ax.tick_params(colors=TEXTO_SUAVE, labelsize=8)
    return ax


def _vacio(ax, texto):
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(0.5, 0.5, texto, ha="center", va="center", color=TEXTO_SUAVE, fontsize=10, transform=ax.transAxes)


def dibujar_serie(fig, filas):
    """Barras = lluvia (mm). Línea = agua ahorrada (L). `filas` viene de Repositorio.ultimos_dias()."""
    ax = _base(fig)
    if not filas:
        _vacio(ax, "Sin datos registrados todavía")
        fig.tight_layout(); return
    x = list(range(len(filas)))
    etiquetas = [f["fecha"][8:10] + "/" + f["fecha"][5:7] for f in filas]
    ax.bar(x, [f["precipitacion_mm"] or 0 for f in filas], color=COLORES["lluvia"], label="Lluvia (mm)")
    ax.set_ylabel("mm", color=TEXTO_SUAVE, fontsize=8)
    paso = max(1, len(x) // 8)
    ax.set_xticks(x[::paso]); ax.set_xticklabels(etiquetas[::paso], rotation=0)
    ax2 = ax.twinx()
    ax2.plot(x, [f["agua_ahorrada_l"] or 0 for f in filas], color=COLORES["ahorro"], lw=2, label="Ahorro (L)")
    ax2.set_ylabel("litros", color=TEXTO_SUAVE, fontsize=8)
    ax2.tick_params(colors=TEXTO_SUAVE, labelsize=8)
    for s in ax2.spines.values():
        s.set_color(BORDE)
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    leg = ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8, frameon=False)
    for t in leg.get_texts():
        t.set_color(TEXTO)
    ax.set_title(f"Últimos {len(filas)} días registrados", color=TEXTO, fontsize=10)
    fig.tight_layout()


def dibujar_donut(fig, lluvia_l, convencional_l, titulo="Origen del agua usada (año)"):
    ax = _base(fig)
    total = (lluvia_l or 0) + (convencional_l or 0)
    ax.set_title(titulo, color=TEXTO, fontsize=10)
    if total <= 0:
        _vacio(ax, "Sin consumo registrado")
        fig.tight_layout(); return
    ax.pie([lluvia_l, convencional_l], colors=[COLORES["lluvia"], COLORES["convencional"]],
           startangle=90, counterclock=False, wedgeprops=dict(width=0.38, edgecolor=TARJETA))
    ax.text(0, 0, f"{lluvia_l / total * 100:.0f}%\nlluvia", ha="center", va="center", color=TEXTO, fontsize=12)
    leg = ax.legend([f"Lluvia {lluvia_l:,.0f} L", f"Convencional {convencional_l:,.0f} L"],
                    loc="lower center", fontsize=8, frameon=False, ncol=1, bbox_to_anchor=(0.5, -0.18))
    for t in leg.get_texts():
        t.set_color(TEXTO)
    fig.tight_layout()


def dibujar_mapa_anio(fig, anio, mm_por_fecha, seleccion=None):
    """
    Mapa del año: 12 filas (meses) x 31 columnas (días). Más celeste = más lluvia (mm).
    Los días sin registro (o que no existen, como 30 de febrero) quedan en gris oscuro.
    `mm_por_fecha` = {'YYYY-MM-DD': mm o None}. `seleccion` = fecha resaltada con un recuadro.
    """
    import calendar
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.patches import Rectangle

    ax = _base(fig)
    datos = np.full((12, 31), np.nan)
    for fecha, mm in mm_por_fecha.items():
        if fecha[:4] == str(anio) and mm is not None:
            datos[int(fecha[5:7]) - 1, int(fecha[8:10]) - 1] = mm
    cmap = LinearSegmentedColormap.from_list("lluvia", ["#1d2c4d", COLORES["lluvia"]]).copy()
    cmap.set_bad("#0f172a")
    vmax = max(5.0, float(np.nanmax(datos))) if np.isfinite(datos).any() else 5.0
    ax.imshow(np.ma.masked_invalid(datos), cmap=cmap, vmin=0, vmax=vmax, aspect="auto", interpolation="nearest")

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    ax.set_yticks(range(12)); ax.set_yticklabels(meses)
    ax.set_xticks([0, 4, 9, 14, 19, 24, 29]); ax.set_xticklabels(["1", "5", "10", "15", "20", "25", "30"])
    ax.set_title(f"Mapa del año {anio} · lluvia diaria (mm) · haz clic en un día", color=TEXTO, fontsize=9)
    if seleccion and seleccion[:4] == str(anio):
        m, d = int(seleccion[5:7]), int(seleccion[8:10])
        if d <= calendar.monthrange(anio, m)[1]:
            ax.add_patch(Rectangle((d - 1.5, m - 1.5), 1, 1, fill=False, edgecolor=TEXTO, lw=1.8))
    fig.tight_layout()


# ====================== Sección 7: estadísticas y comparación ======================
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
PALETA_ANIOS = ["#38bdf8", "#f59e0b", "#a78bfa", "#34d399", "#f472b6", "#facc15", "#fb7185", "#2dd4bf"]


def color_anio(indice: int) -> str:
    return PALETA_ANIOS[indice % len(PALETA_ANIOS)]


def _nan(valores):
    """None (mes sin datos) -> NaN: matplotlib no dibuja nada en vez de dibujar un falso 0."""
    return [float("nan") if v is None else v for v in valores]


def _leyenda_clara(ax, handles, labels, loc="upper left", ejes_extra=()):
    """Leyenda en una fila; se deja espacio libre arriba para que no tape barras ni líneas."""
    for a in (ax, *ejes_extra):
        a.set_ylim(top=a.get_ylim()[1] * 1.22)
    leg = ax.legend(handles, labels, loc=loc, fontsize=8, frameon=False, ncol=len(labels))
    for t in leg.get_texts():
        t.set_color(TEXTO)


def _eje_meses(ax):
    ax.set_xticks(range(12)); ax.set_xticklabels(MESES_CORTOS)
    ax.grid(axis="y", color=BORDE, lw=0.6, alpha=0.7); ax.set_axisbelow(True)


def dibujar_mensual(fig, titulo, barras=(), lineas=(), etq_barras="", etq_lineas="", eje_comun=False):
    """
    Gráfico mensual (12 meses). `barras` y `lineas` = [(valores12, etiqueta, color), ...].
    Barras en el eje izquierdo; líneas en un eje derecho propio SOLO si tienen otra unidad
    (p. ej. días vs mm). Con `eje_comun=True` comparten el eje (misma unidad: litros).
    Los meses sin datos (None) quedan vacíos.
    """
    import numpy as np
    ax = _base(fig)
    ax.set_title(titulo, color=TEXTO, fontsize=10)
    hay = any(v is not None for serie in list(barras) + list(lineas) for v in serie[0])
    if not hay:
        _vacio(ax, "Sin datos para este año")
        fig.tight_layout(); return
    _eje_meses(ax)
    handles, labels = [], []
    n = max(1, len(barras))
    ancho = 0.8 / n
    for i, (vals, etq, color) in enumerate(barras):
        pos = np.arange(12) - 0.4 + ancho * (i + 0.5)
        h = ax.bar(pos, _nan(vals), width=ancho * 0.92, color=color)
        handles.append(h); labels.append(etq)
    if barras:
        ax.set_ylabel(etq_barras, color=TEXTO_SUAVE, fontsize=8)
    eje_l = ax.twinx() if barras and lineas and not eje_comun else ax
    if eje_l is not ax:
        eje_l.tick_params(colors=TEXTO_SUAVE, labelsize=8)
        for s in eje_l.spines.values():
            s.set_color(BORDE)
        eje_l.set_ylabel(etq_lineas, color=TEXTO_SUAVE, fontsize=8)
    elif lineas and not barras:
        ax.set_ylabel(etq_lineas, color=TEXTO_SUAVE, fontsize=8)
    for vals, etq, color in lineas:
        h, = eje_l.plot(range(12), _nan(vals), color=color, lw=2, marker="o", ms=4)
        handles.append(h); labels.append(etq)
    _leyenda_clara(ax, handles, labels, ejes_extra=(eje_l,) if eje_l is not ax else ())
    fig.tight_layout()


def dibujar_comparacion(fig, titulo, series, unidad, modo="barras"):
    """
    Compara una métrica mes a mes entre varios años.
    `series` = [(anio, valores12, color), ...]; modo = 'barras' (agrupadas) o 'lineas'.
    """
    import numpy as np
    ax = _base(fig)
    ax.set_title(titulo, color=TEXTO, fontsize=10)
    if not series or not any(v is not None for _, vals, _ in series for v in vals):
        _vacio(ax, "Sin datos para comparar")
        fig.tight_layout(); return
    _eje_meses(ax)
    handles, labels = [], []
    n = len(series)
    ancho = 0.8 / n
    for i, (anio, vals, color) in enumerate(series):
        if modo == "lineas":
            h, = ax.plot(range(12), _nan(vals), color=color, lw=2, marker="o", ms=4)
        else:
            h = ax.bar(np.arange(12) - 0.4 + ancho * (i + 0.5), _nan(vals), width=ancho * 0.92, color=color)
        handles.append(h); labels.append(str(anio))
    ax.set_ylabel(unidad, color=TEXTO_SUAVE, fontsize=8)
    _leyenda_clara(ax, handles, labels)
    fig.tight_layout()


def dibujar_totales_anios(fig, filas):
    """
    Totales anuales por año. `filas` = [{'anio', 'total_l', 'convencional_l', 'ahorrada_l',
    'recolectada_l'}, ...]. Barras agrupadas: una por concepto, un grupo por año.
    """
    import numpy as np
    ax = _base(fig)
    ax.set_title("Totales del año (L)", color=TEXTO, fontsize=10)
    if not filas:
        _vacio(ax, "Sin datos para comparar")
        fig.tight_layout(); return
    conceptos = [("total_l", "Total consumido", "#94a3b8"), ("convencional_l", "Convencional", COLORES["convencional"]),
                 ("ahorrada_l", "Ahorrada", COLORES["ahorro"]), ("recolectada_l", "Recolectada", COLORES["lluvia"])]
    n = len(conceptos)
    ancho = 0.8 / n
    x = np.arange(len(filas))
    handles = []
    for i, (clave, etq, color) in enumerate(conceptos):
        vals = [f[clave] for f in filas]
        h = ax.bar(x - 0.4 + ancho * (i + 0.5), vals, width=ancho * 0.92, color=color)
        handles.append(h)
        if len(filas) <= 4:     # con pocos años se escribe el valor encima de cada barra
            for xi, v in zip(x - 0.4 + ancho * (i + 0.5), vals):
                ax.text(xi, v, f"{v:,.0f}", ha="center", va="bottom", color=TEXTO_SUAVE, fontsize=6.5)
    ax.set_xticks(x); ax.set_xticklabels([str(f["anio"]) for f in filas])
    ax.grid(axis="y", color=BORDE, lw=0.6, alpha=0.7); ax.set_axisbelow(True)
    ax.set_ylabel("litros", color=TEXTO_SUAVE, fontsize=8)
    _leyenda_clara(ax, handles, [c[1] for c in conceptos])
    fig.tight_layout()
