# Alcance y ecuaciones de la versión 0.1

Esta versión cubre las 13 etapas del plan a nivel de **modelo preliminar**.
Las comprobaciones actuales verifican cálculos y contratos del programa; todavía
no existe validación experimental contra el vehículo ni fichas técnicas aprobadas.
Todos los valores del archivo inicial están marcados como supuestos.
El JSON exige todas las claves y las unidades exactas del ejemplo (`m^2`,
`kg/m^3`, `bar absoluto`, etc.). No convierte unidades automáticamente: convertir
las fichas técnicas antes de introducir sus valores.

## Demanda y recorrido

Se prescribe una velocidad lineal entre puntos del CSV. La pendiente de cada fila
se mantiene hasta la siguiente; la pendiente de la última fila no se usa.
Una velocidad inicial distinta de cero supone un vehículo ya en movimiento.

Con `theta = atan(pendiente_porcentaje / 100)`:

```text
F_rodadura = m g Crr cos(theta)
F_aerodinamica = 0.5 rho Cd A v²
F_pendiente = m g sin(theta)
F_aceleracion = m factor_rotacional a
P_mecanica = (F_rodadura + F_aerodinamica + F_pendiente + F_aceleracion) v
P_bus_motor = max(P_mecanica, 0) / (eta_motor eta_controlador)
```

La potencia mecánica está limitada por el motor. El exceso se registra como
demanda no cubierta equivalente en el bus. No se simula el control de velocidad,
la curva par/velocidad ni la adherencia. Una potencia negativa se registra como
frenado mecánico, sin recuperación de energía. No se representa viento.

La distancia es la integral de la **velocidad objetivo**, incluso cuando falta
potencia o se apaga el bus. No debe interpretarse como distancia real alcanzada.
La viabilidad indicada sólo significa que se cubrió la potencia objetivo del modelo.
No implica validación térmica, eléctrica, mecánica o de seguridad.

## PEM, auxiliares y conversiones

```text
P_bruta = min(P_bruta_maxima, P_neta_solicitada + P_auxiliares_PEM)
flujo_H2 = P_bruta / (eta_PEM_PCI PCI_H2)
P_bus_PEM = (P_bruta - P_auxiliares_PEM) eta_convertidor_PEM
P_auxiliares_bus = P_auxiliares_12V / eta_convertidor_auxiliar
```

La PEM usa una eficiencia constante sobre PCI y modula instantáneamente. No
incluye calentamiento, arranque, purgas, consumo en espera, rampa, curva V-I ni
variación de eficiencia con carga. Al no solicitar potencia se considera apagada.
El calor estimado de la celda no incluye los auxiliares; el balance de pérdidas
del sistema sí incluye calor, auxiliares PEM y pérdidas de conversión.

Se supone un convertidor PEM/bus y un convertidor bidireccional banco/bus.
Son **hipótesis de arquitectura**, no elementos confirmados del diagrama.
No se asume que un banco de supercapacitores estabilice por sí solo la tensión.
La batería auxiliar de 12 V no tiene estado de carga propio: sus cargas se
reflejan como consumo equivalente del bus. No se simula su arranque o respaldo.

## Tanque

```text
m = p_absoluta V / (Z R_H2 T)
p_absoluta = m Z R_H2 T / V
```

Se usa `R_H2 = 4124.2 J/(kg K)`. Volumen en litros se convierte a m³ y bar a Pa.
Temperatura y factor de compresibilidad Z se mantienen constantes. El ejemplo
Z=1.15 es un supuesto ilustrativo, no una propiedad validada para todo el rango.
En alta presión se necesita una ecuación de estado o tabla validada Z(p,T) para
mejorar el inventario. No se simulan regulador, caudal máximo, pérdidas en tubería,
presión de alimentación PEM, válvulas, alivio ni temperatura de descarga.
La presión mínima es una reserva configurable del tanque, no la presión de la PEM.

## Supercapacitores y distribución

```text
E = 0.5 C_equivalente V²
E_utilizable = 0.5 C_equivalente (V_max² - V_min²)
Descarga: E_final = E_inicial - P_bus dt / eta_descarga
Carga:    E_final = E_inicial + abs(P_bus) dt eta_carga
```

Se limita la potencia y la energía por intervalo. Las eficiencias agregan las
pérdidas del banco y su conversión; no representan ESR, corriente máxima,
balanceo de celdas, autodescarga ni temperaturas. La capacitancia configurada es
del **banco equivalente**, no de una celda individual. Se debe obtener de su
configuración serie/paralelo antes de usar datos comerciales.

La PEM atiende la carga más una potencia de recarga limitada; el banco cubre
el déficit o almacena el excedente. Al alcanzar la reserva del tanque deja de
haber generación PEM y el banco puede continuar hasta su mínimo. Si el tanque
se agota durante un intervalo, su aporte es el promedio de la fracción activa.

Se verifica en cada paso:

```text
P_PEM_bus + P_banco_bus + P_no_servida = P_carga_aceptada
E_quimica + E_banco_inicial - E_banco_final = E_servida_bus + E_perdidas_aguas_arriba
```

Las pérdidas exportadas son aguas arriba del bus; no suman las pérdidas del
motor/controlador ni energía de frenado. La demanda rechazada por límite del
motor sí se incluye en la energía total no cubierta del resumen.

## Tiempo y protecciones

Se subdivide cada segmento en intervalos de duración menor o igual al paso
elegido. Fuerzas/potencias se evalúan a velocidad media; el balance de energía
se actualiza algebraicamente. La distancia y la energía cinética para aceleración
constante se integran exactamente; la parte aerodinámica tiene error numérico.
Repetir con un paso menor permite evaluar convergencia.

Los instantes programados de fallo, alarma y aislamiento se incluyen como
fronteras exactas de paso. Los límites de energía/presión se registran al final
del intervalo donde se alcanzan. El apagado lógico aísla PEM y banco del bus;
no modela la energía residual, válvulas o contactores del vehículo real.
El modelo no permite descargar el banco por debajo de V_min ni sobrecargarlo
por encima de V_max. Alcanzar un límite genera un evento; no simula una avería
física del componente. El motor limita potencia y registra sobrecarga solicitada.

`hydrogen_alarm` representa el inicio de una condición lógica de detección más
el retardo configurado. No extrae masa del tanque por una fuga, ni predice
concentración, dispersión, inflamabilidad o ubicación adecuada de sensores.

## Comparación y siguientes mejoras

La comparación varía masa, potencia neta máxima PEM y capacitancia en ±20%,
un factor a la vez. Conserva los demás parámetros, el recorrido y el fallo.
Es análisis de sensibilidad; no es una estimación estadística de incertidumbre.

Antes de dimensionar hardware: confirmar fichas técnicas y curvas, conversiones,
consumos auxiliares, topología del banco, rango del controlador y arquitectura
de aislamiento. Después incorporar límites de corriente/par, térmica,
regulador/caudales, batería de 12 V y validar contra mediciones supervisadas.
La autonomía total hasta agotar recursos queda pendiente de un recorrido válido
repetible y modelos calibrados; esta versión entrega duración y consumo del
recorrido cargado sin extrapolar una autonomía garantizada.

## Referencias de herramientas y alcance

- [Streamlit: AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), usado para comprobar ejecución e interacciones.
- [Streamlit: gráficas](https://docs.streamlit.io/develop/api-reference/charts/st.line_chart).
- [DOE: uso seguro del hidrógeno](https://www.energy.gov/cmei/fuels/safe-use-hydrogen), contexto sobre ventilación y detección que este modelo no sustituye.
