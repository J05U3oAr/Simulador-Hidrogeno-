"""Presentación de resultados calculados; no altera el modelo físico."""

from html import escape

import pandas as pd

from simulador.simulation import Result


SERIES_GROUPS = {
    "Recorrido": {
        "time_s": "Tiempo [s]", "dt_s": "Intervalo [s]", "state": "Estado",
        "target_speed_kmh": "Velocidad objetivo [km/h]",
        "grade_percent": "Pendiente [%]", "distance_target_km": "Distancia objetivo [km]",
    },
    "Potencia": {
        "time_s": "Tiempo [s]", "requested_bus_power_w": "Demanda [W]",
        "fuel_cell_bus_power_w": "PEM al bus [W]", "capacitor_bus_power_w": "Banco al bus [W]",
        "served_bus_power_w": "Potencia servida [W]", "unserved_bus_power_w": "Déficit [W]",
        "mechanical_power_w": "Demanda mecánica [W]", "braking_power_w": "Frenado [W]",
        "chemical_power_w": "Potencia química [W]", "loss_power_w": "Pérdidas aguas arriba [W]",
        "balance_error_w": "Error de balance [W]",
    },
    "Almacenamiento": {
        "time_s": "Tiempo [s]", "hydrogen_remaining_kg": "H₂ restante [kg]",
        "hydrogen_used_kg": "H₂ consumido [kg]", "tank_pressure_bar_abs": "Presión [bar absolutos]",
        "capacitor_voltage_v": "Tensión del banco [V]", "capacitor_energy_j": "Energía del banco [J]",
    },
}


def series_table(result: Result, group: str, start_s: float, end_s: float) -> pd.DataFrame:
    """Filtra por fin de intervalo y conserva números y unidades en las cabeceras."""
    columns = SERIES_GROUPS[group]
    frame = pd.DataFrame(result.rows)
    return frame.loc[frame.time_s.between(start_s, end_s), list(columns)].rename(columns=columns)


def summary_table(result: Result) -> pd.DataFrame:
    summary = result.summary
    values = [
        ("Duración", summary["duration_s"], "s"),
        ("Distancia objetivo", summary["distance_target_km"], "km"),
        ("Hidrógeno consumido", summary["hydrogen_used_kg"] * 1000, "g"),
        ("Energía solicitada", summary["requested_energy_wh"], "Wh"),
        ("Energía no cubierta", summary["unserved_energy_wh"], "Wh"),
        ("Pérdidas aguas arriba del bus", summary["upstream_losses_wh"], "Wh"),
        ("Tensión mínima del banco", summary["minimum_capacitor_voltage_v"], "V"),
        ("Error máximo de balance", summary["max_balance_error_w"], "W"),
        ("Eventos registrados", summary["event_count"], "eventos"),
    ]
    return pd.DataFrame(values, columns=["Métrica", "Valor", "Unidad"])


def storage_levels(result: Result, row: dict) -> tuple[float, float]:
    """Fracciones utilizables: H₂ sobre reserva inicial y banco según energía V²."""
    tank = result.inputs["parameters"]["tank"]
    cap = result.inputs["parameters"]["capacitor"]
    hydrogen = ((row["tank_pressure_bar_abs"] - tank["minimum_pressure_bar_abs"])
                / (tank["initial_pressure_bar_abs"] - tank["minimum_pressure_bar_abs"]))
    bank = ((row["capacitor_voltage_v"] ** 2 - cap["minimum_voltage_v"] ** 2)
            / (cap["maximum_voltage_v"] ** 2 - cap["minimum_voltage_v"] ** 2))
    return tuple(max(0.0, min(1.0, value)) for value in (hydrogen, bank))


