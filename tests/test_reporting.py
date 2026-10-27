import csv
import json

from simulador.reporting import export_result
from simulador.route import Point
from simulador.simulation import simulate


def test_export_includes_inputs_units_events_and_readable_image(config, tmp_path):
    from PIL import Image
    result = simulate(config, [Point(0, 20, 0), Point(3, 20, 0)])
    export_result(result, tmp_path, {"test": "provenance"})
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert report["inputs"]["parameters"] == config.to_dict()
    assert report["provenance"] == {"test": "provenance"}
    with (tmp_path / "timeseries.csv").open(encoding="utf-8-sig", newline="") as file:
        assert len(list(csv.DictReader(file))) == 3
    with Image.open(tmp_path / "plots.png") as image:
        image.verify()
    assert "time_s,code,severity,detail" in (tmp_path / "events.csv").read_text(encoding="utf-8-sig")
