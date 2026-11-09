/* Inventario algebraico pV = Z m R T. Sin modelo estructural o de fugas. */
const H2Physics = (() => {
  const R = 4124.2;
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  function validateTank(tank) {
    for (const key of ["volume_l", "temperature_k", "compressibility_factor"]) {
      if (!Number.isFinite(tank[key]) || tank[key] <= 0) throw new Error("Volumen, temperatura y Z deben ser positivos.");
    }
    if (!Number.isFinite(tank.minimum_pressure_bar_abs) || tank.minimum_pressure_bar_abs < 0) throw new Error("La reserva debe ser no negativa.");
  }
  function massAtPressure(tank, pressure) {
    validateTank(tank);
    if (!Number.isFinite(pressure) || pressure < 0) throw new Error("Presión no negativa requerida.");
    return pressure * 1e5 * tank.volume_l / 1000 / (tank.compressibility_factor * R * tank.temperature_k);
  }
  function pressureAtMass(tank, mass) {
    validateTank(tank);
    if (!Number.isFinite(mass) || mass < 0) throw new Error("Masa no negativa requerida.");
    return mass * tank.compressibility_factor * R * tank.temperature_k / (tank.volume_l / 1000) / 1e5;
  }
  function advance(state, tank, seconds, flowGramsPerSecond) {
    validateTank(tank);
    if (![seconds, flowGramsPerSecond, state.mass, state.time, state.used].every(value => Number.isFinite(value) && value >= 0)) throw new Error("Paso, flujo y estado no negativos requeridos.");
    const reserve = massAtPressure(tank, tank.minimum_pressure_bar_abs);
    // Si un cambio manual de T o V deja la masa bajo la reserva, no se crea gas.
    const available = Math.max(0, state.mass - reserve);
    const withdrawn = state.valveOpen && !state.isolated ? Math.min(available, flowGramsPerSecond / 1000 * seconds) : 0;
    return { ...state, mass: state.mass - withdrawn, used: state.used + withdrawn,
      time: state.time + seconds, actualFlow: seconds > 0 ? withdrawn * 1000 / seconds : 0 };
  }
  function status(tank, pressure, reference, state) {
    const { maximum_pressure_bar_abs: p, minimum_temperature_c: low, maximum_temperature_c: high } = reference;
    const limits = [p, low, high];
    if (limits.some(value => value !== null && !Number.isFinite(value)) ||
        (p !== null && p <= 0) || (low !== null && low <= -273.15) ||
        (high !== null && high <= -273.15) || (low !== null && high !== null && low > high)) {
      return { code: "invalid", label: "Revisa las referencias", detail: "Usa presión máxima positiva y temperatura mínima menor o igual a la máxima." };
    }
    const t = tank.temperature_k - 273.15, eps = 1e-8;
    if ((p !== null && pressure > p + eps) || (low !== null && t < low - eps) || (high !== null && t > high + eps)) {
      return { code: "outside", label: "Fuera de los límites ingresados", detail: "La presión o la temperatura exceden una referencia. La comparación no cierra la salida automáticamente." };
    }
    if (state.isolated) return { code: "isolated", label: "Salida aislada", detail: "Rearma el sistema para volver a abrir la salida." };
    if (pressure <= tank.minimum_pressure_bar_abs + eps) return { code: "reserve", label: "Reserva alcanzada", detail: "No se extrae más gas por debajo de la reserva configurada." };
    if (limits.every(value => value !== null)) return { code: "within", label: "Dentro de los límites ingresados", detail: "Presión y temperatura dentro de tus referencias; no es una evaluación de integridad física." };
    return { code: "unknown", label: limits.some(value => value !== null) ? "Referencias incompletas" : "Sin límites de referencia",
      detail: "Puedes explorar. Para comparar condiciones, completa las tres referencias en el panel." };
  }
  return { R, clamp, massAtPressure, pressureAtMass, advance, status };
})();
if (typeof module !== "undefined" && module.exports) module.exports = H2Physics;