def energy_diagram(result: Result, row: dict) -> str:
    """SVG adaptable con flechas según la dirección real del intercambio en el bus."""
    bank = row["capacitor_bus_power_w"]
    bank_mode = "Descargando al bus" if bank > 1e-6 else "Cargando desde el bus" if bank < -1e-6 else "Sin intercambio"
    state = "Bus aislado" if row["state"] == "apagado" else "Déficit de potencia" if row["unserved_bus_power_w"] > 1e-6 else "Demanda cubierta"
    fc_active = row["fuel_cell_bus_power_w"] > 1e-6
    bank_active = abs(bank) > 1e-6
    load_active = row["served_bus_power_w"] > 1e-6
    hydrogen, capacitor = storage_levels(result, row)

    def arrow(path: str, active: bool, color: str, reverse: bool = False) -> str:
        marker = 'marker-start="url(#bank-start)"' if reverse else f'marker-end="url(#{color}-end)"'
        return (f'<path d="{path}" class="flow {color if active else "idle"}" '
                f'{marker if active else ""}/>')

    return f"""
<section class="energy-view">
<style>
.energy-view {{ --ink:#1e293b; --muted:#475569; --line:#cbd5e1;
  --pem:#1e40af; --bank:#0f766e; --load:#6d28d9;
  container-type:inline-size; background:#fff; color:var(--ink); border:1px solid var(--line); border-radius:16px; padding:16px; }}
.energy-view svg {{ width:100%; height:auto; display:block; font:16px system-ui,sans-serif; }}
.energy-view .node {{ fill:#f8fafc; stroke:var(--line); stroke-width:1.5; }}
.energy-view text {{ fill:var(--ink); }}
.energy-view .small {{ font-size:14px; fill:var(--muted); }}
.energy-view .value {{ font-size:23px; font-weight:700; }}
.energy-view .flow {{ fill:none; stroke-width:4; }}
.energy-view .pem {{ stroke:var(--pem); }}
.energy-view .bank {{ stroke:var(--bank); }}
.energy-view .load {{ stroke:var(--load); }}
.energy-view .idle {{ stroke:var(--line); stroke-dasharray:6 6; }}
.energy-view .track {{ fill:#e2e8f0; }}
.energy-view .status {{ margin:0 0 8px; font:600 16px system-ui,sans-serif; }}
.energy-view .mobile-diagram {{ display:none; font:16px/1.5 system-ui,sans-serif; }}
.energy-view .mobile-diagram p {{ padding:12px; border:1px solid var(--line); border-radius:8px; background:#f8fafc; }}
@container (max-width:719px) {{ .energy-view .desktop-diagram {{ display:none; }}
  .energy-view .mobile-diagram {{ display:block; }} }}
</style>
<p class="status">{escape(state)} · intervalo hasta {row['time_s']:.2f} s</p>
<svg class="desktop-diagram" viewBox="0 0 960 430" role="img" aria-labelledby="energy-title energy-desc">
<title id="energy-title">Flujo de energía del vehículo</title>
<desc id="energy-desc">Tanque de hidrógeno a celda PEM, PEM a bus y bus a motor y auxiliares.
Banco bidireccional: {bank_mode}. {state}. Las potencias son promedios del intervalo.</desc>
<defs>
  <marker id="pem-end" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#1e40af"/></marker>
  <marker id="bank-end" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#0f766e"/></marker>
  <marker id="bank-start" markerWidth="8" markerHeight="8" refX="0" refY="3" orient="auto"><path d="M6,0 L0,3 L6,6" fill="none" stroke="#0f766e"/></marker>
  <marker id="load-end" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#6d28d9"/></marker>
</defs>
<rect class="node" x="10" y="45" width="200" height="155" rx="16"/>
<text x="28" y="77">Tanque H₂</text>
<text class="value" x="28" y="112">{row['tank_pressure_bar_abs']:.1f} bar abs.</text>
<text class="small" x="28" y="140">{row['hydrogen_remaining_kg'] * 1000:.2f} g restantes</text>
<rect class="track" x="28" y="157" width="164" height="10" rx="5"/>
<rect fill="#1e40af" x="28" y="157" width="{164 * hydrogen:.2f}" height="10" rx="5"/>
<text class="small" x="28" y="189">{hydrogen:.0%} sobre reserva inicial</text>
{arrow('M210 115 H265', fc_active, 'pem')}
<rect class="node" x="265" y="45" width="200" height="155" rx="16"/>
<text x="283" y="77">Celda PEM + DC/DC</text>
<text class="value" x="283" y="112">{row['fuel_cell_bus_power_w']:.1f} W</text>
<text class="small" x="283" y="144">Aporte al bus eléctrico</text>
<text class="small" x="283" y="176">{'Generando' if fc_active else 'Sin generación'}</text>
{arrow('M465 115 H590', fc_active, 'pem')}
<rect x="590" y="65" width="12" height="270" rx="6" fill="#475569"/>
<text class="small" x="576" y="42">BUS</text>
{arrow('M602 115 H675', load_active, 'load')}
<rect class="node" x="675" y="45" width="270" height="155" rx="16"/>
<text x="693" y="77">Motor + auxiliares</text>
<text class="value" x="693" y="112">{row['requested_bus_power_w']:.1f} W solicitados</text>
<text class="small" x="693" y="144">{row['served_bus_power_w']:.1f} W servidos</text>
<text class="small" x="693" y="176">Déficit: {row['unserved_bus_power_w']:.1f} W</text>
<rect class="node" x="265" y="255" width="235" height="160" rx="16"/>
<text x="283" y="285">Supercapacitores</text>
<text class="value" x="283" y="320">{row['capacitor_voltage_v']:.2f} V · {abs(bank):.1f} W</text>
<text class="small" x="283" y="349">{bank_mode}</text>
<rect class="track" x="283" y="365" width="199" height="10" rx="5"/>
<rect fill="#0f766e" x="283" y="365" width="{199 * capacitor:.2f}" height="10" rx="5"/>
<text class="small" x="283" y="401">{capacitor:.0%} de energía utilizable</text>
{arrow('M500 335 H590', bank_active, 'bank', reverse=bank < 0)}
<path d="M705 335 L725 298 H830 L875 335 H910 V365 H695 V345 Z" fill="#dbeafe" stroke="#1e40af" stroke-width="2"/>
<path d="M737 306 H773 V332 H722 Z M782 306 H824 L853 332 H782 Z" fill="#fff"/>
<circle cx="738" cy="365" r="19" fill="#1e293b"/><circle cx="865" cy="365" r="19" fill="#1e293b"/>
<circle cx="738" cy="365" r="8" fill="#cbd5e1"/><circle cx="865" cy="365" r="8" fill="#cbd5e1"/>
<text class="small" x="695" y="413">Objetivo: {row['target_speed_kmh']:.1f} km/h · {row['grade_percent']:+.1f}%</text>
</svg>
<div class="mobile-diagram">
<p><strong>Tanque H₂ → PEM → Bus → Motor y auxiliares</strong></p>
<p>Tanque: {row['tank_pressure_bar_abs']:.1f} bar abs. · {hydrogen:.0%} sobre reserva inicial</p>
<p>PEM al bus: {row['fuel_cell_bus_power_w']:.1f} W</p>
<p>Banco {'→ Bus' if bank >= 0 else '← Bus'}: {abs(bank):.1f} W · {bank_mode}<br>
{row['capacitor_voltage_v']:.2f} V · {capacitor:.0%} de energía utilizable</p>
<p>Demanda: {row['requested_bus_power_w']:.1f} W · Servida: {row['served_bus_power_w']:.1f} W<br>
Déficit: {row['unserved_bus_power_w']:.1f} W</p>
<p>Velocidad objetivo: {row['target_speed_kmh']:.1f} km/h · Pendiente: {row['grade_percent']:+.1f}%</p>
</div>
</section>"""
