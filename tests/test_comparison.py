from simulador.comparison import compare
from simulador.route import Point


def test_sensitivity_preserves_baseline_and_changes_one_factor(config):
    original = config.to_dict()
    rows = compare(config, [Point(0, 30, 10), Point(100, 30, 0)])
    assert len(rows) == 7
    assert config.to_dict() == original
    by_name = {row["case"]: row for row in rows}
    assert by_name["Masa +20%"]["requested_energy_wh"] > by_name["Base"]["requested_energy_wh"]
    assert by_name["Potencia neta PEM +20%"]["unserved_energy_wh"] <= by_name["Base"]["unserved_energy_wh"]
