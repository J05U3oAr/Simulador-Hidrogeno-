/* Interacción y dibujo del laboratorio. Las lecturas vienen de H2Physics. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const defaults = LAB_DEFAULTS.tank;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const canvas = $("scene"), ctx = canvas.getContext("2d");
  const chart = $("chart"), plot = chart.getContext("2d");
  const palette = { unknown: "#2268a8", within: "#16836a", outside: "#c23737", invalid: "#c23737", reserve: "#a67719", isolated: "#a67719" };
  let tank, state, initialMass, running, history, particles, chargePressure;
  let view = "explore", lastTimestamp = null, lastSampleTime = 0, paintTime = 0, uiElapsed = 0;
  let modelValid = true;

  function fitCanvas(target, context, width, height) {
    const scale = Math.min(window.devicePixelRatio || 1, 2);
    target.width = width * scale;
    target.height = height * scale;
    context.setTransform(scale, 0, 0, scale, 0, 0);
  }
  fitCanvas(canvas, ctx, 1000, 560);
  fitCanvas(chart, plot, 1000, 320);

  function setText(id, text) {
    if ($(id).textContent !== text) $(id).textContent = text;
  }
  function configureRange(id, value, min, max) {
    const input = $(id);
    input.min = Math.min(min, value);
    input.max = Math.max(max, value);
    // Conserva valores del JSON que no coincidan con el paso visual inicial.
    input.step = "any";
    input.value = value;
  }
  function reference() {
    const optional = id => $(id).value.trim() === "" ? null : $(id).valueAsNumber;
    return { maximum_pressure_bar_abs: optional("max-pressure"), minimum_temperature_c: optional("min-temperature"), maximum_temperature_c: optional("max-temperature") };
  }
  function pressure() { return H2Physics.pressureAtMass(tank, state.mass); }
  function currentStatus() {
    return modelValid ? H2Physics.status(tank, pressure(), reference(), state) :
      { code: "invalid", label: "Revisa los datos del modelo", detail: "Corrige reserva y Z. Se conservan los últimos valores válidos y la simulación está pausada." };
  }
  function seedParticles() {
    particles = Array.from({ length: 110 }, (_, index) => {
      const phase = index * 2.39996;
      return { x: 190 + ((index * 89) % 350), y: 220 + ((index * 47) % 100),
        vx: Math.cos(phase) * 47, vy: Math.sin(phase) * 47, phase };
    });
  }
  function refill() {
    initialMass = H2Physics.massAtPressure(tank, chargePressure);
    state = { mass: initialMass, time: 0, used: 0, valveOpen: false, isolated: false, actualFlow: 0 };
    history = [];
    lastSampleTime = 0;
    seedParticles();
    record("Carga inicial");
    update();
  }
  function reset() {
    tank = { ...defaults };
    chargePressure = defaults.initial_pressure_bar_abs;
    running = !reducedMotion.matches;
    modelValid = true;
    configureRange("temperature", tank.temperature_k - 273.15, -100, 150);
    configureRange("volume", tank.volume_l, 1, 30);
    configureRange("charge", chargePressure, Math.min(20, chargePressure), 400);
    $("flow").value = "0.02";
    $("rate").value = "1";
    $("reserve").value = tank.minimum_pressure_bar_abs;
    $("z-factor").value = tank.compressibility_factor;
    for (const id of ["max-pressure", "min-temperature", "max-temperature"]) $(id).value = "";
    $("model-error").hidden = true;
    $("particles").checked = $("cutaway").checked = true;
    $("vectors").checked = false;
    lastTimestamp = null;
    refill();
  }
  function record(reason) {
    history.push({ time_s: state.time, pressure_bar_abs: pressure(), temperature_c: tank.temperature_k - 273.15,
      volume_l: tank.volume_l, hydrogen_g: state.mass * 1000, flow_g_s: state.actualFlow, change: reason });
    if (history.length > 5000) history.shift();
    if (view === "measure") drawMeasurements();
  }
  function advance(seconds) {
    state = H2Physics.advance(state, tank, seconds, Number($("flow").value));
    if (state.time - lastSampleTime >= 1 - 1e-8) {
      record("Tiempo");
      lastSampleTime = state.time;
    }
  }
  function toggleValve() {
    if (!modelValid || state.isolated) return;
    state.valveOpen = !state.valveOpen;
    state.actualFlow = 0;
    record(state.valveOpen ? "Salida abierta" : "Salida cerrada");
    update();
  }
  function update() {
    const status = currentStatus();
    setText("pressure-reading", `${pressure().toFixed(2)} bar`);
    setText("temperature-reading", `${(tank.temperature_k - 273.15).toFixed(1)} °C`);
    setText("mass-reading", `${(state.mass * 1000).toFixed(2)} g`);
    setText("flow-reading", `${(running ? state.actualFlow : 0).toFixed(4)} g/s`);
    setText("temperature-value", `${(tank.temperature_k - 273.15).toFixed(1)} °C`);
    setText("volume-value", `${tank.volume_l.toFixed(1)} L`);
    setText("charge-value", `${chargePressure.toFixed(1)} bar abs.`);
    setText("flow-value", `${Number($("flow").value).toFixed(3)} g/s`);
    setText("clock", `${state.time.toFixed(1)} s`);
    setText("state-badge", status.label);
    $("state-badge").dataset.state = status.code;
    const operation = state.isolated ? "Salida aislada." : state.valveOpen ? "Salida abierta." : "Salida cerrada.";
    setText("status-detail", `${operation} ${status.detail}`);
    setText("play", running ? "Pausar" : "Reproducir");
    $("play").setAttribute("aria-label", running ? "Pausar simulación" : "Reproducir simulación");
    $("play").disabled = !modelValid;
    $("step").disabled = running || !modelValid;
    for (const id of ["valve", "valve-on-scene"]) {
      setText(id, state.isolated ? "Salida aislada" : state.valveOpen ? "Cerrar salida" : "Abrir salida");
      $(id).disabled = state.isolated || !modelValid;
      $(id).setAttribute("aria-pressed", String(state.valveOpen));
      $(id).setAttribute("aria-label", state.isolated ? "Salida aislada" : state.valveOpen ? "Cerrar salida del cilindro" : "Abrir salida del cilindro");
    }
    setText("isolate", state.isolated ? "Rearmar salida" : "Aislar salida");
    drawScene(0);
  }

  function rounded(context, x, y, width, height, radius, fill, stroke, lineWidth = 2) {
    context.beginPath();
    context.roundRect(x, y, width, height, radius);
    if (fill) { context.fillStyle = fill; context.fill(); }
    if (stroke) { context.strokeStyle = stroke; context.lineWidth = lineWidth; context.stroke(); }
  }
  function text(context, value, x, y, size = 16, color = "#284d73", align = "left", weight = 500) {
    context.font = `${weight} ${size}px system-ui, sans-serif`;
    context.fillStyle = color;
    context.textAlign = align;
    context.fillText(value, x, y);
  }
  function geometry() {
    const width = H2Physics.clamp(470 * Math.cbrt(tank.volume_l / 6), 320, 580);
    return { left: 350 - width / 2, right: 350 + width / 2, top: 205, bottom: 398, width };
  }
  function moveParticles(seconds, box) {
    const radius = 60, left = box.left + 20, right = box.right - 20, top = box.top + 19, bottom = box.bottom - 19;
    const speed = Math.sqrt(tank.temperature_k / 293.15);
    for (const p of particles) {
      const oldX = p.x, oldY = p.y;
      p.x += p.vx * seconds * speed;
      p.y += p.vy * seconds * speed;
      p.x = H2Physics.clamp(p.x, left + 10, right - 10);
      p.y = H2Physics.clamp(p.y, top + 10, bottom - 10);
      if ((p.x <= left + 10 && p.vx < 0) || (p.x >= right - 10 && p.vx > 0)) p.vx *= -1;
      if ((p.y <= top + 10 && p.vy < 0) || (p.y >= bottom - 10 && p.vy > 0)) p.vy *= -1;
      // Reflejo ilustrativo en las esquinas redondeadas del corte.
      const cx = H2Physics.clamp(p.x, left + radius, right - radius);
      const cy = H2Physics.clamp(p.y, top + radius, bottom - radius);
      const dx = p.x - cx, dy = p.y - cy, distance = Math.hypot(dx, dy);
      if (distance > radius - 10) {
        const nx = dx / distance, ny = dy / distance;
        const dot = p.vx * nx + p.vy * ny;
        if (dot > 0) { p.vx -= 2 * dot * nx; p.vy -= 2 * dot * ny; }
        p.x = cx + nx * (radius - 11);
        p.y = cy + ny * (radius - 11);
      }
      if (!Number.isFinite(p.x + p.y)) { p.x = oldX; p.y = oldY; }
    }
  }
  function drawScene(seconds) {
    if (!state) return;
    const box = geometry(), { left, right, top, bottom, width } = box;
    const status = currentStatus(), color = palette[status.code];
    ctx.clearRect(0, 0, 1000, 560);
    for (let x = 30; x < 1000; x += 34) for (let y = 20; y < 520; y += 34) {
      ctx.fillStyle = "#d6e6f4"; ctx.beginPath(); ctx.arc(x, y, 1.1, 0, Math.PI * 2); ctx.fill();
    }
    text(ctx, "¿Qué ocurre si cambias T o V?", 42, 55, 23, "#173b63", "left", 700);
    text(ctx, "Misma masa · la presión responde al instante", 42, 83, 15, "#526c87");
    ctx.beginPath(); ctx.ellipse(355, 435, width / 2 + 30, 13, 0, 0, Math.PI * 2); ctx.fillStyle = "#ccdeed"; ctx.fill();
    rounded(ctx, left + 66, bottom - 20, 38, 48, 7, "#58728c");
    rounded(ctx, right - 104, bottom - 20, 38, 48, 7, "#58728c");
    const metal = ctx.createLinearGradient(0, top, 0, bottom);
    metal.addColorStop(0, "#8da5bd"); metal.addColorStop(.25, "#f6fafc"); metal.addColorStop(.6, "#b9cbdc"); metal.addColorStop(1, "#6f8ba6");
    rounded(ctx, left - 5, top - 5, width + 10, bottom - top + 10, 90, null, color, 3);
    rounded(ctx, left, top, width, bottom - top, 85, metal, "#67839d");
    if ($("cutaway").checked) {
      const gas = ctx.createLinearGradient(0, top, 0, bottom);
      gas.addColorStop(0, "#ecfaff"); gas.addColorStop(1, "#bedff3");
      rounded(ctx, left + 20, top + 19, width - 40, bottom - top - 38, 60, gas, "#739ab7", 1.5);
      moveParticles(seconds, box);
      if ($("particles").checked) {
        const count = Math.max(2, Math.min(particles.length, Math.round(110 * state.mass / initialMass)));
        ctx.save(); ctx.beginPath(); ctx.roundRect(left + 20, top + 19, width - 40, bottom - top - 38, 60); ctx.clip();
        for (const p of particles.slice(0, count)) {
          if ($("vectors").checked) {
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(p.x + p.vx * .28, p.y + p.vy * .28);
            ctx.strokeStyle = "#1977a9"; ctx.lineWidth = 1; ctx.stroke();
          }
          ctx.beginPath(); ctx.arc(p.x - 3, p.y, 4.3, 0, Math.PI * 2); ctx.arc(p.x + 3, p.y + 2, 4.3, 0, Math.PI * 2);
          ctx.fillStyle = "#20a4d8"; ctx.fill(); ctx.strokeStyle = "#087cae"; ctx.lineWidth = 1; ctx.stroke();
        }
        ctx.restore();
      }
    }
    rounded(ctx, 310, 277, 80, 50, 10, "#ffffffea");
    text(ctx, "H₂", 350, 313, 34, "#0a6895", "center", 700);
    text(ctx, `${tank.volume_l.toFixed(1)} L`, 350, 466, 18, "#416889", "center", 650);
    text(ctx, $("cutaway").checked ? "Corte ilustrativo · gas en todo el volumen" : "Vista exterior del cilindro", 350, 493, 14, "#526c87", "center");

    const valveX = right + 38, tubeY = 288;
    rounded(ctx, right - 3, tubeY - 21, 61, 42, 7, "#a4b8ca", "#536f88");
    ctx.beginPath(); ctx.moveTo(valveX, tubeY - 22); ctx.lineTo(valveX, tubeY - 52); ctx.strokeStyle = "#496881"; ctx.lineWidth = 8; ctx.stroke();
    ctx.beginPath();
    if (state.valveOpen && !state.isolated) { ctx.moveTo(valveX - 19, tubeY - 52); ctx.lineTo(valveX + 19, tubeY - 52); }
    else { ctx.moveTo(valveX, tubeY - 70); ctx.lineTo(valveX, tubeY - 34); }
    ctx.strokeStyle = state.valveOpen && !state.isolated ? "#159170" : "#c08722"; ctx.lineWidth = 10; ctx.lineCap = "round"; ctx.stroke(); ctx.lineCap = "butt";
    $("valve-on-scene").style.left = `${(valveX - 48) / 10}%`;
    ctx.beginPath(); ctx.moveTo(right + 58, tubeY); ctx.lineTo(870, tubeY); ctx.lineTo(870, 360); ctx.strokeStyle = "#95b0c8"; ctx.lineWidth = 18; ctx.lineJoin = "round"; ctx.stroke();
    ctx.beginPath(); ctx.moveTo(right + 58, tubeY); ctx.lineTo(870, tubeY); ctx.lineTo(870, 360);
    ctx.strokeStyle = state.actualFlow > 0 && state.valveOpen && !state.isolated ? "#1798c7" : "#c5d9e9";
    ctx.lineWidth = 6; ctx.setLineDash([9, 14]); ctx.lineDashOffset = -paintTime * 40; ctx.stroke(); ctx.setLineDash([]); ctx.lineDashOffset = 0;
    rounded(ctx, 807, 360, 126, 73, 15, "#d7e9f8", "#5485b0"); text(ctx, "PEM", 870, 405, 26, "#245a87", "center", 700);
    text(ctx, state.isolated ? "Aislada" : state.valveOpen ? "Salida abierta" : "Salida cerrada", 870, 458, 15, "#526c87", "center");

    const requestedScale = reference().maximum_pressure_bar_abs;
    const max = Number.isFinite(requestedScale) && requestedScale > 0 ? requestedScale : Math.max(chargePressure * 2, 1);
    const gx = 802, gy = 193;
    ctx.beginPath(); ctx.moveTo(gx, tubeY); ctx.lineTo(gx, gy + 26); ctx.strokeStyle = "#6485a1"; ctx.lineWidth = 9; ctx.stroke();
    ctx.beginPath(); ctx.arc(gx, gy - 12, 65, 0, Math.PI * 2); ctx.fillStyle = "#fff"; ctx.fill(); ctx.strokeStyle = "#547a9c"; ctx.lineWidth = 4; ctx.stroke();
    for (let i = 0; i <= 10; i++) {
      const angle = Math.PI * (1 - i / 10);
      ctx.beginPath(); ctx.moveTo(gx + Math.cos(angle) * 47, gy + Math.sin(-angle) * 47);
      ctx.lineTo(gx + Math.cos(angle) * 54, gy + Math.sin(-angle) * 54); ctx.strokeStyle = "#7a96b0"; ctx.lineWidth = 2; ctx.stroke();
    }
    const angle = Math.PI * (1 - H2Physics.clamp(pressure() / max, 0, 1));
    ctx.beginPath(); ctx.moveTo(gx, gy); ctx.lineTo(gx + Math.cos(angle) * 43, gy - Math.sin(angle) * 43); ctx.strokeStyle = color; ctx.lineWidth = 4; ctx.stroke();
    ctx.beginPath(); ctx.arc(gx, gy, 6, 0, Math.PI * 2); ctx.fillStyle = color; ctx.fill();
    text(ctx, "bar abs.", gx, gy - 24, 15, "#416889", "center");
    text(ctx, `0–${max.toFixed(0)} · escala`, gx, 108, 13, "#526c87", "center");
    text(ctx, "Escala visual; no presión admisible", gx, 84, 11, "#526c87", "center");
    const thermometer = H2Physics.clamp((tank.temperature_k - 173.15) / 250, 0, 1);
    rounded(ctx, 48, 225, 22, 170, 11, "#fff", "#6b8eaa");
    rounded(ctx, 54, 234 + 147 * (1 - thermometer), 10, 5 + 147 * thermometer, 5, "#dd6a45");
    ctx.beginPath(); ctx.arc(59, 400, 17, 0, Math.PI * 2); ctx.fillStyle = "#dd6a45"; ctx.fill();
    text(ctx, "T", 59, 443, 18, "#526c87", "center", 700);
  }

  function drawMeasurements() {
    plot.clearRect(0, 0, 1000, 320);
    const left = 90, top = 25, width = 860, height = 230;
    const maxPressure = Math.max(1, ...history.map(sample => sample.pressure_bar_abs)) * 1.15;
    const firstTime = history[0]?.time_s || 0, span = Math.max(1, state.time - firstTime);
    for (let i = 0; i <= 4; i++) {
      const y = top + height * i / 4;
      plot.beginPath(); plot.moveTo(left, y); plot.lineTo(left + width, y); plot.strokeStyle = "#cfdeed"; plot.lineWidth = 1; plot.stroke();
      text(plot, (maxPressure * (1 - i / 4)).toFixed(1), left - 12, y + 5, 14, "#526c87", "right");
    }
    text(plot, "bar abs.", left, 15, 13);
    plot.beginPath();
    history.forEach((sample, i) => {
      const x = left + (sample.time_s - firstTime) / span * width;
      const y = top + height * (1 - sample.pressure_bar_abs / maxPressure);
      if (i === 0) plot.moveTo(x, y); else plot.lineTo(x, y);
    });
    plot.strokeStyle = "#1e64a8"; plot.lineWidth = 3; plot.stroke();
    text(plot, `${firstTime.toFixed(1)} s`, left, 285, 14);
    text(plot, `${state.time.toFixed(1)} s`, left + width, 285, 14, "#526c87", "right");
    text(plot, "Tiempo de exploración", left + width / 2, 307, 14, "#526c87", "center");
    const tbody = $("table-body"); tbody.replaceChildren();
    for (const row of history.slice(-12).reverse()) {
      const tr = document.createElement("tr");
      for (const value of [row.time_s.toFixed(2), row.pressure_bar_abs.toFixed(2), row.temperature_c.toFixed(1), row.volume_l.toFixed(1), row.hydrogen_g.toFixed(3), row.change]) {
        const td = document.createElement("td"); td.textContent = value; tr.append(td);
      }
      tbody.append(tr);
    }
    setText("table-caption", `Últimas ${Math.min(12, history.length)} de ${history.length} muestras conservadas`);
  }
  function selectView(next) {
    view = next;
    $("exploration").hidden = next !== "explore";
    $("measurements").hidden = next !== "measure";
    $("explore-tab").setAttribute("aria-pressed", String(next === "explore"));
    $("measure-tab").setAttribute("aria-pressed", String(next === "measure"));
    if (next === "measure") drawMeasurements();
  }
  function validateModel() {
    const reserve = $("reserve").valueAsNumber, z = $("z-factor").valueAsNumber;
    modelValid = Number.isFinite(reserve) && reserve >= 0 && Number.isFinite(z) && z > 0;
    $("model-error").hidden = modelValid;
    if (!modelValid) { running = false; setText("model-error", "Reserva no negativa y Z positivo requeridos. Se pausó el experimento."); }
    else { tank.minimum_pressure_bar_abs = reserve; tank.compressibility_factor = z; state.actualFlow = 0; record("Referencia o Z"); }
    update();
  }
  $("temperature").addEventListener("input", () => { tank.temperature_k = Number($("temperature").value) + 273.15; state.actualFlow = 0; record("Temperatura"); update(); });
  $("volume").addEventListener("input", () => { tank.volume_l = Number($("volume").value); state.actualFlow = 0; record("Volumen"); update(); });
  $("charge").addEventListener("input", () => { chargePressure = Number($("charge").value); refill(); });
  $("flow").addEventListener("input", update);
  for (const id of ["max-pressure", "min-temperature", "max-temperature"]) $(id).addEventListener("input", update);
  for (const id of ["reserve", "z-factor"]) $(id).addEventListener("input", validateModel);
  for (const id of ["cutaway", "particles", "vectors"]) $(id).addEventListener("change", update);
  for (const id of ["valve", "valve-on-scene"]) $(id).addEventListener("click", toggleValve);
  $("isolate").addEventListener("click", () => { state.isolated = !state.isolated; state.valveOpen = false; state.actualFlow = 0; record(state.isolated ? "Aislamiento manual" : "Rearme"); update(); });
  $("refill").addEventListener("click", refill);
  $("reset").addEventListener("click", reset);
  $("play").addEventListener("click", () => { if (modelValid) running = !running; update(); });
  $("step").addEventListener("click", () => { if (!running && modelValid) { advance(1); record("Paso manual"); update(); } });
  $("explore-tab").addEventListener("click", () => selectView("explore"));
  $("measure-tab").addEventListener("click", () => selectView("measure"));
  $("export-csv").addEventListener("click", () => {
    const columns = ["time_s", "pressure_bar_abs", "temperature_c", "volume_l", "hydrogen_g", "flow_g_s", "change"];
    const csv = "\ufeff" + columns.join(",") + "\n" + history.map(row => columns.map(key => row[key]).join(",")).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a"); link.href = url; link.download = "mediciones_cilindro.csv"; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  document.addEventListener("visibilitychange", () => { lastTimestamp = null; });
  reducedMotion.addEventListener("change", () => { if (reducedMotion.matches) { running = false; update(); } });

  function frame(timestamp) {
    const seconds = lastTimestamp === null ? 0 : Math.min(.1, Math.max(0, (timestamp - lastTimestamp) / 1000));
    lastTimestamp = timestamp;
    if (!document.hidden) {
      if (running && modelValid && seconds > 0) advance(seconds * Number($("rate").value));
      const visualSeconds = running && !reducedMotion.matches ? seconds : 0;
      paintTime += visualSeconds;
      if (view === "explore" && visualSeconds > 0) drawScene(visualSeconds);
      uiElapsed += seconds;
      if (running && uiElapsed >= .12) { update(); uiElapsed = 0; }
    }
    requestAnimationFrame(frame);
  }
  reset();
  requestAnimationFrame(frame);
})();
