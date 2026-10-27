"""Banco equivalente y convertidor bidireccional de eficiencia agregada constante."""

from dataclasses import dataclass
from math import isfinite, sqrt

from simulador.config import Capacitor


def energy_j(cap: Capacitor, voltage_v: float) -> float:
    return 0.5 * cap.capacitance_f * voltage_v**2


def voltage_v(cap: Capacitor, stored_energy_j: float) -> float:
    return sqrt(2 * max(0, stored_energy_j) / cap.capacitance_f)


@dataclass(frozen=True)
class Exchange:
    energy_j: float
    bus_power_w: float
    loss_power_w: float


def exchange(cap: Capacitor, stored_energy_j: float, requested_bus_power_w: float,
             dt_s: float) -> Exchange:
    """Potencia positiva: descarga hacia el bus; negativa: carga desde el bus."""
    if not all(isfinite(v) for v in (stored_energy_j, requested_bus_power_w, dt_s)) or dt_s <= 0:
        raise ValueError("Paso positivo y valores finitos requeridos.")
    minimum, maximum = energy_j(cap, cap.minimum_voltage_v), energy_j(cap, cap.maximum_voltage_v)
    if not minimum - 1e-6 <= stored_energy_j <= maximum + 1e-6:
        raise ValueError("Energía del banco fuera de límites.")
    stored_energy_j = min(maximum, max(minimum, stored_energy_j))
    if requested_bus_power_w >= 0:
        power = min(requested_bus_power_w, cap.max_discharge_power_w,
                    (stored_energy_j - minimum) * cap.discharge_efficiency / dt_s)
        removed_w = power / cap.discharge_efficiency
        return Exchange(max(minimum, stored_energy_j - removed_w * dt_s), power, removed_w - power)
    power = min(-requested_bus_power_w, cap.max_charge_power_w,
                (maximum - stored_energy_j) / cap.charge_efficiency / dt_s)
    stored_w = power * cap.charge_efficiency
    return Exchange(min(maximum, stored_energy_j + stored_w * dt_s), -power, power - stored_w)
