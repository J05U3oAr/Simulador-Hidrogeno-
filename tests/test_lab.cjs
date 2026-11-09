const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assets = path.join(__dirname, "../src/simulador/lab_assets");
const physics = require(path.join(assets, "physics.js"));
const tank = { volume_l: 6, temperature_k: 293.15, compressibility_factor: 1.15,
  initial_pressure_bar_abs: 200, minimum_pressure_bar_abs: 10 };
const initialState = () => ({ mass: physics.massAtPressure(tank, 200), used: 0, time: 0, valveOpen: true, isolated: false });
const near = (a, b) => assert.ok(Math.abs(a - b) < 1e-9, `${a} != ${b}`);

test("T and V change pressure at fixed mass; gas mass is conserved", () => {
  const mass = physics.massAtPressure(tank, 200);
  near(physics.pressureAtMass(tank, mass), 200);
  near(physics.pressureAtMass({ ...tank, temperature_k: tank.temperature_k * 2 }, mass), 400);
  near(physics.pressureAtMass({ ...tank, volume_l: 12 }, mass), 100);
});
test("withdrawal conserves mass and cannot consume reserve", () => {
  const state = initialState();
  const final = physics.advance(state, tank, 100000, 1);
  near(physics.pressureAtMass(tank, final.mass), 10);
  near(final.mass + final.used, state.mass);
  near(physics.advance(final, tank, 10, 1).mass, final.mass);
  const a = physics.advance(state, tank, 5, .02);
  const b = physics.advance(physics.advance(state, tank, 2, .02), tank, 3, .02);
  near(a.mass, b.mass);
});
test("closed and isolated outlets consume nothing; expanded gas does not gain mass at reserve", () => {
  const state = initialState();
  near(physics.advance({ ...state, valveOpen: false }, tank, 10, .2).mass, state.mass);
  near(physics.advance({ ...state, isolated: true }, tank, 10, .2).mass, state.mass);
  const lowMass = { ...state, mass: physics.massAtPressure(tank, 5) };
  near(physics.advance(lowMass, tank, 10, .2).mass, lowMass.mass);
  assert.throws(() => physics.advance(state, tank, -1, .02));
  assert.throws(() => physics.advance(state, tank, 1, NaN));
});
test("unknown, partial, invalid and exceeded references are distinct", () => {
  const ref = { maximum_pressure_bar_abs: null, minimum_temperature_c: null, maximum_temperature_c: null };
  const state = initialState();
  assert.equal(physics.status(tank, 200, ref, state).code, "unknown");
  assert.equal(physics.status(tank, 200, { ...ref, maximum_pressure_bar_abs: 150 }, state).code, "outside");
  const complete = { maximum_pressure_bar_abs: 250, minimum_temperature_c: 0, maximum_temperature_c: 36.6 };
  assert.equal(physics.status({ ...tank, temperature_k: 36.6 + 273.15 }, 200, complete, state).code, "within");
  assert.equal(physics.status(tank, 200, { ...complete, minimum_temperature_c: 50 }, state).code, "invalid");
  assert.equal(physics.status(tank, 10, complete, state).code, "reserve");
  assert.equal(physics.status(tank, 200, complete, { ...state, isolated: true }).code, "isolated");
});

