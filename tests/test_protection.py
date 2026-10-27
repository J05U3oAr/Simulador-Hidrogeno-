import pytest

from simulador.protection import Fault
from simulador.route import Point
from simulador.simulation import simulate


def test_emergency_stop_is_exact_even_between_regular_steps(config):
    result = simulate(config, [Point(0, 20, 0), Point(10, 20, 0)], 2,
                      Fault("emergency_stop", 2.25))
    shutdown_at = 2.25 + config.protection.shutdown_delay_s
    assert any(row["time_s"] == shutdown_at for row in result.rows)
    after = [row for row in result.rows if row["time_s"] > shutdown_at]
    assert all(row["state"] == "apagado" for row in after)
    assert all(row["fuel_cell_bus_power_w"] == row["capacitor_bus_power_w"] == 0 for row in after)
    assert len({row["hydrogen_used_kg"] for row in after}) == 1
    assert not result.summary["target_feasible_in_model"]


def test_hydrogen_alarm_includes_detection_delay(config):
    result = simulate(config, [Point(0, 0, 0), Point(10, 0, 0)], fault=Fault("hydrogen_alarm", 2))
    shutdown = next(e for e in result.events if e["code"] == "shutdown")
    assert shutdown["time_s"] == pytest.approx(2 + config.protection.detection_delay_s + config.protection.shutdown_delay_s)


def test_fault_outside_route_is_rejected(config):
    with pytest.raises(ValueError):
        simulate(config, [Point(0, 0, 0), Point(1, 0, 0)], fault=Fault("emergency_stop", 2))
