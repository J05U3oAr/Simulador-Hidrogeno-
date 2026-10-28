# Simulador de hidrógeno

Herramienta de dimensionamiento preliminar de un vehículo con celda PEM y
supercapacitores. Los datos iniciales son ejemplos, no especificaciones
verificadas de los componentes del diagrama. No controla hardware ni certifica
la seguridad de una instalación.

## Preparación en PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m simulador.cli
.\.venv\Scripts\python.exe -m pytest
```

## Abrir la interfaz

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Abre `http://127.0.0.1:8501`, configura el escenario y pulsa **Ejecutar
simulación**. Las pestañas muestran energía, eventos, parámetros usados,
comparación y descargas. El formulario aplica masa y potencia PEM sobre el
JSON cargado; los demás parámetros se conservan. Los archivos subidos se leen
en memoria. Para editar todos los parámetros, copia `data/example.json` y
mantén el formato de unidades y procedencia.

### Qué rellenar en la interfaz

En la barra lateral **Preparar escenario**, completa los campos que correspondan
al escenario y luego pulsa **Ejecutar simulación**:

| Campo | Qué significa / qué introducir | Cuándo aplica |
| --- | --- | --- |
| Recorrido | Perfil de velocidad y pendiente que seguirá el vehículo: urbano de ejemplo, velocidad constante o CSV personalizado. | Siempre; elige una opción. |
| Recorrido CSV | Archivo con columnas `time_s`, `speed_kmh` y `grade_percent`. El tiempo debe iniciar en 0 y aumentar. La pendiente de cada fila aplica hasta la siguiente. | Solo con CSV personalizado. |
| Configuración JSON (opcional) | Archivo con parámetros completos siguiendo la estructura de `data/example.json`; permite modificar los valores avanzados descritos abajo. | Opcional. |
| Masa total [kg] | Masa total simulada del vehículo, incluyendo lo que se haya decidido representar como carga. | Siempre; reemplaza la masa del JSON si se carga uno. |
| Potencia bruta máxima PEM [W] | Límite de potencia eléctrica bruta de la celda PEM. | Siempre; reemplaza la potencia PEM del JSON si se carga uno. |
| Pendiente para velocidad constante [%] | Inclinación de la vía; positiva es subida y negativa bajada. | Solo para velocidad constante. |
| Velocidad constante [km/h] | Velocidad objetivo mantenida durante el escenario. | Solo para velocidad constante. |
| Duración a velocidad constante [s] | Tiempo durante el que se mantiene esa velocidad. | Solo para velocidad constante. |
| Paso máximo [s] | Duración máxima de cada intervalo de cálculo. Menor valor da más detalle temporal y puede tardar más. | Siempre. |
| Evento de prueba | Sin fallo, alarma lógica de hidrógeno o parada de emergencia. | Siempre; elige el evento a simular. |
| Instante del evento [s] | Momento desde el inicio del recorrido en que se inyecta el evento. | Solo si se selecciona una alarma o parada. |

Los campos muestran valores iniciales de ejemplo, no valores recomendados ni
medidos. **Velocidad constante** supone que el vehículo ya está en movimiento;
el CSV urbano ya incluye su propio perfil. Si se carga JSON, masa y potencia PEM
se siguen tomando de los campos visibles, mientras el resto viene del archivo.

### Parámetros avanzados del JSON

Si necesitas modificar los demás campos, copia `data/example.json` y cambia los
valores de `parameters`, manteniendo todos los nombres y unidades. La sección
`provenance` debe conservar una entrada por parámetro con `unit`, `status` y
`source`: unidad requerida, estado (`supuesto`, `confirmado` o `pendiente`) y
fuente del dato. Convierte los valores a las unidades indicadas antes de
introducirlos; el programa no convierte unidades.

