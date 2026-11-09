"""Interfaz local. Ejecutar: python -m streamlit run app.py."""

from dataclasses import asdict, replace
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from simulador.config import load_config
from simulador.comparison import compare
from simulador.cylinder import CylinderReference
from simulador.dashboard import render_cylinder_preview, render_metrics, render_visual
from simulador.protection import Fault
from simulador.reporting import csv_text, plot_png
from simulador.route import Point, load_route
from simulador.simulation import simulate

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Simulador de hidrógeno", layout="wide")
st.title("Simulador de hidrógeno")
st.write("Explora la demanda del vehículo, el consumo de la celda PEM y el aporte del banco de supercapacitores.")
st.warning("Dimensionamiento preliminar con datos de ejemplo. Las estimaciones no validan la seguridad del vehículo.")

config, provenance = load_config(ROOT / "data/example.json")
with st.sidebar:
    st.header("Preparar escenario")
    with st.form("scenario"):
        route_name = st.selectbox("Recorrido", ["Urbano de ejemplo", "Velocidad constante", "CSV personalizado"])
        route_file = st.file_uploader("Recorrido CSV", type=["csv"], help="Columnas: time_s,speed_kmh,grade_percent. Tiempo inicial 0; velocidad interpolada entre puntos.")
        config_file = st.file_uploader("Configuración JSON (opcional)", type=["json"], help="Mismo formato que data/example.json. Los controles siguientes sustituyen algunos valores.")
        mass = st.number_input("Masa total [kg]", min_value=1.0, value=float(config.vehicle.mass_kg), step=5.0)
        power = st.number_input("Potencia bruta máxima PEM [W]", min_value=1.0, value=float(config.fuel_cell.gross_power_w), step=100.0)
        with st.expander("Datos del cilindro", expanded=True):
            st.caption("Deja un campo vacío para conservar el valor del JSON. La temperatura permanece constante durante la simulación.")
            tank_volume = st.number_input("Volumen del cilindro [L]", min_value=0.001, value=None, step=1.0,
                                          placeholder=f"Del JSON; ejemplo: {config.tank.volume_l:g} L", key="tank_volume")
            tank_pressure = st.number_input("Presión inicial del cilindro [bar absolutos]", min_value=0.001, value=None, step=10.0,
                                            placeholder=f"Del JSON; ejemplo: {config.tank.initial_pressure_bar_abs:g} bar", key="tank_pressure")
            tank_reserve = st.number_input("Presión de reserva [bar absolutos]", min_value=0.0, value=None, step=1.0,
                                           placeholder=f"Del JSON; ejemplo: {config.tank.minimum_pressure_bar_abs:g} bar", key="tank_reserve")
            tank_temperature = st.number_input("Temperatura del cilindro [°C]", min_value=-273.14, value=None, step=1.0,
                                               placeholder=f"Del JSON; ejemplo: {config.tank.temperature_k - 273.15:.2f} °C", key="tank_temperature")
        with st.expander("Límites de referencia del cilindro"):
            st.caption("Introduce las referencias de la ficha técnica en las unidades indicadas. Vacío = desconocido. Se comparan valores; no se evalúa integridad física ni se activa un apagado por estos límites.")
            pressure_limit = st.number_input("Presión máxima de referencia [bar absolutos]", min_value=0.001, value=None, step=10.0, key="cylinder_pressure_limit")
            temperature_min = st.number_input("Temperatura mínima de referencia [°C]", min_value=-273.14, value=None, step=1.0, key="cylinder_temperature_min")
            temperature_max = st.number_input("Temperatura máxima de referencia [°C]", min_value=-273.14, value=None, step=1.0, key="cylinder_temperature_max")
        grade = st.number_input("Pendiente para velocidad constante [%]", min_value=-30.0, max_value=30.0, value=0.0)
        speed = st.number_input("Velocidad constante [km/h]", min_value=0.0, max_value=150.0, value=20.0)
        duration = st.number_input("Duración a velocidad constante [s]", min_value=1.0, max_value=86400.0, value=600.0)
        step = st.number_input("Paso máximo [s]", min_value=0.05, max_value=10.0, value=1.0)
        fault_label = st.selectbox("Evento de prueba", ["Sin fallo", "Alarma de hidrógeno", "Parada de emergencia"])
        fault_time = st.number_input("Instante del evento [s]", min_value=0.0, value=60.0)
        submitted = st.form_submit_button("Ejecutar simulación", type="primary")

