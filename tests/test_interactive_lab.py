import json
import shutil
import subprocess

import pytest

from conftest import ROOT
from simulador.interactive_lab import laboratory_html
from simulador.tank import mass_at_pressure


def test_lab_document_is_self_contained_and_contains_real_configuration(config):
    document = laboratory_html(config)
    assert "__LAB_" not in document
    assert '<html lang="es">' in document
    assert "requestAnimationFrame(frame)" in document
    assert 'src="http' not in document
    assert 'href="http' in document  # Únicamente el enlace de atribución a PhET.
    assert json.dumps(config.to_dict()["tank"]) in document


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js no instalado; solo se omiten las pruebas de JavaScript")
def test_lab_javascript_physics_and_event_bindings():
    result = subprocess.run([shutil.which("node"), "--test", str(ROOT / "tests/test_lab.cjs")],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js no instalado")
def test_lab_gas_inventory_matches_python_model(config):
    tank = config.to_dict()["tank"]
    script = "const p=require(process.argv[1]);const t=JSON.parse(process.argv[2]);console.log(JSON.stringify([10,150,200].map(v=>p.massAtPressure(t,v))))"
    result = subprocess.run([shutil.which("node"), "-e", script,
                             str(ROOT / "src/simulador/lab_assets/physics.js"), json.dumps(tank)],
                            capture_output=True, text=True, check=True, timeout=10)
    assert json.loads(result.stdout) == pytest.approx([mass_at_pressure(config.tank, value) for value in [10, 150, 200]])
