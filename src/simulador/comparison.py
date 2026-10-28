"""Sensibilidad de un factor a la vez; no equivale a incertidumbre probabilística."""

from dataclasses import replace

from simulador.config import Config
from simulador.protection import Fault
from simulador.route import Point
from simulador.simulation import simulate


def compare(config: Config, route: list[Point], max_step_s: float = 1,
            fault: Fault | None = None) -> list[dict]:
    cases = [("Base", config)]
    for factor in (0.8, 1.2):
        change = f"{(factor - 1) * 100:+.0f}%"
        cases.append((f"Masa {change}", replace(config, vehicle=replace(config.vehicle,
                     mass_kg=config.vehicle.mass_kg * factor))))
        # Variar potencia neta conserva auxiliares y evita celdas inviables por construcción.
        gross = config.fuel_cell.auxiliary_power_w + (
            config.fuel_cell.gross_power_w - config.fuel_cell.auxiliary_power_w) * factor
        cases.append((f"Potencia neta PEM {change}", replace(config, fuel_cell=replace(config.fuel_cell,
                     gross_power_w=gross))))
        cases.append((f"Capacitancia {change}", replace(config, capacitor=replace(config.capacitor,
                     capacitance_f=config.capacitor.capacitance_f * factor))))
    return [{"case": name, **simulate(case, route, max_step_s, fault).summary}
            for name, case in cases]
