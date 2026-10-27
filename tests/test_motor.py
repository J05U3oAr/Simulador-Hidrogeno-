import pytest

from simulador.config import Motor
from simulador.motor import electrical_demand


def test_conversion_includes_both_losses():
    result = electrical_demand(Motor(), 855)
    assert result.accepted_electrical_power_w == pytest.approx(1000)


def test_motor_limit_and_braking_are_explicit():
    assert electrical_demand(Motor(), 4000).unserved_mechanical_power_w == 1000
    result = electrical_demand(Motor(), -100)
    assert result.accepted_electrical_power_w == 0
    assert result.braking_power_w == 100
