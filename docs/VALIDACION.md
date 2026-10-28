# Comprobación inicial — 27 de octubre de 2026

Entorno: Windows, Python 3.13.7. Dependencias instaladas en `.venv`; versiones
registradas en `requirements-tested.txt`.

## Verificaciones ejecutadas

- `python -m pytest -q`: **44 pruebas aprobadas**.
- Conservación de energía del bus y banco, carga/descarga y agotamiento parcial
  del combustible; presión mínima y límites de tensión.
- Escalamiento aerodinámico, energía de aceleración y convergencia temporal.
- Validación de parámetros, unidades, procedencia y recorridos.
- Apagado entre pasos regulares, cese de generación y consumo tras aislamiento.
- Lectura del CSV exportado y apertura del PNG generado.
- AppTest: ejecución inicial, simulación, comparación y entrada inválida sin
  conservar resultados anteriores.
- Revisión visual de formulario y gráficas del escenario urbano en Brave.
  No se ha efectuado una revisión completa de accesibilidad o pantallas móviles.

## Escenarios de ejemplo ejecutados

Valores ilustrativos; no describen un vehículo construido.

| Escenario | Duración | Distancia objetivo | H₂ consumido | Resultado |
|---|---:|---:|---:|---|
| Urbano | 300 s | 1.833 km | 2.124 g | Demanda cubierta en el modelo |
| Crucero a 20 km/h | 600 s | 3.333 km | 3.012 g | Demanda cubierta en el modelo |
| Urbano con alarma a 60 s | 300 s | 1.833 km | 0.614 g | Aislamiento a 61.5 s; demanda posterior no cubierta |

Se ejecutó la comparación de siete casos por consola. Los archivos se generan
en `results/`, excluido de Git. El error máximo del balance de potencia en estos
escenarios fue menor a `1e-9 W`.

Streamlit emitió avisos de deprecación de una llamada interna a pandas. Matplotlib
no pudo guardar su caché de fuentes fuera del proyecto bajo el entorno
restringido; sí generó las gráficas, que se abrieron y verificaron.

No se ha realizado validación experimental ni contraste de los parámetros con
fichas técnicas de los componentes. Consultar [MODELO.md](MODELO.md) antes de
interpretar resultados para dimensionamiento.
