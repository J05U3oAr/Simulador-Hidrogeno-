"""PEM cuasiestática con eficiencia constante sobre poder calorífico inferior."""

from dataclasses import dataclass
from math import isfinite

from simulador.config import FuelCell


@dataclass(frozen=True)
class Generation:
    net_power_w: float
    gross_power_w: float
    hydrogen_kg_s: float
    waste_heat_w: float


def generate(cell: FuelCell, requested_net_power_w: float, enabled: bool = True) -> Generation:
    if not isfinite(requested_net_power_w) or requested_net_power_w < 0:
        raise ValueError("La potencia solicitada a la celda debe ser finita y no negativa.")
    if not enabled or requested_net_power_w == 0:
        return Generation(0, 0, 0, 0)
    gross = min(cell.gross_power_w, requested_net_power_w + cell.auxiliary_power_w)
    chemical = gross / cell.efficiency_lhv
    return Generation(gross - cell.auxiliary_power_w, gross,
                      chemical / cell.hydrogen_lhv_j_kg, chemical - gross)
