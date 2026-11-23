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

Abre `http://127.0.0.1:8501`. La vista inicial es **Laboratorio interactivo**:
puedes manipular el cilindro directamente, sin cargar JSON ni ejecutar antes un
recorrido. Para el modelo del vehículo, selecciona **Recorrido y métricas**,
configura el escenario y pulsa **Ejecutar simulación**.
Encima de las pestañas aparece la energía eléctrica total que la PEM entregó
al bus durante el recorrido (Wh), el estado del cilindro frente a las
referencias ingresadas y los tiempos de detección y aislamiento si se simula
un evento de protección.
Sus pestañas muestran el simulador visual, métricas y tablas,
energía, eventos, parámetros usados, comparación y descargas. El formulario
aplica masa, potencia PEM y los campos del cilindro que rellenes sobre el JSON
cargado; los demás parámetros se conservan. Los archivos subidos se leen
en memoria. Para editar todos los parámetros, copia `data/example.json` y
mantén el formato de unidades y procedencia.

### Laboratorio interactivo

El laboratorio tiene una escena Canvas con partículas en movimiento, manómetro,
termómetro y salida hacia la PEM. Su interacción se inspira en la exploración
directa de [PhET](https://phet.colorado.edu/es/simulations/models-of-the-hydrogen-atom),
con una implementación propia sin copiar código ni imágenes. Aquí se representa
hidrógeno **molecular en un cilindro**, no un modelo del átomo.

- Mueve **Temperatura** o **Volumen interno**: la masa se conserva y la presión
  responde inmediatamente mediante `pV = ZmRT`. No hace falta pulsar Ejecutar.
- Pulsa **Abrir salida** sobre la escena o en el panel para consumir H₂ con el
  caudal solicitado. El inventario y la presión disminuyen; la extracción se
  detiene al alcanzar la reserva. El caudal es una entrada de este experimento;
  el laboratorio no calcula la demanda del vehículo ni la potencia PEM.
- **Pausar**, **Paso +1 s** y el ritmo **1× / 10× / 30×** controlan el tiempo.
  El movimiento molecular es ilustrativo y su rapidez visual depende de la
  temperatura. Se inicia en pausa si el sistema solicita movimiento reducido.
- Cambiar **Presión de carga** o pulsar **Recargar** comienza una serie nueva,
  conservando la temperatura y volumen actuales y cerrando la salida.
  **Reiniciar todo** restaura los datos de ejemplo y elimina las referencias.
- **Aislar salida** interrumpe el suministro inmediatamente por acción manual;
  **Rearmar salida** habilita volver a abrirla. No representa el retardo de
  detección/apagado del modelo de recorrido.
- Activa o desactiva partículas, corte y direcciones de movimiento en **Mostrar**.
- En **Referencias y modelo**, introduce tus límites de presión y temperatura,
  reserva y Z. Los rangos de los controles son rangos de exploración, no límites
  admisibles del cilindro. Sin referencias completas no se asigna estado verde.
- **Mediciones** muestra gráfica y tabla. **Descargar CSV** conserva las últimas
  5000 muestras, incluyendo tiempo, presión absoluta, temperatura, volumen, masa,
  caudal efectivo y motivo del cambio. Los cambios manuales de T o V pueden
  producir varias muestras en el mismo instante.

Los cambios de T y V son impuestos: no se calcula calor, trabajo, termodinámica
de descarga ni integridad estructural. Z permanece constante salvo edición
manual. No se crea gas para recuperar la reserva si un cambio de T/V deja el
estado por debajo de ella. El manómetro usa como escala la máxima de referencia
o el doble de la presión de carga; las lecturas numéricas conservan el valor
aunque la aguja llegue al tope.

La exploración se reinicia al recargar la página o cambiar de espacio de trabajo;
exporta las mediciones antes. No modifica los parámetros del modelo de recorrido.
**Descargar laboratorio para abrir sin conexión** genera un HTML autónomo con
los valores iniciales de ejemplo, sin CDN ni peticiones de red.

El motor Python y el laboratorio JavaScript se comprueban con:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
node --test tests/test_lab.cjs
```

Node.js solo se usa para estas comprobaciones, no para ejecutar el laboratorio.
Sin Node, pytest omite las comprobaciones de JavaScript e inventario cruzado.

### Explorar la simulación visual

La vista principal es **Cilindro animado**: un cilindro en corte con partículas
de gas en todo su volumen, manómetro, salida ilustrativa y conducto hacia la PEM.
Se muestra una vista inicial de ejemplo incluso antes de ejecutar un escenario.
Después de ejecutar, puedes observar el estado inicial en `0 s` y reproducir
el consumo calculado durante el recorrido. **Animar partículas y flujo** permite
detener el movimiento ilustrativo sin cambiar los datos ni la reproducción
temporal. También respeta la preferencia de movimiento reducido del sistema.

En la barra lateral, abre **Datos del cilindro** e introduce volumen, presión
inicial, presión de reserva y temperatura. Los campos vacíos conservan los datos
del JSON cargado o del ejemplo; los campos rellenados los sustituyen al pulsar
**Ejecutar simulación**. La temperatura se introduce en °C y se convierte a K
para el modelo y el informe. El factor de compresibilidad continúa viniendo del
JSON. El modelo mantiene la temperatura constante durante la descarga.

En **Límites de referencia del cilindro**, puedes introducir presión máxima y
temperaturas mínima y máxima de la ficha técnica. Todas las presiones se expresan
en **bar absolutos**; convierte primero si tu ficha indica presión manométrica.
No hay límites admisibles predeterminados. El contorno y la etiqueta muestran:

- **Azul:** sin referencias o referencias incompletas.
- **Verde:** presión y temperatura dentro de las tres referencias ingresadas.
- **Rojo:** se supera un límite conocido o se activa una alarma lógica simulada.
- **Ámbar:** reserva alcanzada o suministro aislado por la protección simulada.

Las etiquetas explican el estado también sin depender del color. Si se supera
una referencia conocida, se señala aunque falten las otras. Estos límites son
una comparación visual y **no introducen un apagado automático** en el balance
energético. El manómetro utiliza como escala la presión máxima ingresada; si no
existe, usa la inicial y lo indica expresamente. Se conserva el valor numérico
completo aunque la aguja llegue al tope de la escala.

El estado verde significa únicamente que las dos variables están dentro de las
referencias ingresadas. No significa «cilindro en perfectas condiciones»: no se
evalúan material, fatiga, daños, inspecciones ni pruebas físicas. Consulta el
contexto de [pruebas de tanques de hidrógeno del DOE](https://www.energy.gov/cmei/fuels/high-pressure-hydrogen-tank-testing).
Las partículas no representan velocidad molecular y la salida representa un
aislamiento lógico, sin simular una válvula física o una fuga. El informe JSON
conserva los parámetros efectivos, su procedencia y `inputs.cylinder_reference`.

En **Simulador visual → Flujo de energía** puedes ver el tanque, la celda PEM, el bus eléctrico,
el banco de supercapacitores y las cargas del vehículo. Las flechas muestran el
sentido del intercambio: el banco aporta al bus al descargar y recibe del bus
al cargar. Las líneas discontinuas indican que no hay intercambio. El esquema
también indica déficit, aislamiento del bus y el último evento registrado hasta
el instante seleccionado. En pantallas pequeñas se presenta un esquema textual.

- Usa **Intervalo del recorrido**, **Anterior**, **Siguiente** o **Volver al inicio**
  para inspeccionar los resultados.
- Activa **Reproducir recorrido** para avanzar automáticamente; desactívalo para
  pausar. **Intervalos por avance** permite recorrer más rápido las ejecuciones
  largas. Se actualiza cada medio segundo, sin representar tiempo real, y se
  detiene al final.
- Las potencias son promedios del intervalo indicado y el almacenamiento es el
  valor al final. Un apagado en la frontera final afecta al siguiente intervalo.
- El porcentaje del tanque representa el hidrógeno sobre la reserva, relativo
  al inventario utilizable inicial. El del banco representa energía utilizable
  entre sus tensiones mínima y máxima, calculada con el cuadrado de la tensión.

En **Métricas y tablas** encontrarás el resumen de la ejecución completa y la
serie temporal agrupada en **Recorrido**, **Potencia** y **Almacenamiento**.
Selecciona un rango de tiempo para consultar o descargar únicamente esas filas
con **Descargar tabla filtrada CSV**. Los tiempos corresponden al final de cada
intervalo; el resumen siempre corresponde a toda la ejecución.

Ambas vistas usan la última simulación ejecutada. Al ejecutar otro escenario,
el cursor visual y el rango de la tabla se reinician. La velocidad y distancia
mostradas siguen siendo **objetivos del recorrido**, incluso ante déficit o
apagado; el dibujo no representa movimiento real calculado ni regeneración.

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
| Volumen del cilindro [L] | Volumen interno del tanque. | Opcional; vacío conserva el JSON. |
| Presión inicial del cilindro [bar absolutos] | Presión del tanque al comenzar; debe superar la reserva. | Opcional; vacío conserva el JSON. |
| Presión de reserva [bar absolutos] | Presión a la que el modelo deja de extraer H₂. | Opcional; vacío conserva el JSON. |
| Temperatura del cilindro [°C] | Temperatura constante asumida; se convierte a K. | Opcional; vacío conserva el JSON. |
| Presión máxima y temperaturas de referencia | Límites proporcionados por el usuario para comparar el estado visual. | Opcionales; no modifican el modelo físico ni certifican el cilindro. |
| Pendiente para velocidad constante [%] | Inclinación de la vía; positiva es subida y negativa bajada. | Solo para velocidad constante. |
| Velocidad constante [km/h] | Velocidad objetivo mantenida durante el escenario. | Solo para velocidad constante. |
| Duración a velocidad constante [s] | Tiempo durante el que se mantiene esa velocidad. | Solo para velocidad constante. |
| Paso máximo [s] | Duración máxima de cada intervalo de cálculo. Menor valor da más detalle temporal y puede tardar más. | Siempre. |
| Evento de prueba | Sin fallo, alarma lógica de hidrógeno o parada de emergencia. | Siempre; elige el evento a simular. |
| Instante del evento [s] | Momento desde el inicio del recorrido en que se inyecta el evento. | Solo si se selecciona una alarma o parada. |

Los campos muestran valores iniciales de ejemplo, no valores recomendados ni
medidos. **Velocidad constante** supone que el vehículo ya está en movimiento;
el CSV urbano ya incluye su propio perfil. Si se carga JSON, masa y potencia PEM
se siguen tomando de los campos visibles; los campos opcionales del cilindro
solo reemplazan el archivo cuando se rellenan. El resto viene del archivo.

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
