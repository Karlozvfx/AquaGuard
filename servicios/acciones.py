"""
Acciones que la interfaz (y la consola) pueden disparar.
Mantiene la lógica FUERA de las ventanas: así se puede probar sin abrir la GUI.
"""
from datetime import date

from clima.senamhi import SenamhiCliente
from servicios.motor import Motor
from servicios import simulador
from sistemas.hardware import ActuadoresSimulados
from sistemas.sensores import SensorLluviaSimulado


def evaluar_hoy(cfg, repo):
    """
    Evalúa el día de hoy con el pronóstico SENAMHI (archivo/URL configurado).
    Devuelve (ok, mensaje). Sin sensor real, la lluvia observada se asume 0 (no se inventa).
    Si hoy ya fue registrado NO se vuelve a ejecutar: duplicaría el consumo del depósito.
    """
    hoy = date.today().isoformat()
    if repo.dia(hoy) is not None:
        return False, f"El día {hoy} ya fue evaluado y registrado."
    pron = SenamhiCliente(cfg).obtener_pronostico(hoy)
    motor = Motor(cfg, repo, ActuadoresSimulados(), SensorLluviaSimulado({}), es_simulacion=True)
    r = motor.ejecutar_dia(hoy, pron)
    return True, r["decision"].motivo


def simular_anio(cfg, repo, anio: int):
    """Simula un año completo. TODO queda marcado como SIMULADO / estimación."""
    repo.guardar_historico(simulador.historial_simulado([anio - 2, anio - 1]), "SIMULADO")
    lluvia, pronos = simulador.generar_anio(anio)
    motor = Motor(cfg, repo, ActuadoresSimulados(), SensorLluviaSimulado(lluvia), es_simulacion=True)
    for f in sorted(pronos):
        motor.ejecutar_dia(f, pronos[f])
    return f"Año {anio} simulado ({len(pronos)} días). Datos SIMULADOS, no son de SENAMHI."
