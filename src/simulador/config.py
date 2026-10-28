"""Configuración explícita y validada; presiones en bar absolutos."""

from dataclasses import asdict, dataclass, fields
import json
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class Vehicle:
    mass_kg: float = 180
    rolling_coefficient: float = 0.012
    drag_coefficient: float = 0.35
    frontal_area_m2: float = 0.8
    air_density_kg_m3: float = 1.2
    rotational_mass_factor: float = 1.05


@dataclass(frozen=True)
class Motor:
    efficiency: float = 0.9
    controller_efficiency: float = 0.95
    max_mechanical_power_w: float = 3000


@dataclass(frozen=True)
class FuelCell:
    gross_power_w: float = 1000
    efficiency_lhv: float = 0.5
    auxiliary_power_w: float = 60
    hydrogen_lhv_j_kg: float = 120_000_000


@dataclass(frozen=True)
class Tank:
    volume_l: float = 6
    initial_pressure_bar_abs: float = 200
    minimum_pressure_bar_abs: float = 10
    temperature_k: float = 293.15
    compressibility_factor: float = 1.15


@dataclass(frozen=True)
class Capacitor:
    capacitance_f: float = 100
    minimum_voltage_v: float = 30
    maximum_voltage_v: float = 48
    initial_voltage_v: float = 45
    max_charge_power_w: float = 1000
    max_discharge_power_w: float = 3000
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95


@dataclass(frozen=True)
class Bus:
    fuel_cell_converter_efficiency: float = 0.95
    auxiliary_converter_efficiency: float = 0.9
    auxiliary_load_w: float = 30
    capacitor_recharge_power_w: float = 200


@dataclass(frozen=True)
class Protection:
    detection_delay_s: float = 1
    shutdown_delay_s: float = 0.5


@dataclass(frozen=True)
class Config:
    vehicle: Vehicle
    motor: Motor
    fuel_cell: FuelCell
    tank: Tank
    capacitor: Capacitor
    bus: Bus
    protection: Protection

    def validate(self):
        for section in fields(self):
            for field in fields(getattr(self, section.name)):
                value = getattr(getattr(self, section.name), field.name)
                name = f"{section.name}.{field.name}"
                if isinstance(value, bool) or not isinstance(value, (float, int)):
                    raise ValueError(f"{name}: se requiere un número.")
                if not isfinite(value) or value < 0:
                    raise ValueError(f"{name}: debe ser finito y no negativo.")
                if "efficiency" in field.name and not 0 < value <= 1:
                    raise ValueError(f"{name}: la eficiencia debe estar entre 0 y 1 (sin incluir 0).")
        positive = (
            self.vehicle.mass_kg, self.vehicle.frontal_area_m2,
            self.vehicle.air_density_kg_m3, self.motor.max_mechanical_power_w,
            self.fuel_cell.gross_power_w, self.fuel_cell.hydrogen_lhv_j_kg,
            self.tank.volume_l, self.tank.temperature_k, self.tank.compressibility_factor,
            self.capacitor.capacitance_f, self.capacitor.minimum_voltage_v,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("Masas, dimensiones, capacidades y constantes físicas deben ser positivas.")
        if self.vehicle.rotational_mass_factor < 1:
            raise ValueError("El factor de masa rotacional debe ser al menos 1.")
        if self.tank.initial_pressure_bar_abs <= self.tank.minimum_pressure_bar_abs:
            raise ValueError("La presión inicial debe superar la presión mínima del tanque.")
        cap = self.capacitor
        if not cap.minimum_voltage_v <= cap.initial_voltage_v <= cap.maximum_voltage_v:
            raise ValueError("La tensión inicial debe estar dentro del intervalo del banco.")
        if cap.minimum_voltage_v >= cap.maximum_voltage_v:
            raise ValueError("La tensión máxima debe superar la mínima del banco.")
        if self.fuel_cell.auxiliary_power_w >= self.fuel_cell.gross_power_w:
            raise ValueError("La celda debe poder alimentar sus propios auxiliares.")
        return self

    def to_dict(self):
        return asdict(self)


SECTIONS = {
    "vehicle": Vehicle, "motor": Motor, "fuel_cell": FuelCell, "tank": Tank,
    "capacitor": Capacitor, "bus": Bus, "protection": Protection,
}

UNIT_SUFFIXES = {
    "kg_m3": "kg/m^3", "j_kg": "J/kg", "bar_abs": "bar absoluto",
    "kg": "kg", "w": "W", "f": "F", "v": "V", "s": "s",
    "m2": "m^2", "l": "L", "k": "K",
}


def parameter_unit(name: str) -> str:
    for suffix in sorted(UNIT_SUFFIXES, key=len, reverse=True):
        if name.endswith("_" + suffix):
            return UNIT_SUFFIXES[suffix]
    return "adimensional"


def load_config(path: str | Path) -> tuple[Config, dict]:
    return config_from_dict(json.loads(Path(path).read_text(encoding="utf-8-sig")))


def config_from_dict(data: dict) -> tuple[Config, dict]:
    if not isinstance(data, dict):
        raise ValueError("La configuración debe ser un objeto JSON.")
    if set(data) != {"parameters", "provenance"}:
        raise ValueError("La configuración requiere parameters y provenance.")
    if not isinstance(data["parameters"], dict) or set(data["parameters"]) != set(SECTIONS):
        raise ValueError("Las secciones de parámetros no coinciden con el modelo.")
    if not isinstance(data["provenance"], dict):
        raise ValueError("provenance debe ser un objeto JSON.")
    for name, cls in SECTIONS.items():
        values = data["parameters"][name]
        if not isinstance(values, dict) or set(values) != {field.name for field in fields(cls)}:
            raise ValueError(f"{name}: proporcione todos los parámetros definidos en el ejemplo, sin claves adicionales.")
    try:
        config = Config(**{name: cls(**data["parameters"][name]) for name, cls in SECTIONS.items()})
    except TypeError as exc:
        raise ValueError(f"Parámetro desconocido: {exc}") from exc
    for section, cls in SECTIONS.items():
        for field in fields(cls):
            key = f"{section}.{field.name}"
            entry = data["provenance"].get(key, {})
            if not isinstance(entry, dict) or not all(isinstance(entry.get(item), str) and entry[item].strip() for item in ("unit", "status", "source")):
                raise ValueError(f"Falta unidad, estado o fuente de {key}.")
            if entry["status"] not in {"supuesto", "confirmado", "pendiente"}:
                raise ValueError(f"Estado de procedencia inválido: {key}.")
            if entry["unit"] != parameter_unit(field.name):
                raise ValueError(f"{key}: la unidad requerida es {parameter_unit(field.name)}; no se convierten unidades automáticamente.")
    return config.validate(), data["provenance"]
