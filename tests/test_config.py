from copy import deepcopy
import json

import pytest

from conftest import ROOT
from simulador.config import config_from_dict


@pytest.mark.parametrize("section,key,value", [
    ("motor", "efficiency", 0), ("motor", "efficiency", 1.1),
    ("vehicle", "mass_kg", float("nan")), ("vehicle", "mass_kg", True),
    ("tank", "compressibility_factor", 0), ("tank", "temperature_k", 0),
    ("capacitor", "initial_voltage_v", 100), ("protection", "shutdown_delay_s", -1),
])
def test_invalid_physical_parameters_are_rejected(section, key, value):
    data = json.loads((ROOT / "data/example.json").read_text(encoding="utf-8"))
    data["parameters"][section][key] = value
    with pytest.raises(ValueError):
        config_from_dict(data)


def test_missing_provenance_is_rejected():
    data = json.loads((ROOT / "data/example.json").read_text(encoding="utf-8"))
    invalid = deepcopy(data)
    del invalid["provenance"]["vehicle.mass_kg"]
    with pytest.raises(ValueError):
        config_from_dict(invalid)


def test_missing_parameter_cannot_silently_use_default():
    data = json.loads((ROOT / "data/example.json").read_text(encoding="utf-8"))
    del data["parameters"]["tank"]["volume_l"]
    with pytest.raises(ValueError):
        config_from_dict(data)


def test_mismatched_units_cannot_silently_change_interpretation():
    data = json.loads((ROOT / "data/example.json").read_text(encoding="utf-8"))
    data["provenance"]["vehicle.mass_kg"]["unit"] = "lb"
    with pytest.raises(ValueError, match="unidad"):
        config_from_dict(data)
