import pytest

from simulador.capacitor import energy_j, exchange, voltage_v
from simulador.config import Capacitor


def test_full_discharge_obeys_energy_balance_and_minimum_voltage():
    cap = Capacitor()
    initial = energy_j(cap, cap.initial_voltage_v)
    result = exchange(cap, initial, 1e9, 1e4)
    assert voltage_v(cap, result.energy_j) == pytest.approx(cap.minimum_voltage_v)
    assert initial - result.energy_j == pytest.approx((result.bus_power_w + result.loss_power_w) * 1e4)


def test_charge_never_overfills_and_accounts_for_losses():
    cap = Capacitor()
    initial = energy_j(cap, cap.initial_voltage_v)
    result = exchange(cap, initial, -1e9, 1e4)
    assert voltage_v(cap, result.energy_j) == pytest.approx(cap.maximum_voltage_v)
    assert result.energy_j - initial == pytest.approx((-result.bus_power_w - result.loss_power_w) * 1e4)