if submitted:
    try:
        if config_file is not None:
            # Lectura en memoria: no se guardan archivos subidos en el servidor.
            from simulador.config import config_from_dict
            config, provenance = config_from_dict(json.loads(config_file.getvalue()))
        tank_overrides = {key: value for key, value in {
            "volume_l": tank_volume, "initial_pressure_bar_abs": tank_pressure,
            "minimum_pressure_bar_abs": tank_reserve,
            "temperature_k": tank_temperature + 273.15 if tank_temperature is not None else None,
        }.items() if value is not None}
        config = replace(config, vehicle=replace(config.vehicle, mass_kg=mass),
                         fuel_cell=replace(config.fuel_cell, gross_power_w=power),
                         tank=replace(config.tank, **tank_overrides)).validate()
        cylinder_reference = CylinderReference(pressure_limit, temperature_min, temperature_max).validate()
        provenance = {key: dict(value) for key, value in provenance.items()}
        for key in ("vehicle.mass_kg", "fuel_cell.gross_power_w", *(f"tank.{name}" for name in tank_overrides)):
            provenance[key].update(status="supuesto", source="Valor introducido en la interfaz; confirmar con medición o ficha técnica.")
        if route_name == "Urbano de ejemplo":
            route = load_route(ROOT / "data/routes/urban.csv")
        elif route_name == "Velocidad constante":
            route = [Point(0, speed, grade), Point(duration, speed, grade)]
        else:
            if route_file is None:
                raise ValueError("Selecciona un archivo de recorrido CSV.")
            from simulador.route import route_from_text
            route = route_from_text(route_file.getvalue().decode("utf-8-sig"))
        kind = {"Sin fallo": "none", "Alarma de hidrógeno": "hydrogen_alarm",
                "Parada de emergencia": "emergency_stop"}[fault_label]
        fault = Fault(kind, fault_time if kind != "none" else 0)
        result = simulate(config, route, step, fault)
        result.inputs["cylinder_reference"] = asdict(cylinder_reference)
        st.session_state["simulation"] = (result, provenance)
        st.session_state.pop("comparison", None)
        st.session_state.pop("simulation_error", None)
        for key in ("visual_index", "visual_playing", "visual_next_index", "visual_finished", "table_time_range"):
            st.session_state.pop(key, None)
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        st.session_state["simulation_error"] = str(exc)
        st.session_state.pop("simulation", None)

if "simulation_error" in st.session_state:
    st.error(f"Revisa el escenario: {st.session_state['simulation_error']}")

if "simulation" not in st.session_state:
    if "simulation_error" not in st.session_state:
        render_cylinder_preview(config)
    st.info("Configura un escenario y pulsa «Ejecutar simulación» para ver los resultados.")
    st.caption("El CSV urbano incluye aceleraciones, paradas y pendientes. Velocidad constante supone que el vehículo ya está en movimiento.")
