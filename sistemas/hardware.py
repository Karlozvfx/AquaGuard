"""
Interfaz de actuadores (relés). La simulación solo guarda estados en memoria.
Para conectar un ESP32/Arduino, crea otra clase que herede de Actuadores
(ver README: 'Conexión de dispositivos físicos').
"""
from abc import ABC, abstractmethod


class Actuadores(ABC):
    @abstractmethod
    def poner(self, nombre: str, encendido: bool): ...

    @abstractmethod
    def leer(self, nombre: str) -> bool: ...


class ActuadoresSimulados(Actuadores):
    def __init__(self):
        self.estado = {"riego1": False, "riego2": False, "succion": False}

    def poner(self, nombre, encendido):
        self.estado[nombre] = encendido

    def leer(self, nombre):
        return self.estado[nombre]
