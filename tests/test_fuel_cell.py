import pytest

from simulador.config import FuelCell
from simulador.fuel_cell import generate


def test_pem_energy_and_auxiliary_balance():
    cell = FuelCell()
    result = generate(cell, 5000)
    assert result.gross_power_w == 1000
    assert result.net_power_w == 940
    chemical = result.hydrogen_kg_s * cell.hydrogen_lhv_j_kg
    assert chemical == pytest.approx(result.gross_power_w + result.waste_heat_w)


def test_disabled_cell_uses_no_hydrogen():
    assert generate(FuelCell(), 100, enabled=False).hydrogen_kg_s == 0
