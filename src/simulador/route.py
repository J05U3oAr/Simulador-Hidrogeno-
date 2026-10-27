"""Recorridos: velocidad lineal entre puntos; pendiente constante por segmento."""

import csv
from dataclasses import dataclass
from math import ceil, isfinite
from pathlib import Path


@dataclass(frozen=True)
class Point:
    time_s: float
    speed_kmh: float
    grade_percent: float


@dataclass(frozen=True)
class Interval:
    start_s: float
    end_s: float
    speed_m_s: float
    end_speed_m_s: float
    acceleration_m_s2: float
    grade_percent: float

    @property
    def dt_s(self):
        return self.end_s - self.start_s


def validate_route(points: list[Point]):
    if len(points) < 2 or points[0].time_s != 0:
        raise ValueError("El recorrido necesita al menos dos puntos y debe comenzar en t=0.")
    previous = -1
    for point in points:
        if not all(isfinite(x) for x in (point.time_s, point.speed_kmh, point.grade_percent)):
            raise ValueError("El recorrido contiene valores no finitos.")
        if point.time_s <= previous or point.speed_kmh < 0:
            raise ValueError("Los tiempos deben ser crecientes y las velocidades no negativas.")
        previous = point.time_s


def load_route(path: str | Path) -> list[Point]:
    with Path(path).open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != ["time_s", "speed_kmh", "grade_percent"]:
            raise ValueError("Columnas requeridas: time_s,speed_kmh,grade_percent (en ese orden).")
        try:
            points = [Point(**{key: float(value) for key, value in row.items()}) for row in reader]
        except (TypeError, ValueError) as exc:
            raise ValueError("El recorrido debe contener tres valores numéricos por fila.") from exc
    validate_route(points)
    return points


def intervals(points: list[Point], max_step_s: float = 1, boundaries=()):
    validate_route(points)
    if not isfinite(max_step_s) or max_step_s <= 0:
        raise ValueError("El paso temporal debe ser positivo y finito.")
    count = sum(ceil((b.time_s - a.time_s) / max_step_s) for a, b in zip(points, points[1:]))
    if count + len(boundaries) > 200_000:
        raise ValueError("Demasiados pasos; aumente el paso temporal o reduzca el recorrido.")
    for a, b in zip(points, points[1:]):
        duration = b.time_s - a.time_s
        n = ceil(duration / max_step_s)
        times = {a.time_s + duration * i / n for i in range(n + 1)}
        times.update(t for t in boundaries if a.time_s < t < b.time_s)
        times = sorted(times)
        start_v = a.speed_kmh / 3.6
        acceleration = (b.speed_kmh / 3.6 - start_v) / duration
        for start, end in zip(times, times[1:]):
            yield Interval(start, end, start_v + acceleration * ((start + end) / 2 - a.time_s),
                           start_v + acceleration * (end - a.time_s), acceleration, a.grade_percent)
