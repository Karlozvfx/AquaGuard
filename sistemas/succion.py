"""Sistema de succión/captación de agua de lluvia."""


class SistemaSuccion:
    def __init__(self, area_m2, coef, deposito, actuadores, clave="succion"):
        self.area_m2, self.coef, self.deposito, self.act, self.clave = area_m2, coef, deposito, actuadores, clave
        self.armado = False

    def armar(self):
        """Modo lluvia: queda listo para captar (solo enciende si el sensor detecta lluvia)."""
        self.armado = True

    def desarmar(self):
        self.armado = False
        self.act.poner(self.clave, False)

    def captar(self, lluvia_mm: float, umbral_mm: float):
        """
        Devuelve (litros_almacenados, encendio). 1 mm sobre 1 m2 = 1 L.
        Solo capta si está armado, el sensor confirma lluvia y hay espacio en el depósito.
        """
        if not self.armado or lluvia_mm < umbral_mm or self.deposito.disponible_para_llenar <= 0:
            self.act.poner(self.clave, False)
            return 0.0, False
        self.act.poner(self.clave, True)
        potencial = lluvia_mm * self.area_m2 * self.coef
        return self.deposito.llenar(potencial), True
