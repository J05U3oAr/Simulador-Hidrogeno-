from dataclasses import replace

import pytest

from simulador.protection import Fault
from simulador.route import Point
from simulador.simulation import simulate
from simulador.visualization import energy_diagram, series_table, storage_levels, summary_table


def test_storage_uses_energy_and_hydrogen_above_reserve(config):
    result = simulate(config, [Point(0, 20, 0), Point(2, 20, 0)])
    row = dict(result.rows[0], tank_pressure_bar_abs=105, capacitor_voltage_v=39)
    hydrogen, bank = storage_levels(result, row)
    assert hydrogen == pytest.approx(0.5)
    assert bank == pytest.approx((39**2 - 30**2) / (48**2 - 30**2))
    assert storage_levels(result, dict(row, tank_pressure_bar_abs=0, capacitor_voltage_v=0)) == (0, 0)


def test_diagram_shows_charge_discharge_and_isolation(config):
    route = [Point(0, 20, 0), Point(3, 20, 0)]
    charging = simulate(config, route)
    diagram = energy_diagram(charging, charging.rows[0])
    assert "Cargando desde el bus" in diagram
    assert 'marker-start="url(#bank-start)"' in diagram
    low_power = replace(config, fuel_cell=replace(config.fuel_cell, gross_power_w=100))
    discharging = simulate(low_power, route)
    diagram = energy_diagram(discharging, discharging.rows[0])
    assert "Descargando al bus" in diagram
    assert 'marker-end="url(#bank-end)"' in diagram
    stopped = simulate(config, route, fault=Fault("emergency_stop", 0))
    diagram = energy_diagram(stopped, stopped.rows[-1])
    assert "Bus aislado" in diagram
    assert "Sin intercambio" in diagram
    assert 'marker-end="url(#pem-end)"' not in diagram


def test_tables_keep_units_filter_actual_times_and_convert_grams(config):
    result = simulate(config, [Point(0, 20, 0), Point(3, 20, 0)],
                      fault=Fault("emergency_stop", 1))
    table = series_table(result, "Potencia", 1, 1.5)
    assert table["Tiempo [s]"].tolist() == [1, 1.5]
    assert table["Déficit [W]"].tolist() == [r["unserved_bus_power_w"] for r in result.rows[:2]]
    assert series_table(result, "Almacenamiento", 1.1, 1.2).empty
    summary = summary_table(result).set_index("Métrica")
    assert summary.loc["Hidrógeno consumido", "Valor"] == result.summary["hydrogen_used_kg"] * 1000
    assert summary.loc["Hidrógeno consumido", "Unidad"] == "g"
