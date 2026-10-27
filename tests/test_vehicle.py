from dataclasses import replace

import pytest

from simulador.config import Vehicle
from simulador.vehicle import mechanical_demand


def test_rest_has_no_power_demand():
    assert mechanical_demand(Vehicle(), 0).mechanical_power_w == 0


def test_drag_power_scales_with_speed_cubed():
    vehicle = replace(Vehicle(), rolling_coefficient=0)
    assert mechanical_demand(vehicle, 20).mechanical_power_w == pytest.approx(
        8 * mechanical_demand(vehicle, 10).mechanical_power_w)


def test_acceleration_energy_matches_kinetic_energy():
    vehicle = replace(Vehicle(), rolling_coefficient=0, drag_coefficient=0)
    # Aceleración constante 0 -> 10 m/s en 10 s: potencia en el punto medio.
    energy = mechanical_demand(vehicle, 5, 1).mechanical_power_w * 10
    assert energy == pytest.approx(0.5 * vehicle.mass_kg * vehicle.rotational_mass_factor * 10**2)


def test_downhill_can_require_braking():
    assert mechanical_demand(Vehicle(), 10, grade_percent=-15).mechanical_power_w < 0
