"""Estado visual del cilindro frente a referencias explícitas del usuario.

No evalúa integridad estructural, certificación ni seguridad del recipiente.
"""

from dataclasses import dataclass
from html import escape
from math import cos, isfinite, pi, sin

from simulador.config import Tank
from simulador.tank import mass_at_pressure


@dataclass(frozen=True)
class CylinderReference:
    maximum_pressure_bar_abs: float | None = None
    minimum_temperature_c: float | None = None
    maximum_temperature_c: float | None = None

    def validate(self):
        for value in (self.maximum_pressure_bar_abs, self.minimum_temperature_c, self.maximum_temperature_c):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)):
                raise ValueError("Los límites de referencia del cilindro deben ser números finitos.")
        if self.maximum_pressure_bar_abs is not None and self.maximum_pressure_bar_abs <= 0:
            raise ValueError("La presión máxima de referencia debe ser positiva.")
        for value in (self.minimum_temperature_c, self.maximum_temperature_c):
            if value is not None and value <= -273.15:
                raise ValueError("La temperatura de referencia debe superar el cero absoluto.")
        if (self.minimum_temperature_c is not None and self.maximum_temperature_c is not None
                and self.minimum_temperature_c > self.maximum_temperature_c):
            raise ValueError("La temperatura mínima de referencia no puede superar la máxima.")
        return self


@dataclass(frozen=True)
class CylinderStatus:
    code: str
    label: str
    detail: str


def cylinder_status(tank: Tank, pressure: float, reference: CylinderReference,
                    alarm: bool = False, isolated: bool = False) -> CylinderStatus:
    reference.validate()
    outside = []
    temperature_c = tank.temperature_k - 273.15
    # Evita clasificar 36.6 °C como exceso por la conversión 36.6 + 273.15 - 273.15.
    tolerance = 1e-8
    if reference.maximum_pressure_bar_abs is not None and pressure > reference.maximum_pressure_bar_abs + tolerance:
        outside.append("La presión supera la máxima ingresada.")
    if reference.minimum_temperature_c is not None and temperature_c < reference.minimum_temperature_c - tolerance:
        outside.append("La temperatura está por debajo de la mínima ingresada.")
    if reference.maximum_temperature_c is not None and temperature_c > reference.maximum_temperature_c + tolerance:
        outside.append("La temperatura supera la máxima ingresada.")
    if outside:
        return CylinderStatus("outside", "Fuera de los límites ingresados", " ".join(outside))
    if alarm:
        return CylinderStatus("alarm", "Alarma simulada de H₂", "Se activó la señal lógica de alarma; no se calcula una fuga real.")
    if isolated:
        return CylinderStatus("isolated", "Suministro aislado", "La protección simulada aisló las fuentes del bus.")
    if pressure <= tank.minimum_pressure_bar_abs + 1e-8:
        return CylinderStatus("reserve", "Reserva alcanzada", "El modelo no extrae más hidrógeno por debajo de esta reserva.")
    limits = (reference.maximum_pressure_bar_abs, reference.minimum_temperature_c, reference.maximum_temperature_c)
    if all(value is not None for value in limits):
        return CylinderStatus("within", "Dentro de los límites ingresados", "Presión y temperatura dentro de las referencias proporcionadas.")
    if any(value is not None for value in limits):
        return CylinderStatus("unknown", "Referencias incompletas", "Completa presión máxima y temperaturas mínima y máxima para comparar ambas variables.")
    return CylinderStatus("unknown", "Sin límites de referencia", "Ingresa las referencias del cilindro para comparar presión y temperatura.")


def initial_cylinder_row(tank: Tank) -> dict:
    return {"time_s": 0.0, "tank_pressure_bar_abs": tank.initial_pressure_bar_abs,
            "hydrogen_remaining_kg": mass_at_pressure(tank, tank.initial_pressure_bar_abs),
            "hydrogen_flow_g_s": 0.0}


