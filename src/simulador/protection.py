"""Eventos lógicos de protección; sin modelo de concentración ni válvulas físicas."""

from dataclasses import dataclass
from math import isfinite

from simulador.config import Protection


@dataclass(frozen=True)
class Fault:
    kind: str = "none"
    at_s: float = 0

    def schedule(self, protection: Protection, duration_s: float) -> list[dict]:
        if self.kind not in {"none", "hydrogen_alarm", "emergency_stop"}:
            raise ValueError("Fallo desconocido.")
        if not isfinite(self.at_s) or not 0 <= self.at_s <= duration_s:
            raise ValueError("El instante del fallo debe estar dentro del recorrido.")
        if self.kind == "none":
            return []
        delay = protection.detection_delay_s if self.kind == "hydrogen_alarm" else 0
        detected_at = self.at_s + delay
        return [
            {"time_s": self.at_s, "code": "fault_injected", "severity": "info", "detail": self.kind},
            {"time_s": detected_at, "code": "alarm", "severity": "alarm", "detail": self.kind},
            {"time_s": detected_at + protection.shutdown_delay_s, "code": "shutdown",
             "severity": "alarm", "detail": "Aislamiento lógico de PEM y banco del bus."},
        ]
