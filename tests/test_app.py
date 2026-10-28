from streamlit.testing.v1 import AppTest

from conftest import ROOT


def test_app_runs_default_scenario_and_reports_bad_parameters():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    assert len(app.metric) == 3
    assert app.success
    app.number_input[1].set_value(10)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    assert app.error
    assert len(app.metric) == 0


def test_comparison_uses_last_executed_scenario():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    next(button for button in app.button if button.label == "Comparar configuraciones").click().run()
    assert not app.exception
    assert len(app.session_state["comparison"]) == 7
