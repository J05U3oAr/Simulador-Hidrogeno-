"""Simulación cuasiestática de seguimiento de un recorrido prescrito."""

from dataclasses import dataclass

from simulador.capacitor import energy_j, voltage_v
from simulador.config import Config
from simulador.motor import electrical_demand
from simulador.powertrain import dispatch
from simulador.route import Point, intervals
from simulador.tank import mass_at_pressure, pressure_at_mass
from simulador.vehicle import mechanical_demand


@dataclass
class Result:
    rows: list[dict]
    events: list[dict]
    summary: dict


def simulate(config: Config, route: list[Point], max_step_s: float = 1) -> Result:
    config.validate()
    mass = mass_at_pressure(config.tank, config.tank.initial_pressure_bar_abs)
    initial_mass = mass
    stored = energy_j(config.capacitor, config.capacitor.initial_voltage_v)
    rows, events = [], []
    distance_m = unserved_j = demand_j = losses_j = 0.0
    for interval in intervals(route, max_step_s):
        dt = interval.dt_s
        mechanical = mechanical_demand(config.vehicle, interval.speed_m_s,
                                       interval.acceleration_m_s2, interval.grade_percent)
        motor = electrical_demand(config.motor, mechanical.mechanical_power_w)
        auxiliaries = config.bus.auxiliary_load_w / config.bus.auxiliary_converter_efficiency
        load = motor.accepted_electrical_power_w + auxiliaries
        requested = motor.requested_electrical_power_w + auxiliaries
        step = dispatch(config, load, mass, stored, dt)
        mass, stored = step.hydrogen_mass_kg, step.capacitor_energy_j
        missing = step.unserved_power_w + requested - load
        distance_m += interval.speed_m_s * dt
        demand_j += requested * dt
        unserved_j += missing * dt
        losses_j += step.loss_power_w * dt
        rows.append({
            "time_s": interval.end_s, "dt_s": dt,
            "target_speed_kmh": interval.end_speed_m_s * 3.6,
            "grade_percent": interval.grade_percent,
            "distance_target_km": distance_m / 1000,
            "mechanical_power_w": mechanical.mechanical_power_w,
            "braking_power_w": motor.braking_power_w,
            "requested_bus_power_w": requested,
            "fuel_cell_bus_power_w": step.fuel_cell_bus_power_w,
            "capacitor_bus_power_w": step.capacitor_bus_power_w,
            "served_bus_power_w": step.served_power_w,
            "unserved_bus_power_w": missing,
            "hydrogen_remaining_kg": mass,
            "hydrogen_used_kg": initial_mass - mass,
            "tank_pressure_bar_abs": pressure_at_mass(config.tank, mass),
            "capacitor_voltage_v": voltage_v(config.capacitor, stored),
            "capacitor_energy_j": stored,
            "chemical_power_w": step.chemical_power_w,
            "loss_power_w": step.loss_power_w,
            "balance_error_w": step.balance_error_w,
        })
    summary = {
        "duration_s": rows[-1]["time_s"], "distance_target_km": distance_m / 1000,
        "hydrogen_used_kg": initial_mass - mass,
        "requested_energy_wh": demand_j / 3600,
        "unserved_energy_wh": unserved_j / 3600,
        "upstream_losses_wh": losses_j / 3600,
        "target_feasible_in_model": unserved_j < 1e-6,
        "minimum_capacitor_voltage_v": min(config.capacitor.initial_voltage_v, *(r["capacitor_voltage_v"] for r in rows)),
        "max_balance_error_w": max(abs(r["balance_error_w"]) for r in rows),
    }
    return Result(rows, events, summary)
