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


def test_visual_navigation_tables_and_reset_on_new_run():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert [tab.label for tab in app.tabs][:2] == ["Simulador visual", "Métricas y tablas"]
    app.selectbox(key="visual_stride").set_value(5).run()
    app.button(key="visual_next").click().run()
    assert app.session_state["visual_index"] == 5
    app.button(key="visual_previous").click().run()
    assert app.session_state["visual_index"] == 0
    app.slider(key="visual_index").set_value(20).run()
    next(box for box in app.selectbox if box.label == "Variables de la tabla").set_value("Potencia").run()
    app.slider(key="table_time_range").set_value((10.0, 20.0)).run()
    assert any("Déficit [W]" in table.value.columns and len(table.value) == 11 for table in app.dataframe)
    next(box for box in app.selectbox if box.label == "Recorrido").set_value("Velocidad constante")
    next(field for field in app.number_input if field.label == "Duración a velocidad constante [s]").set_value(1)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    assert app.session_state["visual_index"] == 0
    assert app.button(key="visual_next").disabled
    assert not any(slider.key == "table_time_range" for slider in app.slider)
    app.toggle(key="visual_playing").set_value(True).run()
    assert not app.exception
    assert app.session_state["visual_playing"] is False


def test_playback_advances_pauses_and_stops_at_end():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(box for box in app.selectbox if box.label == "Recorrido").set_value("Velocidad constante")
    next(field for field in app.number_input if field.label == "Duración a velocidad constante [s]").set_value(3)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    original_rows = app.session_state["simulation"][0].rows.copy()
    app.toggle(key="visual_playing").set_value(True).run()
    assert app.session_state["visual_index"] == 0
    assert app.slider(key="visual_index").disabled
    app.run()
    assert app.session_state["visual_index"] == 1
    app.toggle(key="visual_playing").set_value(False).run()
    assert app.session_state["visual_index"] == 1
    app.toggle(key="visual_playing").set_value(True).run()
    app.run()
    assert not app.exception
    assert app.session_state["visual_index"] == 2
    assert app.session_state["visual_playing"] is False
    assert app.session_state["simulation"][0].rows == original_rows
    app.button(key="visual_restart").click().run()
    assert app.session_state["visual_index"] == 0
