"""Conversión mecánica/eléctrica de tracción, sin regeneración."""

from dataclasses import dataclass

from simulador.config import Motor


@dataclass(frozen=True)
class MotorDemand:
    requested_electrical_power_w: float
    accepted_electrical_power_w: float
    unserved_mechanical_power_w: float
    braking_power_w: float


def electrical_demand(motor: Motor, mechanical_power_w: float) -> MotorDemand:
    efficiency = motor.efficiency * motor.controller_efficiency
    traction = max(0.0, mechanical_power_w)
    accepted = min(traction, motor.max_mechanical_power_w)
    return MotorDemand(traction / efficiency, accepted / efficiency,
                       traction - accepted, max(0.0, -mechanical_power_w))
