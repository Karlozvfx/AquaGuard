AquaGuard — Sistema inteligente de gestión hídrica y prevención de riesgos urbanos para Villa El Salvador

Prototipo funcional que usa el **pronóstico de lluvia de SENAMHI** para decidir cada día si se riega con agua
convencional o con **agua de lluvia almacenada**, y que registra, calcula y muestra cuánta agua potable se ahorra.

Equipo

| Nombre | Rol |
|---|---|
| Huertas Silva, Ángel | Backend / Lógica de predicción |
| Chumpitaz Quin, Carlos | Frontend / UI |
| Bendezu Champiama, Víctor | API GitHub / Integración |

Problema y solución

Villa El Salvador (Lima Sur) tiene acceso desigual al agua potable: muchas familias dependen de camiones cisterna
y el riego de áreas verdes y huertos compite con el consumo humano. Al mismo tiempo, no existe una herramienta
sencilla que ayude a decidir cuándo conviene captar y usar agua de lluvia en lugar de agua de red.

**AquaGuard** es un sistema de escritorio que:

1. **Predice** si habrá lluvia (usa la probabilidad del pronóstico oficial de SENAMHI y la ajusta ±5 puntos según el
   historial de lluvias del mes; nunca reemplaza el pronóstico).
2. **Decide** si activar el *modo lluvia* cuando la probabilidad supera el umbral (70 % por defecto, configurable).
3. **Actúa**: anula los riegos convencionales, arma la succión y almacena agua en el depósito solo si el sensor
   confirma lluvia y hay espacio. Si el agua guardada no alcanza, el riego convencional entra como respaldo.
4. **Mide**: calcula agua recolectada, usada, convencional y **ahorrada**, y guarda todo en una base de datos.
5. **Muestra**: Dashboard en vivo, Calendario diario, Estadísticas mensuales/anuales y Comparación entre años.

> **Honestidad de los datos:** no se inventa información. Sin pronóstico vigente no se activa el modo lluvia;
> los datos simulados se marcan siempre como **ESTIMADO / SIMULADO**; un día sin registro se muestra como
> «sin registro», no como 0.

Objetivos de Desarrollo Sostenible (ODS)

| ODS | Aporte del proyecto |
|---|---|
| **ODS 6 — Agua limpia y saneamiento** | Reduce el uso de agua potable en riego aprovechando agua de lluvia; mide el ahorro en litros. |
| **ODS 11 — Ciudades y comunidades sostenibles** | Gestión eficiente del recurso hídrico urbano y base de datos climática local para decisiones comunitarias. |
| **ODS 13 — Acción por el clima** | Usa información climática oficial para adaptarse a la variabilidad de lluvias y registrar su historial. |

Tecnologías

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.10+ |
| Interfaz (frontend) | CustomTkinter (escritorio) · Streamlit (web) |
| Gráficos | matplotlib |
| Base de datos | SQLite (incluida en Python) |
| Datos climáticos | CSV de SENAMHI (pronóstico e histórico); `requests` opcional si hay una URL oficial |
| Control de versiones | Git + GitHub |

Estructura: `clima/` (predicción y datos SENAMHI) · `servicios/` (motor, ahorro, simulador) · `sistemas/` (riego, succión,
sensores, hardware) · `base_datos/` (SQLite) · `interfaz/` (pantallas) · `datos/` (CSV) · `docs/` (documentación técnica).

Instalación

Requisitos: **Python 3.10 o superior** (con tkinter; en Windows y macOS ya viene incluido).

```bash
git clone https://github.com/Karlozvfx/AquaGuard.git
cd AquaGuard

python -m venv .venv
# Windows:        .venv\Scripts\activate
# Linux / macOS:  source .venv/bin/activate

pip install -r requirements.txt            # versión web (Streamlit)
pip install -r requirements-escritorio.txt # solo si usarás la app de escritorio (CustomTkinter)
```

