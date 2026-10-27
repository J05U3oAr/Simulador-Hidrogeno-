"""Dinámica longitudinal para un perfil de velocidad prescrito."""

from dataclasses import dataclass
from math import atan, cos, sin, isfinite

from simulador.config import Vehicle

GRAVITY_M_S2 = 9.80665


@dataclass(frozen=True)
class Demand:
    rolling_force_n: float
    drag_force_n: float
    grade_force_n: float
    acceleration_force_n: float
    mechanical_power_w: float


def mechanical_demand(vehicle: Vehicle, speed_m_s: float, acceleration_m_s2: float = 0,
                      grade_percent: float = 0) -> Demand:
    """Pendiente = 100 * subida / distancia horizontal; sin marcha atrás ni viento."""
    if not all(isfinite(x) for x in (speed_m_s, acceleration_m_s2, grade_percent)) or speed_m_s < 0:
        raise ValueError("Velocidad no negativa y condiciones finitas requeridas.")
    angle = atan(grade_percent / 100)
    rolling = vehicle.mass_kg * GRAVITY_M_S2 * vehicle.rolling_coefficient * cos(angle) if speed_m_s > 0 else 0
    drag = 0.5 * vehicle.air_density_kg_m3 * vehicle.drag_coefficient * vehicle.frontal_area_m2 * speed_m_s**2
    grade = vehicle.mass_kg * GRAVITY_M_S2 * sin(angle)
    inertia = vehicle.mass_kg * vehicle.rotational_mass_factor * acceleration_m_s2
    return Demand(rolling, drag, grade, inertia, (rolling + drag + grade + inertia) * speed_m_s)
