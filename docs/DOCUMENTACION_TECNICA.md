# Sistema de Predicción Climática y Gestión del Agua — Parte 1 (núcleo)

Proyecto completo: motor del sistema (parte 1), interfaz de escritorio en Python con Dashboard (2A),
Calendario (2B) y Estadísticas + Comparación entre años (2C, final).

## Instalación (VS Code)
1. Instala Python 3.10+ y abre la carpeta en VS Code.
2. Terminal: `python -m venv .venv` y activa el entorno (`.venv\Scripts\activate` en Windows).
3. `pip install -r requirements.txt`

## Ejecución
```
python main.py --simular 2025        # año completo con datos SIMULADOS
python main.py --resumen 2025        # resumen mensual/anual guardado en SQLite
python main.py --importar-historico  # carga datos/senamhi/historico.csv
python main.py --hoy                 # decisión de hoy con pronóstico SENAMHI (archivo/URL)
```
La primera ejecución crea `config.json`: edita ahí localidad, estación, umbral (70 % inicial),
área de captación, capacidad del depósito y demanda de cada riego.

## Datos de SENAMHI (sin inventar nada)
No se asume ninguna API pública de SENAMHI. Debes proporcionar los datos:
- **Pronóstico**: `datos/senamhi/pronostico.csv` → `fecha,prob_lluvia,precipitacion_mm,temperatura_c`
  (puedes dejar vacíos los campos que no tengas). Opcionalmente `url_pronostico_csv` en `config.json`
  si tienes una fuente oficial que entregue ese formato.
- **Histórico**: `datos/senamhi/historico.csv` → `fecha,precipitacion_mm` (descarga de SENAMHI).
- Sin archivo/URL, sin conexión o con datos de más de 24 h (`horas_vigencia_pronostico`):
  **no se activa el modo lluvia** y el riego convencional opera normal. El origen y la fecha de
  actualización se guardan con cada predicción.

## Algoritmo de predicción
1. Base: probabilidad de lluvia del pronóstico oficial vigente.
2. El historial mensual (≥ `min_dias_historicos` días) clasifica el mes: lluvioso (≥40 % de días con lluvia),
   seco (≤10 %) o transición. Solo ajusta el umbral ±`margen_estacional` puntos; **no reemplaza** el pronóstico.
3. Activa el modo lluvia si `prob >= umbral efectivo`. Se registra el motivo en `activaciones`.

## Qué hace el modo lluvia
Anula los dos riegos convencionales, arma la succión y almacena agua **solo si el sensor confirma lluvia
y el depósito tiene espacio**. Si el agua guardada no alcanza, el convencional entra como respaldo
(la probabilidad no garantiza lluvia).

## Cálculo del ahorro
- Recolectada (L) = mm × área × coeficiente de escorrentía (limitada por el depósito).
- Lluvia usada = agua extraída del depósito para riego; Convencional = demanda − lluvia usada.
- Total consumido = lluvia usada + convencional. **Ahorrada = lluvia usada.**
- Sin sensores reales todo se marca `es_estimacion = 1`.

## Conexión de dispositivos físicos
Crea una clase que herede de `sistemas.hardware.Actuadores` (relés vía serial/WiFi del ESP32/Arduino)
y una de `sistemas.sensores.SensorLluvia` (pluviómetro/sensor de lluvia), con `es_estimacion = False`.
Pásalas a `Motor(...)` en `main.py`. Añade un sensor de nivel para reemplazar `Deposito`.

## GitHub
`git init && git add . && git commit -m "Parte 1: núcleo"` (`.gitignore` ya excluye BD y config).

---

## Parte 2A: interfaz gráfica y Dashboard (sección 5)

Interfaz de escritorio hecha 100 % en Python (CustomTkinter + matplotlib). Sin HTML, CSS ni JavaScript.

### Instalar y ejecutar (Visual Studio Code)
```bash
pip install -r requirements.txt
python main.py            # abre la interfaz (también: python main.py --gui)
```
Si usas Linux y falta tkinter: `sudo apt install python3-tk`.

### Qué muestra el Dashboard
- Probabilidad de lluvia de HOY (solo pronóstico SENAMHI) con barra frente al umbral.
- Estado de la predicción: VIGENTE / DESACTUALIZADO / SIN PRONÓSTICO, con origen y fecha de actualización.
- Temperatura (solo si el pronóstico la trae) y precipitación registrada (día y mes).
- Estado de Riego 1, Riego 2 y succión, con colores; modo lluvia y su motivo.
- Agua en el depósito, usada, ahorrada y recolectada (día, mes y año), siempre marcada como ESTIMADO si es simulación.
- Gráfico de lluvia (mm) y ahorro (L) de los últimos 30 días, y gráfico circular lluvia vs. convencional del año.
- Botones: **Actualizar**, **Evaluar hoy** (usa el pronóstico configurado; no se ejecuta dos veces el mismo día) y **Simular año…**.

### Archivos nuevos
| Archivo | Función |
|---|---|
| `interfaz/app.py` | Ventana principal y menú lateral |
| `interfaz/dashboard.py` | Vista del Dashboard (solo dibuja) |
| `interfaz/datos_dashboard.py` | Prepara los datos (sin ventanas, se puede probar solo) |
| `interfaz/graficos.py` | Gráficos matplotlib |
| `interfaz/estilos.py` | Colores, fuentes y estados |
| `servicios/acciones.py` | «Evaluar hoy» y «Simular año» |

