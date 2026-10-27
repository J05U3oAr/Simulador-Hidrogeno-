import pytest

from simulador.config import Tank
from simulador.tank import mass_at_pressure, pressure_at_mass, withdraw


def test_pressure_mass_roundtrip_and_volume_scaling():
    tank = Tank()
    mass = mass_at_pressure(tank, 200)
    assert pressure_at_mass(tank, mass) == pytest.approx(200)
    assert mass_at_pressure(Tank(volume_l=12), 200) == pytest.approx(2 * mass)


def test_inventory_never_drops_below_reserve():
    tank = Tank()
    initial = mass_at_pressure(tank, 200)
    final, used = withdraw(tank, initial, 10)
    assert pressure_at_mass(tank, final) == pytest.approx(10)
    assert initial - final == pytest.approx(used)
