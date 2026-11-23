"""Los dos sistemas de riego convencionales."""


class SistemaRiego:
    def __init__(self, nombre: str, clave: str, demanda_l_dia: float, actuadores):
        self.nombre, self.clave, self.demanda_l_dia, self.act = nombre, clave, demanda_l_dia, actuadores
        self.anulado = False      # True = anulado temporalmente por el modo lluvia

    def anular(self):
        self.anulado = True
        self.act.poner(self.clave, False)

    def habilitar(self):
        self.anulado = False
