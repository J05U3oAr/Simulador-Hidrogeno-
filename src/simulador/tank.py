"""Inventario isotérmico pV = Z m R T con Z constante configurable.

No resuelve el regulador, la termodinámica de descarga ni la dispersión de fugas.
"""

from math import isfinite

from simulador.config import Tank

HYDROGEN_R_J_KG_K = 4124.2


def mass_at_pressure(tank: Tank, pressure_bar_abs: float) -> float:
    return pressure_bar_abs * 1e5 * tank.volume_l / 1000 / (
        tank.compressibility_factor * HYDROGEN_R_J_KG_K * tank.temperature_k)


def pressure_at_mass(tank: Tank, mass_kg: float) -> float:
    return mass_kg * tank.compressibility_factor * HYDROGEN_R_J_KG_K * tank.temperature_k / (
        tank.volume_l / 1000) / 1e5


def withdraw(tank: Tank, mass_kg: float, requested_kg: float) -> tuple[float, float]:
    """Devuelve masa final y retirada efectiva; conserva la reserva de presión mínima."""
    if not all(isfinite(v) and v >= 0 for v in (mass_kg, requested_kg)):
        raise ValueError("La masa y la retirada deben ser finitas y no negativas.")
    available = max(0, mass_kg - mass_at_pressure(tank, tank.minimum_pressure_bar_abs))
    used = min(requested_kg, available)
    return mass_kg - used, used
