"""Exportaciones reproducibles y gráficas sin depender de una pantalla."""

import csv
from io import BytesIO, StringIO
import json
from pathlib import Path

from matplotlib.figure import Figure

from simulador.simulation import Result


def csv_text(rows: list[dict], columns: list[str] | None = None) -> str:
    output = StringIO(newline="")
    names = columns or (list(rows[0]) if rows else [])
    writer = csv.DictWriter(output, fieldnames=names)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def plot_png(result: Result) -> bytes:
    figure = Figure(figsize=(11, 10), layout="constrained")
    axes = figure.subplots(4, 1, sharex=True)
    times = [row["time_s"] for row in result.rows]
    for key, label in [("requested_bus_power_w", "Demanda"), ("fuel_cell_bus_power_w", "PEM"),
                       ("capacitor_bus_power_w", "Banco (+ descarga)"), ("unserved_bus_power_w", "Déficit")]:
        axes[0].plot(times, [r[key] for r in result.rows], label=label)
    axes[0].set_ylabel("Potencia [W]")
    axes[0].legend(loc="upper right", fontsize=8)
    for axis, key, label in zip(axes[1:],
            ["capacitor_voltage_v", "hydrogen_used_kg", "target_speed_kmh"],
            ["Tensión banco [V]", "H₂ consumido [kg]", "Velocidad objetivo [km/h]"]):
        axis.plot(times, [r[key] for r in result.rows], color="#2563EB")
        axis.set_ylabel(label)
    for axis in axes:
        axis.grid(alpha=0.2)
    axes[-1].set_xlabel("Tiempo [s]")
    figure.suptitle("Simulación preliminar · potencias promedio por intervalo")
    output = BytesIO()
    figure.savefig(output, format="png", dpi=140)
    return output.getvalue()


def export_result(result: Result, directory: str | Path, provenance: dict) -> Path:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "timeseries.csv").write_text(csv_text(result.rows), encoding="utf-8-sig")
    (directory / "events.csv").write_text(csv_text(result.events,
        ["time_s", "code", "severity", "detail"]), encoding="utf-8-sig")
    report = {"model_version": "0.1.0", "summary": result.summary,
              "inputs": result.inputs, "provenance": provenance,
              "limitations": "Modelo cuasiestático de recorrido prescrito con datos de ejemplo; no certifica seguridad ni velocidad alcanzable."}
    (directory / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                                     allow_nan=False) + "\n", encoding="utf-8")
    (directory / "plots.png").write_bytes(plot_png(result))
    return directory