// Prueba de enlaces de eventos y ciclo temporal con DOM y Canvas simulados.
// No sustituye una revisión visual en navegador.
function laboratory(reduced = false) {
  const noop = () => {};
  const context2d = new Proxy({ createLinearGradient: () => ({ addColorStop: noop }) }, {
    get: (target, key) => key in target ? target[key] : noop,
  });
  class Element {
    constructor(id = "") { this.id = id; this._value = ""; this.textContent = ""; this.style = {}; this.dataset = {}; this.events = {}; this.attributes = {}; this.children = []; this.checked = false; this.hidden = false; this.disabled = false; }
    set value(value) { this._value = String(value); }
    get value() { return this._value; }
    get valueAsNumber() { return this.value === "" ? NaN : Number(this.value); }
    addEventListener(name, handler) { this.events[name] = handler; }
    setAttribute(name, value) { this.attributes[name] = value; }
    getContext() { return context2d; }
    append(element) { this.children.push(element); }
    replaceChildren() { this.children = []; }
    click() { if (!this.disabled) this.events.click?.(); }
    emit(name) { this.events[name]?.(); }
  }
  const html = fs.readFileSync(path.join(assets, "index.html"), "utf8");
  const nodes = Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(match => [match[1], new Element(match[1])]));
  let nextFrame;
  const sandbox = { document: { hidden: false, getElementById: id => nodes[id], createElement: () => new Element(), addEventListener: noop },
    window: { devicePixelRatio: 1, matchMedia: () => ({ matches: reduced, addEventListener: noop }) },
    requestAnimationFrame: callback => { nextFrame = callback; }, console, setTimeout: noop,
    Blob, URL: { createObjectURL: () => "blob:test", revokeObjectURL: noop } };
  const source = `const LAB_DEFAULTS = ${JSON.stringify({ tank })};\n` +
    fs.readFileSync(path.join(assets, "physics.js"), "utf8") + "\n" + fs.readFileSync(path.join(assets, "lab.js"), "utf8");
  vm.runInNewContext(source, sandbox);
  return { nodes, input(id, value) { nodes[id].value = value; nodes[id].emit("input"); }, tick(time) { nextFrame(time); } };
}
test("live sliders update readings immediately without starting a route", () => {
  const lab = laboratory(), n = lab.nodes;
  assert.equal(parseFloat(n["pressure-reading"].textContent), 200);
  const mass = n["mass-reading"].textContent;
  lab.input("volume", 12);
  assert.equal(parseFloat(n["pressure-reading"].textContent), 100);
  assert.equal(n["mass-reading"].textContent, mass);
  lab.input("temperature", 100);
  assert.equal(parseFloat(n["pressure-reading"].textContent), Number((100 * 373.15 / 293.15).toFixed(2)));
  assert.equal(n["mass-reading"].textContent, mass);
  lab.input("max-pressure", 100);
  assert.equal(n["state-badge"].dataset.state, "outside");
  lab.input("max-pressure", 250); lab.input("min-temperature", 0); lab.input("max-temperature", 150);
  assert.equal(n["state-badge"].dataset.state, "within");
});
test("play, pause, step, valve, isolation and refill control gas consumption", () => {
  const lab = laboratory(), n = lab.nodes;
  const initial = parseFloat(n["mass-reading"].textContent);
  n.valve.click(); lab.tick(0); lab.tick(100);
  n.play.click();
  lab.tick(200);
  assert.ok(n.step.disabled === false);
  n.step.click();
  assert.ok(parseFloat(n["mass-reading"].textContent) < initial);
  n.isolate.click();
  assert.equal(n.valve.disabled, true);
  const isolatedMass = n["mass-reading"].textContent;
  n.step.click(); assert.equal(n["mass-reading"].textContent, isolatedMass);
  n.isolate.click(); assert.equal(n.valve.attributes["aria-pressed"], "false");
  n.refill.click();
  assert.equal(parseFloat(n["mass-reading"].textContent), initial);
  assert.equal(n.clock.textContent, "0.0 s");
});
test("measurements are available as a table and model errors pause the experiment", () => {
  const lab = laboratory(), n = lab.nodes;
  n["measure-tab"].click();
  assert.equal(n.measurements.hidden, false);
  assert.equal(n["table-body"].children.length, 1);
  lab.input("volume", 12);
  assert.equal(n["table-body"].children.length, 2);
  lab.input("z-factor", "");
  assert.equal(n.play.disabled, true);
  assert.equal(n["state-badge"].dataset.state, "invalid");
  lab.input("z-factor", 1.15);
  assert.equal(n.play.disabled, false);
  assert.equal(n.play.textContent, "Reproducir");
  n["export-csv"].click();
});
test("reduced motion starts paused and can still expose static readings", () => {
  const lab = laboratory(true);
  assert.equal(lab.nodes.play.textContent, "Reproducir");
  assert.equal(lab.nodes.step.disabled, false);
  assert.equal(parseFloat(lab.nodes["pressure-reading"].textContent), 200);
});
