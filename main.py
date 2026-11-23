"""
Punto de entrada (primera mitad: núcleo sin interfaz gráfica).

  python main.py --simular 2025          # simula un año completo (datos SIMULADOS)
  python main.py --hoy                   # evalúa hoy con el pronóstico SENAMHI (archivo/URL)
  python main.py --importar-historico    # carga datos/senamhi/historico.csv a la base
  python main.py --resumen 2025          # tablas mensual/anual guardadas en SQLite
  python main.py                         # sin argumentos: abre la interfaz gráfica
  python main.py --gui                   # idem
"""
import argparse
from datetime import date

from config import Config
from base_datos.conexion import conectar
from base_datos.operaciones import Repositorio
from clima.senamhi import SenamhiCliente
from clima.datos_historicos import importar_csv, MESES
from sistemas.hardware import ActuadoresSimulados
from sistemas.sensores import SensorLluviaSimulado
from servicios.motor import Motor
from servicios import simulador


def imprimir_resumen(repo, anio):
    filas = repo.resumen_mensual(anio)
    if not filas:
        print(f"Sin datos para {anio}.")
        return
    print(f"\nResumen {anio} (litros; valores ESTIMADOS si vienen de simulación)")
    print(f"{'Mes':<4}{'DíasLluv':>9}{'mm':>8}{'Recolect':>10}{'Lluvia':>9}{'Convenc':>9}{'Total':>9}{'Ahorro':>9}")
    for r in filas:
        print(f"{MESES[r['mes']-1]:<4}{r['dias_lluviosos']:>9}{r['precipitacion_mm']:>8.1f}{r['recolectada_l']:>10.0f}"
              f"{r['lluvia_usada_l']:>9.0f}{r['convencional_l']:>9.0f}{r['total_l']:>9.0f}{r['ahorrada_l']:>9.0f}")
    a = repo.resumen_anual(anio)
    print(f"AÑO: días lluviosos={a['dias_lluviosos']}  recolectada={a['recolectada_l']:.0f} L  "
          f"usada(total)={a['total_l']:.0f} L  convencional={a['convencional_l']:.0f} L  AHORRADA={a['ahorrada_l']:.0f} L")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--simular", type=int, metavar="AÑO")
    ap.add_argument("--hoy", action="store_true")
    ap.add_argument("--importar-historico", action="store_true")
    ap.add_argument("--resumen", type=int, metavar="AÑO")
    ap.add_argument("--gui", action="store_true", help="abre la interfaz gráfica")
    args = ap.parse_args()

    cfg = Config.cargar()
    repo = Repositorio(conectar(cfg.ruta(cfg.ruta_bd)))

    if args.importar_historico:
        print(f"Filas importadas de SENAMHI: {importar_csv(cfg, repo)}")

    if args.simular:
        a = args.simular
        print("*** MODO SIMULACIÓN: datos generados, NO son de SENAMHI ***")
        repo.guardar_historico(simulador.historial_simulado([a - 2, a - 1]), "SIMULADO")
        lluvia, pronos = simulador.generar_anio(a)
        motor = Motor(cfg, repo, ActuadoresSimulados(), SensorLluviaSimulado(lluvia), es_simulacion=True)
        for f in sorted(pronos):
            motor.ejecutar_dia(f, pronos[f])
        imprimir_resumen(repo, a)

    if args.hoy:
        hoy = date.today().isoformat()
        pron = SenamhiCliente(cfg).obtener_pronostico(hoy)
        if pron is None:
            print(f"[{hoy}] Sin pronóstico SENAMHI disponible (revisa config y datos/senamhi/pronostico.csv).")
        else:
            print(f"[{hoy}] Origen: {pron.origen} | Actualizado: {pron.actualizado} | Vigente: {pron.vigente} "
                  f"| Prob. lluvia: {pron.prob_lluvia}%")
        # Sin sensor real conectado: la lluvia observada se asume 0 (no se inventa).
        motor = Motor(cfg, repo, ActuadoresSimulados(), SensorLluviaSimulado({}), es_simulacion=True)
        motor.recalcular_historial()
        r = motor.ejecutar_dia(hoy, pron)
        print("Decisión:", r["decision"].motivo, "| Riego1:", r["riego1"], "| Riego2:", r["riego2"],
              "| Depósito:", r["nivel_deposito_l"], "L (estimado)")

    if args.resumen:
        imprimir_resumen(repo, args.resumen)

    if args.gui or not any([args.simular, args.hoy, args.importar_historico, args.resumen]):
        repo.con.close()
        try:
            from interfaz.app import iniciar   # import tardío: la consola no exige customtkinter
        except ModuleNotFoundError as e:
            import sys
            print(f"\nFalta el módulo '{e.name}' en este Python:\n  {sys.executable}\n"
                  f"Instálalo con:\n  \"{sys.executable}\" -m pip install -r requirements.txt\n"
                  "o selecciona en VS Code el intérprete donde ya lo instalaste "
                  "(Ctrl+Shift+P > Python: Select Interpreter).")
            sys.exit(1)
        iniciar()


if __name__ == "__main__":
    main()
