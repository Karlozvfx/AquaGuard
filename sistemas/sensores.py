"""
Sensores. Aquí hay SOLO implementaciones simuladas (valores = ESTIMACIONES).
Para hardware real, crea clases con la misma interfaz (ver README).
"""
from abc import ABC, abstractmethod


class SensorLluvia(ABC):
    es_estimacion = True

    @abstractmethod
    def leer_mm(self, fecha: str) -> float: ...


class SensorLluviaSimulado(SensorLluvia):
    """La 'lluvia real' la dicta el simulador (dict fecha -> mm)."""
    def __init__(self, lluvia_real: dict):
        self.lluvia_real = lluvia_real

    def leer_mm(self, fecha):
        return self.lluvia_real.get(fecha, 0.0)


class Deposito:
    """Depósito de agua. Nivel simulado hasta tener un sensor de nivel real."""
    es_estimacion = True

    def __init__(self, capacidad_l: float, nivel_l: float = 0.0):
        self.capacidad_l = capacidad_l
        self.nivel_l = min(nivel_l, capacidad_l)

    @property
    def disponible_para_llenar(self):
        return self.capacidad_l - self.nivel_l

    def llenar(self, litros: float) -> float:
        """Agrega agua; devuelve los litros realmente almacenados (el resto se desborda)."""
        guardado = min(litros, self.disponible_para_llenar)
        self.nivel_l += guardado
        return guardado

    def extraer(self, litros: float) -> float:
        sacado = min(litros, self.nivel_l)
        self.nivel_l -= sacado
        return sacado
