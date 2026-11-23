"""
Cálculo del ahorro de agua.

  total_consumido = lluvia_usada + convencional
  agua_ahorrada   = lluvia_usada   (agua convencional que NO se gastó)
  recolectada     = litros que entraron al depósito (limitado por su capacidad)
Sin sensores reales, todo es ESTIMACIÓN (es_estimacion = 1).
"""


def calcular_dia(demanda_l, deposito, usar_lluvia: bool):
    """Cubre la demanda con el depósito (si se permite) y el resto con agua convencional."""
    lluvia_usada = deposito.extraer(demanda_l) if usar_lluvia else 0.0
    convencional = demanda_l - lluvia_usada
    return {
        "lluvia_usada_l": round(lluvia_usada, 2),
        "convencional_l": round(convencional, 2),
        "total_consumido_l": round(lluvia_usada + convencional, 2),
        "agua_ahorrada_l": round(lluvia_usada, 2),
    }