Pendiente para las siguientes partes: Calendario diario, Estadísticas mensuales/anuales y Comparación entre años (el menú ya tiene sus entradas).

---

## Parte 2B: Calendario diario (sección 6)

Entrada **Calendario** del menú lateral. Sigue siendo Python puro (CustomTkinter + matplotlib).

### Qué hace
- **Cuadrícula del mes** (semana desde el lunes). Cada día muestra los mm de lluvia y un color:
  celeste = llovió · verde = no llovió pero se regó con lluvia guardada · ámbar = riego mixto ·
  naranja = solo agua convencional · gris = sin registro. El día de hoy lleva borde ámbar.
- **Selector de año** (solo años con datos en la base) y botones ‹ › para cambiar de mes. «Hoy» vuelve a la fecha actual.
- **Mapa del año**: 12 meses × 31 días con la lluvia diaria; haz clic en cualquier día para seleccionarlo.
- **Detalle del día**: fecha, si llovió, precipitación (mm), agua recolectada, lluvia usada, agua convencional,
  total consumido, agua ahorrada, nivel del depósito, estado de Riego 1 y Riego 2, modo lluvia y su motivo,
  y el pronóstico que se guardó ese día (con origen y fecha de actualización).
- **Mismo día en otros años**: lista de los demás años con datos para esa fecha, para comparar.

### Honestidad de los datos
- Un día sin registro se muestra como «SIN REGISTRO»: nunca se rellena con valores inventados.
- Los días simulados se marcan **ESTIMADO / SIMULADO** y las cifras llevan «(est.)».
- Si no hay pronóstico guardado para el día, se dice «Sin pronóstico guardado».

### Archivos nuevos o modificados
| Archivo | Función |
|---|---|
| `interfaz/calendario.py` | Vista del calendario (solo dibuja) |
| `interfaz/datos_calendario.py` | Prepara los datos del mes y del día (sin ventanas, se puede probar solo) |
| `interfaz/graficos.py` | Se añadió `dibujar_mapa_anio` |
| `base_datos/operaciones.py` | Consultas nuevas: `dias_mes`, `dias_anio`, `mismo_dia_otros_anios`, `prediccion_dia` |
| `interfaz/app.py` | Registra la vista Calendario en el menú |

Para ver datos: en el Dashboard pulsa **Simular año…** (por ejemplo 2024 y luego 2025) y abre **Calendario**.

---

## Parte 2C: Estadísticas y Comparar años (sección 7)

Entradas **Estadísticas** y **Comparar años** del menú lateral. Python puro (CustomTkinter + matplotlib).

### Estadísticas (un año a la vez, selector de año arriba a la derecha)
- **Totales de todo el año**: agua usada, convencional, ahorrada (con % del riego cubierto por lluvia),
  recolectada, días lluviosos y precipitación acumulada.
- **Rankings**: mes que más ahorró, mes que más agua convencional usó, mes con más días lluviosos y
  mes que más recolectó (si hay empate se muestran ambos meses).
- **Gráficos** (pestañas): barras de ahorrada vs convencional con línea del total · barras de días
  lluviosos con línea de mm · líneas de recolectada / lluvia usada / convencional.
- **Tabla mensual** con una fila por mes y el total del año.

### Comparar años
- Elige un **año base** y marca con qué otros años comparar (solo aparecen años con datos).
- Métrica mensual a elegir (ahorrada, convencional, recolectada, total, días lluviosos, mm) en **barras o líneas**.
- Gráfico de **totales anuales** por año y un resumen por año con el **cambio porcentual frente al año base**.
- Marca qué año ahorró más agua.

### Honestidad de los datos
- Un mes sin registros se dibuja **vacío**, nunca como 0 (no es lo mismo «no hay dato» que «no se ahorró nada»).
- Los meses con registro parcial (p. ej. el año en curso) se avisan: sus totales no son comparables con meses completos.
- Si el año contiene datos simulados se indica «ESTIMADO / SIMULADO» y las cifras llevan «(est.)».
- Sin datos en la base, ambas vistas explican cómo generarlos (Dashboard → «Simular año…»).

### Archivos nuevos o modificados
| Archivo | Función |
|---|---|
| `interfaz/estadisticas.py` | Vista Estadísticas (solo dibuja) |
| `interfaz/comparacion.py` | Vista Comparar años (solo dibuja) |
| `interfaz/datos_estadisticas.py` | Series mensuales, rankings, totales y variaciones (sin ventanas, se puede probar solo) |
| `interfaz/graficos.py` | Se añadieron `dibujar_mensual`, `dibujar_comparacion`, `dibujar_totales_anios` |
| `base_datos/operaciones.py` | `resumen_mensual` ahora incluye `dias_registrados`; nueva `anio_tiene_estimacion` |
| `interfaz/app.py` | Registra las dos vistas (ya no hay secciones pendientes) |

### Cómo probarlo
1. `python main.py`
2. Dashboard → **Simular año…** con 2023, luego 2024 y 2025 (cada uno por separado).
3. Abre **Estadísticas** (cambia de año) y **Comparar años**.

## Estado del proyecto
Todas las secciones del documento de requisitos están implementadas. Para pasar de simulación a datos reales:
carga tus CSV oficiales de SENAMHI (ver «Datos de SENAMHI») y conecta tu hardware (ver «Conexión de dispositivos físicos»).
