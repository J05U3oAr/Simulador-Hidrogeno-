from dataclasses import replace

import pytest

from simulador.cylinder import CylinderReference, cylinder_scene, cylinder_status, initial_cylinder_row


def test_missing_references_never_produce_a_green_status(config):
    tank = config.tank
    assert cylinder_status(tank, 200, CylinderReference()).code == "unknown"
    assert cylinder_status(tank, 200, CylinderReference(250)).code == "unknown"
    # Un límite conocido excedido se señala aunque falten otras referencias.
    assert cylinder_status(tank, 200, CylinderReference(150)).code == "outside"


def test_reference_comparison_includes_pressure_temperature_and_boundaries(config):
    tank = replace(config.tank, temperature_k=303.15)
    reference = CylinderReference(200, 10, 30)
    assert cylinder_status(tank, 200, reference).code == "within"
    assert cylinder_status(tank, 200.01, reference).code == "outside"
    assert cylinder_status(replace(tank, temperature_k=304.15), 150, reference).code == "outside"
    assert cylinder_status(replace(tank, temperature_k=282.15), 150, reference).code == "outside"
    assert cylinder_status(tank, tank.minimum_pressure_bar_abs, reference).code == "reserve"
    assert cylinder_status(tank, 150, reference, alarm=True).code == "alarm"
    assert cylinder_status(tank, 150, reference, isolated=True).code == "isolated"
    fractional_temperature = replace(tank, temperature_k=36.6 + 273.15)
    assert cylinder_status(fractional_temperature, 150, CylinderReference(200, 10, 36.6)).code == "within"


@pytest.mark.parametrize("reference", [
    CylinderReference(-1), CylinderReference(float("inf")), CylinderReference(True),
    CylinderReference(250, 50, 20), CylinderReference(250, -273.15, 20),
    CylinderReference(250, 0, float("nan")),
])
def test_invalid_references_are_rejected(reference):
    with pytest.raises(ValueError):
        reference.validate()


def test_scene_represents_flow_and_stops_it_on_isolation(config):
    row = dict(initial_cylinder_row(config.tank), hydrogen_flow_g_s=0.02)
    reference = CylinderReference(250, 0, 50)
    flowing = cylinder_scene(config.tank, row, reference)
    assert 'data-state="within"' in flowing
    assert 'class="supply active"' in flowing
    assert "prefers-reduced-motion:reduce" in flowing
    stopped = cylinder_scene(config.tank, row, reference, isolated=True, animate=False)
    assert 'class="cylinder-scene still"' in stopped
    assert 'class="supply inactive"' in stopped
    assert "Salida aislada" in stopped
    assert "no verifica el estado físico" in stopped
