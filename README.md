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
