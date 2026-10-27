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