def cylinder_scene(tank: Tank, row: dict, reference: CylinderReference,
                   alarm: bool = False, isolated: bool = False, animate: bool = True) -> str:
    """Cilindro con corte ilustrativo, gas en todo el volumen y salida animada."""
    pressure = row["tank_pressure_bar_abs"]
    status = cylinder_status(tank, pressure, reference, alarm, isolated)
    colors = {"within": "#047857", "unknown": "#1e40af", "reserve": "#a16207",
              "outside": "#b91c1c", "alarm": "#b91c1c", "isolated": "#a16207"}
    color = colors[status.code]
    fraction = max(0.0, min(1.0, (pressure - tank.minimum_pressure_bar_abs)
                           / (tank.initial_pressure_bar_abs - tank.minimum_pressure_bar_abs)))
    gauge_max = reference.maximum_pressure_bar_abs or tank.initial_pressure_bar_abs
    angle = pi * (1 - max(0.0, min(1.0, pressure / gauge_max)))
    needle_x, needle_y = 768 + 47 * cos(angle), 142 - 47 * sin(angle)
    supplying = row["hydrogen_flow_g_s"] > 1e-9 and not isolated and fraction > 0
    particles = []
    # Partículas abstractas distribuidas por TODO el volumen: el H₂ es gas,
    # no se representa como un líquido cuyo nivel desciende.
    for index in range(14 + round(26 * fraction)):
        x = 155 + (index * 83) % 380
        y = 190 + (index * 47) % 125
        particles.append(f'<g class="molecule" style="animation-delay:-{index * .31:.2f}s;animation-duration:{3 + index % 4}s">'
                         f'<circle cx="{x}" cy="{y}" r="5"/><circle cx="{x + 8}" cy="{y - 3}" r="5"/>'
                         f'<path d="M{x} {y} l8 -3"/></g>')
    valve_label = "Salida aislada" if isolated else "Suministrando H₂" if supplying else "Sin suministro"
    def limit_text(value, unit):
        return f"{value:g} {unit}" if value is not None else "sin referencia"

    return f"""
<section class="cylinder-scene {'motion' if animate else 'still'}" style="--state:{color}" data-state="{status.code}">
<style>
.cylinder-scene {{ background:#f8fafc; color:#1e293b; border:1px solid #cbd5e1; border-radius:18px;
  padding:20px; font:16px/1.5 system-ui,sans-serif; container-type:inline-size; }}
.cylinder-scene .cyl-heading {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; align-items:center; }}
.cylinder-scene .cyl-heading p {{ margin:0; }}
.cylinder-scene .cyl-state {{ padding:6px 12px; border:1px solid var(--state); border-radius:24px;
  color:var(--state); font-weight:700; background:#fff; }}
.cylinder-scene svg {{ width:100%; height:auto; display:block; }}
.cylinder-scene .molecule {{ fill:#38bdf8; stroke:#0284c7; stroke-width:2; opacity:.65; }}
.cylinder-scene.motion .molecule {{ animation:cylinder-drift 4s ease-in-out infinite alternate; }}
.cylinder-scene .supply {{ fill:none; stroke:#0284c7; stroke-width:6; stroke-dasharray:10 12; }}
.cylinder-scene.motion .supply.active {{ animation:cylinder-flow 1s linear infinite; }}
.cylinder-scene .supply.inactive {{ stroke:#94a3b8; stroke-dasharray:none; }}
.cylinder-scene .readings {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; }}
.cylinder-scene .reading {{ background:#fff; border:1px solid #cbd5e1; padding:12px; border-radius:10px; }}
.cylinder-scene .reading strong {{ display:block; font-size:24px; font-variant-numeric:tabular-nums; }}
.cylinder-scene .reading span {{ color:#475569; }}
.cylinder-scene .cyl-detail {{ border-left:4px solid var(--state); padding-left:12px; }}
.cylinder-scene .cyl-note {{ color:#475569; font-size:14px; margin-bottom:0; }}
@keyframes cylinder-drift {{ from {{ transform:translate(-9px,-6px); }} to {{ transform:translate(10px,7px); }} }}
@keyframes cylinder-flow {{ to {{ stroke-dashoffset:-44; }} }}
@media (prefers-reduced-motion:reduce) {{ .cylinder-scene.motion .molecule,.cylinder-scene.motion .supply.active {{ animation:none; }} }}
@container (max-width:600px) {{ .cylinder-scene .readings {{ grid-template-columns:repeat(2,minmax(0,1fr)); }}
 .cylinder-scene .reading strong {{ font-size:20px; }} }}
</style>
<div class="cyl-heading"><p><strong>CILINDRO DE HIDRÓGENO</strong> · {row['time_s']:.2f} s</p>
<p class="cyl-state">{escape(status.label)}</p></div>
<svg viewBox="0 0 960 420" role="img" aria-labelledby="cylinder-title cylinder-desc">
<title id="cylinder-title">Cilindro de hidrógeno animado</title>
<desc id="cylinder-desc">{escape(status.label)}. Presión {pressure:.2f} bar absolutos.
Gas distribuido en el cilindro, manómetro y conducto hacia la PEM. {valve_label}.
Ilustración del inventario y flujo, sin evaluación de integridad estructural.</desc>
<defs>
 <linearGradient id="cyl-metal" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#94a3b8"/>
 <stop offset=".3" stop-color="#f1f5f9"/><stop offset=".6" stop-color="#cbd5e1"/><stop offset="1" stop-color="#64748b"/></linearGradient>
 <linearGradient id="cyl-gas" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#e0f2fe"/><stop offset="1" stop-color="#bae6fd"/></linearGradient>
 <clipPath id="cyl-interior"><rect x="137" y="175" width="435" height="160" rx="65"/></clipPath>
</defs>
<ellipse cx="360" cy="373" rx="270" ry="17" fill="#e2e8f0"/>
<path d="M190 325 V366 H230 V325 M477 325 V366 H517 V325" fill="#475569"/>
<rect x="80" y="140" width="555" height="205" rx="100" fill="none" stroke="{color}" stroke-width="18" opacity=".12"/>
<rect x="80" y="140" width="555" height="205" rx="100" fill="url(#cyl-metal)" stroke="{color}" stroke-width="3"/>
<rect x="137" y="175" width="435" height="160" rx="65" fill="url(#cyl-gas)" stroke="#64748b" stroke-width="2"/>
<g clip-path="url(#cyl-interior)">{''.join(particles)}</g>
<path d="M194 145 Q170 245 194 338 M523 145 Q547 245 523 338" fill="none" stroke="#64748b" stroke-width="17" opacity=".55"/>
<rect x="295" y="221" width="120" height="65" rx="12" fill="#fff" fill-opacity=".92"/>
<text x="355" y="266" text-anchor="middle" font-family="system-ui,sans-serif" font-size="36" font-weight="700" fill="#075985">H₂</text>
<rect x="622" y="218" width="65" height="48" rx="8" fill="#94a3b8" stroke="#475569" stroke-width="2"/>
<rect x="654" y="193" width="12" height="29" fill="#475569"/>
<path d="{'M644 196 H676' if not isolated else 'M660 180 V208'}" stroke="{color}" stroke-width="9" stroke-linecap="round"/>
<path d="M687 241 H881 V290" fill="none" stroke="#cbd5e1" stroke-width="18" stroke-linejoin="round"/>
<path class="supply {'active' if supplying else 'inactive'}" d="M687 241 H881 V290"/>
<path d="M768 241 V170" stroke="#64748b" stroke-width="9"/>
<circle cx="768" cy="120" r="65" fill="#fff" stroke="#64748b" stroke-width="5"/>
<path d="M716 142 A52 52 0 0 1 820 142" fill="none" stroke="#cbd5e1" stroke-width="8"/>
<path d="M768 142 L{needle_x:.2f} {needle_y:.2f}" stroke="{color}" stroke-width="5" stroke-linecap="round"/>
<circle cx="768" cy="142" r="7" fill="#334155"/>
<text x="768" y="111" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18" fill="#334155">bar abs.</text>
<rect x="820" y="290" width="120" height="72" rx="14" fill="#dbeafe" stroke="#1e40af" stroke-width="2"/>
<text x="880" y="335" text-anchor="middle" font-family="system-ui,sans-serif" font-size="24" fill="#1e40af">PEM</text>
<text x="355" y="403" text-anchor="middle" font-family="system-ui,sans-serif" font-size="18" fill="#475569">Corte ilustrativo · gas en todo el volumen</text>
</svg>
<div class="readings">
 <div class="reading"><span>Presión absoluta</span><strong>{pressure:.2f} bar</strong></div>
 <div class="reading"><span>Temperatura asumida</span><strong>{tank.temperature_k - 273.15:.2f} °C</strong></div>
 <div class="reading"><span>H₂ restante</span><strong>{row['hydrogen_remaining_kg'] * 1000:.2f} g</strong></div>
 <div class="reading"><span>Volumen interno</span><strong>{tank.volume_l:g} L</strong></div>
</div>
<p class="cyl-detail"><strong>{valve_label}</strong> · Flujo medio del intervalo: {row['hydrogen_flow_g_s']:.4f} g/s.<br>
{escape(status.detail)}</p>
<p class="cyl-note">Escala del manómetro: 0–{gauge_max:g} bar absolutos ({'máxima ingresada' if reference.maximum_pressure_bar_abs else 'presión inicial, no límite admisible'}).
Inventario sobre reserva: {fraction:.0%} del inicial. Reserva: {tank.minimum_pressure_bar_abs:g} bar absolutos.</p>
<p class="cyl-note">Referencias ingresadas · presión máxima: {limit_text(reference.maximum_pressure_bar_abs, 'bar abs.')};
temperatura mínima: {limit_text(reference.minimum_temperature_c, '°C')}; máxima: {limit_text(reference.maximum_temperature_c, '°C')}.</p>
<p class="cyl-note">Partículas y válvula ilustrativas. El movimiento no representa velocidad molecular ni una fuga.
Esta vista compara valores; no verifica el estado físico ni certifica el cilindro.</p>
</section>"""