- Linux: si falta tkinter → `sudo apt install python3-tk`.
- VS Code: elige el intérprete del entorno (`Ctrl+Shift+P` → *Python: Select Interpreter* → `.venv`). Si ves
  `No module named 'customtkinter'`, estás usando otro Python distinto al que instalaste los paquetes.

Uso

Demo con interfaz gráfica
```bash
python main.py
```
1. En **Dashboard** pulsa **Simular año…** y genera 2023, luego 2024 y 2025 (uno por uno).
2. Abre **Calendario** (clic en un día para ver el detalle), **Estadísticas** y **Comparar años**.
3. Pulsa **Evaluar hoy** para ver la decisión con el pronóstico de `datos/senamhi/pronostico.csv`.

Línea de comandos
```bash
python main.py --simular 2025        # año completo con datos SIMULADOS
python main.py --resumen 2025        # resumen mensual/anual guardado
python main.py --hoy                 # decisión de hoy con el pronóstico SENAMHI
python main.py --importar-historico  # carga datos/senamhi/historico.csv
```

Versión web (Streamlit)
```bash
streamlit run streamlit_app.py
```
Abre http://localhost:8501. Tiene las mismas 4 pantallas que la app de escritorio (Dashboard, Calendario,
Estadísticas, Comparar años) y reutiliza el mismo núcleo y los mismos gráficos. La interfaz web vive en
`interfaz_web/`; la de escritorio (`interfaz/`) sigue funcionando con `python main.py`.

Publicarla en internet (Streamlit Community Cloud, gratis)
1. Sube el repositorio a GitHub (`git add . && git commit -m "Versión web" && git push`).
2. En https://share.streamlit.io elige **Create app**, selecciona tu repositorio y la rama `main`, y como
   *Main file path* escribe `streamlit_app.py`.
3. En *Advanced settings* elige una versión de Python 3.10–3.13 (si la nube aún no ofrece la que usas en tu PC).
4. Pulsa **Deploy**. En el primer ingreso pulsa **Cargar demostración** en el Dashboard.

Notas importantes para la versión publicada:
- **Los datos no son permanentes.** La nube puede reiniciar el servidor (p. ej. tras un tiempo de inactividad) y se pierden los archivos creados mientras corría
  (`datos/sistema.db`, `config.json`). Tras un reinicio hay que volver a cargar la demostración. Para datos
  permanentes habría que migrar a una base externa (p. ej. Supabase/Postgres).
- **Cualquier visitante comparte la misma base de datos.** Para que solo tú puedas modificar datos, en
  *Settings → Secrets* de la app agrega `ADMIN_PASSWORD = "tu-clave"`: los botones «Evaluar hoy», «Simular año»
  y «Cargar demostración» pedirán esa clave en la barra lateral. Sin ese secreto, quedan abiertos.
- `datos/senamhi/pronostico.csv` debe estar actualizado (hasta 24 h) para que el pronóstico cuente como vigente.

Configuración y datos reales
La primera ejecución crea `config.json` (localidad, umbral, área de captación, capacidad del depósito, demanda de riego).
Coloca los CSV oficiales de SENAMHI en `datos/senamhi/`:
- `pronostico.csv` → `fecha,prob_lluvia,precipitacion_mm,temperatura_c`
- `historico.csv` → `fecha,precipitacion_mm`

Más detalle del algoritmo, el cálculo del ahorro y la conexión de hardware (ESP32/Arduino) en
[`docs/DOCUMENTACION_TECNICA.md`](docs/DOCUMENTACION_TECNICA.md).

Alcance actual y próximos pasos

- El prototipo funciona hoy en **modo simulación** (sin sensores físicos). El perfil de lluvia simulado es un ejemplo
  genérico y **no representa el clima de Villa El Salvador**; con los CSV reales de SENAMHI se usan datos oficiales.
- **Prevención de riesgos urbanos** (alertas por lluvias intensas, aniegos, etc.): planificado como siguiente módulo,
  aprovechando el mismo pronóstico y el historial ya almacenado.
- Integración con sensores reales (pluviómetro y nivel de depósito) mediante las clases `Actuadores` y `SensorLluvia`.

Licencia
MIT
