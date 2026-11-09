from streamlit.testing.v1 import AppTest

from conftest import ROOT


def route_app():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.radio(key="workspace").set_value("Recorrido y métricas").run()
    return app


def test_interactive_lab_is_the_default_workspace():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.radio(key="workspace").value == "Laboratorio interactivo"
    assert "Laboratorio del cilindro" in app.get("iframe")[0].proto.srcdoc
    assert not app.sidebar.number_input


def test_app_runs_default_scenario_and_reports_bad_parameters():
    app = route_app()
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
    app = route_app()
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    next(button for button in app.button if button.label == "Comparar configuraciones").click().run()
    assert not app.exception
    assert len(app.session_state["comparison"]) == 7


def test_visual_navigation_tables_and_reset_on_new_run():
    app = route_app()
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
    app.slider(key="visual_index").set_value(1).run()
    assert app.button(key="visual_next").disabled
    assert not any(slider.key == "table_time_range" for slider in app.slider)
    app.toggle(key="visual_playing").set_value(True).run()
    assert not app.exception
    assert app.session_state["visual_playing"] is False


def test_playback_advances_pauses_and_stops_at_end():
    app = route_app()
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
    app.run()
    assert not app.exception
    assert app.session_state["visual_index"] == 3
    assert app.session_state["visual_playing"] is False
    assert app.session_state["simulation"][0].rows == original_rows
    app.button(key="visual_restart").click().run()
    assert app.session_state["visual_index"] == 0


def test_cylinder_inputs_drive_scene_and_are_saved_with_provenance():
    app = route_app()
    assert any("Cilindro de hidrógeno animado" in element.proto.body for element in app.get("html"))
    app.number_input(key="tank_volume").set_value(12)
    app.number_input(key="tank_pressure").set_value(150)
    app.number_input(key="tank_reserve").set_value(15)
    app.number_input(key="tank_temperature").set_value(40)
    app.number_input(key="cylinder_pressure_limit").set_value(200)
    app.number_input(key="cylinder_temperature_min").set_value(10)
    app.number_input(key="cylinder_temperature_max").set_value(50)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    result, provenance = app.session_state["simulation"]
    tank = result.inputs["parameters"]["tank"]
    assert tank["temperature_k"] == 313.15
    assert tank["volume_l"] == 12
    assert tank["initial_pressure_bar_abs"] == 150
    assert tank["minimum_pressure_bar_abs"] == 15
    assert provenance["tank.temperature_k"]["unit"] == "K"
    assert provenance["tank.temperature_k"]["source"].startswith("Valor introducido")
    assert result.inputs["cylinder_reference"]["maximum_pressure_bar_abs"] == 200
    assert any('data-state="within"' in element.proto.body and "150.00 bar" in element.proto.body for element in app.get("html"))
    app.number_input(key="tank_temperature").set_value(60)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    assert any('data-state="outside"' in element.proto.body for element in app.get("html"))
    app.number_input(key="cylinder_temperature_min").set_value(70)
    next(button for button in app.button if button.label == "Ejecutar simulación").click().run()
    assert not app.exception
    assert any("mínima de referencia" in error.value for error in app.error)
