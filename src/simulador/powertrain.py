"""Gestión de energía del bus: PEM primero, banco para picos y recarga limitada."""

from dataclasses import dataclass, replace
from math import isfinite

from simulador.capacitor import energy_j, exchange
from simulador.config import Config
from simulador.fuel_cell import generate
from simulador.tank import withdraw


@dataclass(frozen=True)
class PowerStep:
    hydrogen_mass_kg: float
    capacitor_energy_j: float
    hydrogen_used_kg: float
    fuel_cell_bus_power_w: float
    capacitor_bus_power_w: float
    served_power_w: float
    unserved_power_w: float
    loss_power_w: float
    chemical_power_w: float
    balance_error_w: float


def dispatch(config: Config, load_w: float, mass_kg: float, cap_energy_j: float,
             dt_s: float, enabled: bool = True) -> PowerStep:
    if not all(isfinite(x) and x >= 0 for x in (load_w, mass_kg, cap_energy_j)) or not isfinite(dt_s) or dt_s <= 0:
        raise ValueError("Carga y estados no negativos; paso positivo y finito requerido.")
    if not enabled:
        return PowerStep(mass_kg, cap_energy_j, 0, 0, 0, 0, load_w, 0, 0, 0)
    cap = config.capacitor
    room_j = max(0, energy_j(cap, cap.maximum_voltage_v) - cap_energy_j)
    recharge_w = min(config.bus.capacitor_recharge_power_w, cap.max_charge_power_w,
                     room_j / cap.charge_efficiency / dt_s)
    converter_eff = config.bus.fuel_cell_converter_efficiency
    cell = generate(config.fuel_cell, (load_w + recharge_w) / converter_eff)
    mass_after, used = withdraw(config.tank, mass_kg, cell.hydrogen_kg_s * dt_s)
    # Si el combustible se agota durante el paso, las potencias son promedios del intervalo.
    if cell.hydrogen_kg_s > 0:
        fraction = used / (cell.hydrogen_kg_s * dt_s)
        cell = replace(cell, net_power_w=cell.net_power_w * fraction,
                       gross_power_w=cell.gross_power_w * fraction,
                       hydrogen_kg_s=cell.hydrogen_kg_s * fraction,
                       waste_heat_w=cell.waste_heat_w * fraction)
    fc_bus = cell.net_power_w * converter_eff
    bank = exchange(cap, cap_energy_j, load_w - fc_bus, dt_s)
    available = fc_bus + bank.bus_power_w
    served = min(load_w, max(0, available))
    unserved = max(0, load_w - served)
    chemical = used / dt_s * config.fuel_cell.hydrogen_lhv_j_kg
    losses = chemical - fc_bus + bank.loss_power_w
    return PowerStep(mass_after, bank.energy_j, used, fc_bus, bank.bus_power_w,
                     served, unserved, losses, chemical, available + unserved - load_w)
