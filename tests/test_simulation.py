from dataclasses import replace

import pytest

from simulador.route import Point, intervals
from simulador.simulation import simulate


def test_interval_distance_and_partial_last_step():
    steps = list(intervals([Point(0, 0, 0), Point(10.3, 36, 0)], 1))
    assert sum(s.dt_s for s in steps) == pytest.approx(10.3)
    assert sum(s.speed_m_s * s.dt_s for s in steps) == pytest.approx(51.5)


def test_cruise_is_feasible_and_has_balanced_power(config):
    result = simulate(config, [Point(0, 20, 0), Point(60, 20, 0)])
    assert result.summary["target_feasible_in_model"]
    assert result.summary["distance_target_km"] == pytest.approx(1 / 3)
    assert result.summary["max_balance_error_w"] < 1e-9


def test_motor_limit_marks_target_infeasible(config):
    limited = replace(config, motor=replace(config.motor, max_mechanical_power_w=10))
    result = simulate(limited, [Point(0, 50, 10), Point(5, 50, 0)])
    assert not result.summary["target_feasible_in_model"]
    assert result.summary["unserved_energy_wh"] > 0


def test_time_refinement_converges_for_acceleration(config):
    route = [Point(0, 0, 0), Point(30, 36, 0), Point(60, 36, 0)]
    coarse = simulate(config, route, 1).summary["requested_energy_wh"]
    fine = simulate(config, route, 0.5).summary["requested_energy_wh"]
    finer = simulate(config, route, 0.25).summary["requested_energy_wh"]
    assert abs(finer - fine) < abs(fine - coarse)
    assert finer == pytest.approx(fine, rel=1e-4)


@pytest.mark.parametrize("points", [[], [Point(1, 0, 0), Point(2, 0, 0)],
    [Point(0, 0, 0), Point(0, 1, 0)], [Point(0, 0, 0), Point(1, float('nan'), 0)]])
def test_invalid_routes_are_rejected(points):
    with pytest.raises(ValueError):
        list(intervals(points))