else:
    result, used_provenance = st.session_state["simulation"]
    st.caption("Resultados de la última ejecución. Pulsa «Ejecutar simulación» para aplicar cambios en el formulario.")
    summary = result.summary
    if summary["target_feasible_in_model"]:
        st.success("Demanda objetivo cubierta en este modelo y con estos supuestos.")
    else:
        st.error("El sistema no cubre toda la demanda objetivo. La distancia mostrada pertenece al recorrido solicitado.")
    metrics = st.columns(3)
    metrics[0].metric("Distancia objetivo [km]", f"{summary['distance_target_km']:.2f}")
    metrics[1].metric("Hidrógeno consumido [g]", f"{summary['hydrogen_used_kg'] * 1000:.2f}")
    metrics[2].metric("Energía no cubierta [Wh]", f"{summary['unserved_energy_wh']:.3f}")
    visual, metrics_tab, charts, events, inputs, sensitivity, downloads = st.tabs([
        "Simulador visual", "Métricas y tablas", "Energía y recorrido", "Eventos", "Datos usados", "Comparación", "Descargas"])
    frame = pd.DataFrame(result.rows).set_index("time_s")
    with visual:
        render_visual(result)
    with metrics_tab:
        render_metrics(result)
    with charts:
        st.subheader("Balance de potencia del bus [W]")
        st.caption("Banco: positivo al descargar, negativo al cargar. Potencias promedio por intervalo.")
        st.line_chart(frame[["requested_bus_power_w", "fuel_cell_bus_power_w", "capacitor_bus_power_w", "unserved_bus_power_w"]].rename(columns={
            "requested_bus_power_w": "Demanda", "fuel_cell_bus_power_w": "Celda PEM",
            "capacitor_bus_power_w": "Banco", "unserved_bus_power_w": "Déficit"}), x_label="Tiempo [s]", y_label="Potencia [W]")
        for key, title in [("capacitor_voltage_v", "Tensión del banco [V]"),
                           ("tank_pressure_bar_abs", "Presión aproximada del tanque [bar absolutos]"),
                           ("hydrogen_used_kg", "Hidrógeno consumido [kg]"),
                           ("target_speed_kmh", "Velocidad objetivo [km/h]")]:
            st.subheader(title)
            st.line_chart(frame[[key]], x_label="Tiempo [s]", y_label=title)
    with events:
        if result.events:
            st.dataframe(pd.DataFrame(result.events).rename(columns={"time_s": "Tiempo [s]", "code": "Evento", "severity": "Nivel", "detail": "Detalle"}), hide_index=True)
        else:
            st.info("No se registraron eventos en esta ejecución.")
        st.caption("La alarma es una señal lógica inyectada. No se calcula dispersión, concentración de gas ni cobertura del sensor.")
    with inputs:
        st.json(result.inputs)
        st.dataframe(pd.DataFrame.from_dict(used_provenance, orient="index").rename(columns={"unit": "Unidad", "status": "Estado", "source": "Fuente"}))
    with downloads:
        st.download_button("Descargar serie temporal CSV", csv_text(result.rows).encode("utf-8-sig"), "timeseries.csv", "text/csv")
        st.download_button("Descargar eventos CSV", csv_text(result.events, ["time_s", "code", "severity", "detail"]).encode("utf-8-sig"), "events.csv", "text/csv")
        report = {"summary": summary, "inputs": result.inputs, "provenance": used_provenance, "model_version": "0.1.0"}
        st.download_button("Descargar informe JSON", json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False), "report.json", "application/json")
        st.download_button("Descargar gráficas PNG", plot_png(result), "plots.png", "image/png")
    with sensitivity:
        st.write("Compara masa, potencia neta de la celda y capacitancia con variaciones de ±20%, cambiando un factor a la vez.")
        st.caption("Conserva el recorrido, los demás parámetros y el fallo de la última ejecución. No representa intervalos de confianza.")
        if st.button("Comparar configuraciones"):
            from simulador.config import config_from_dict
            saved_config, _ = config_from_dict({"parameters": result.inputs["parameters"], "provenance": used_provenance})
            saved_route = [Point(**point) for point in result.inputs["route"]]
            st.session_state["comparison"] = compare(saved_config, saved_route,
                result.inputs["max_step_s"], Fault(**result.inputs["fault"]))
        if "comparison" in st.session_state:
            comparison = st.session_state["comparison"]
            st.dataframe(pd.DataFrame(comparison), hide_index=True)
            st.download_button("Descargar comparación CSV", csv_text(comparison).encode("utf-8-sig"), "comparison.csv", "text/csv")
