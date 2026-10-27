import pytest

from simulador.capacitor import energy_j
from simulador.powertrain import dispatch
from simulador.tank import mass_at_pressure


@pytest.mark.parametrize("load", [0, 100, 1000, 6000])
def test_whole_system_energy_conservation(config, load):
    mass = mass_at_pressure(config.tank, config.tank.initial_pressure_bar_abs)
    initial = energy_j(config.capacitor, config.capacitor.initial_voltage_v)
    result = dispatch(config, load, mass, initial, 2)
    assert result.balance_error_w == pytest.approx(0, abs=1e-9)
    assert result.chemical_power_w * 2 + initial - result.capacitor_energy_j == pytest.approx(
        (result.served_power_w + result.loss_power_w) * 2)
    assert mass - result.hydrogen_mass_kg == pytest.approx(result.hydrogen_used_kg)


def test_empty_tank_and_depleted_bank_report_deficit(config):
    mass = mass_at_pressure(config.tank, config.tank.minimum_pressure_bar_abs)
    minimum = energy_j(config.capacitor, config.capacitor.minimum_voltage_v)
    result = dispatch(config, 2000, mass, minimum, 1)
    assert result.unserved_power_w == pytest.approx(2000)
    assert result.hydrogen_used_kg == 0