| Sección y clave JSON | Unidad | Qué representa |
| --- | --- | --- |
| `vehicle.mass_kg` | kg | Masa total del vehículo; en la interfaz se introduce en Masa total. |
| `vehicle.rolling_coefficient` | adimensional | Coeficiente de resistencia a la rodadura de ruedas/superficie. |
| `vehicle.drag_coefficient` | adimensional | Coeficiente aerodinámico de arrastre. |
| `vehicle.frontal_area_m2` | m² | Área frontal expuesta al flujo de aire. |
| `vehicle.air_density_kg_m3` | kg/m³ | Densidad del aire usada en el cálculo aerodinámico. |
| `vehicle.rotational_mass_factor` | adimensional | Factor que aproxima la masa rotacional de ruedas y componentes giratorios; debe ser al menos 1. |
| `motor.efficiency` | adimensional (0–1) | Eficiencia mecánica del motor. |
| `motor.controller_efficiency` | adimensional (0–1) | Eficiencia del controlador del motor. |
| `motor.max_mechanical_power_w` | W | Límite de potencia mecánica del motor. |
| `fuel_cell.gross_power_w` | W | Potencia bruta máxima PEM; en la interfaz se introduce como Potencia bruta máxima PEM. |
| `fuel_cell.efficiency_lhv` | adimensional (0–1) | Eficiencia PEM calculada respecto al poder calorífico inferior (PCI) del hidrógeno. |
| `fuel_cell.auxiliary_power_w` | W | Potencia consumida por auxiliares propios de la PEM. |
| `fuel_cell.hydrogen_lhv_j_kg` | J/kg | Poder calorífico inferior del hidrógeno empleado. |
| `tank.volume_l` | L | Volumen interno del tanque. |
| `tank.initial_pressure_bar_abs` | bar absoluto | Presión inicial absoluta del tanque. |
| `tank.minimum_pressure_bar_abs` | bar absoluto | Presión de reserva; por debajo de ella el modelo deja de producir desde la PEM. |
| `tank.temperature_k` | K | Temperatura constante asumida para estimar el inventario de hidrógeno. |
| `tank.compressibility_factor` | adimensional | Factor Z constante usado en la estimación del gas real. |
| `capacitor.capacitance_f` | F | Capacitancia equivalente del banco completo, no de una celda individual. |
| `capacitor.minimum_voltage_v` | V | Tensión mínima permitida del banco. |
| `capacitor.maximum_voltage_v` | V | Tensión máxima permitida del banco. |
| `capacitor.initial_voltage_v` | V | Tensión del banco al inicio; debe quedar entre mínimo y máximo. |
| `capacitor.max_charge_power_w` | W | Potencia máxima de carga del banco. |
| `capacitor.max_discharge_power_w` | W | Potencia máxima de descarga del banco. |
| `capacitor.charge_efficiency` | adimensional (0–1) | Eficiencia del banco y su conversión al cargar. |
| `capacitor.discharge_efficiency` | adimensional (0–1) | Eficiencia del banco y su conversión al descargar. |
| `bus.fuel_cell_converter_efficiency` | adimensional (0–1) | Eficiencia del convertidor entre PEM y bus eléctrico. |
| `bus.auxiliary_converter_efficiency` | adimensional (0–1) | Eficiencia de conversión para cargas auxiliares. |
| `bus.auxiliary_load_w` | W | Potencia de las cargas auxiliares conectadas al bus. |
| `bus.capacitor_recharge_power_w` | W | Potencia permitida para recargar el banco desde la PEM. |
| `protection.detection_delay_s` | s | Retardo lógico de detección de alarma. |
| `protection.shutdown_delay_s` | s | Retardo lógico de apagado después de detección. |

Todos los parámetros numéricos deben ser finitos y no negativos; dimensiones,
capacidades y constantes indicadas por el validador deben ser mayores que cero.
Las eficiencias deben estar entre 0 (excluido) y 1 (incluido). Los valores del
archivo de ejemplo son supuestos educativos: confirma las fichas técnicas o
mediciones antes de usarlos como datos del vehículo.

## Escenarios por consola

```powershell
# Marcha sostenida y comparación de configuraciones
.\.venv\Scripts\python.exe -m simulador.cli --route data/routes/cruise.csv --compare --output results/cruise

# Alarma inyectada a los 60 segundos
.\.venv\Scripts\python.exe -m simulador.cli --fault hydrogen_alarm --fault-at 60 --output results/alarm

# Configuración propia y paso más pequeño
.\.venv\Scripts\python.exe -m simulador.cli --config data/example.json --step 0.5 --output results/fine
```

Cada ejecución exporta `timeseries.csv`, `events.csv`, `report.json` y
`plots.png`. Con `--compare` también genera `comparison.csv`. Reutilizar una
carpeta reemplaza esos archivos; usa carpetas distintas para conservar escenarios.
Los resultados locales no se incluyen en Git. `report.json` conserva parámetros,
recorrido, evento, paso temporal y procedencia para reproducir la ejecución.

## Datos y límites

El CSV debe tener `time_s,speed_kmh,grade_percent`, comenzar en tiempo cero y
usar tiempos crecientes. La pendiente corresponde al segmento que comienza en
esa fila. `data/routes/urban.csv` es un ejemplo ficticio; `cruise.csv` supone
velocidad inicial de 20 km/h.

Las gráficas muestran **velocidad y distancia objetivo**. Cuando aparece déficit,
el programa no calcula la velocidad real ni una autonomía alcanzable.
Las protecciones son eventos lógicos; no se modela una fuga real o su dispersión.
El tanque usa temperatura y compresibilidad constantes. Consulta las ecuaciones,
la arquitectura supuesta y las mejoras pendientes en [docs/MODELO.md](docs/MODELO.md).

Para comprobar conservación de energía, límites, entradas y la interfaz:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Las dependencias directas se declaran en `pyproject.toml`; las versiones de la
instalación comprobada se registran en `requirements-tested.txt` (Python 3.13,
Windows). No se requiere SciPy en esta versión: el balance se actualiza
algebraicamente por intervalos y no integra un sistema diferencial general.

No es necesario activar el entorno virtual. Modelos en `src/simulador`, datos
en `data`, pruebas en `tests` y salidas locales en `results`.

## Plan de implementación

1. Preparación del proyecto.
2. Configuración validada con unidades y procedencia.
3. Fuerzas y demanda mecánica del vehículo.
4. Demanda eléctrica del motor y pérdidas.
5. Generación PEM y consumo de hidrógeno.
6. Inventario y presión del tanque.
7. Energía y tensión del banco de supercapacitores.
8. Distribución de potencia y conversiones.
9. Recorridos y simulación temporal.
10. Eventos y protecciones simuladas.
11. Gráficas y exportación.
12. Interfaz Streamlit.
13. Validación física, comparación y documentación de límites.
