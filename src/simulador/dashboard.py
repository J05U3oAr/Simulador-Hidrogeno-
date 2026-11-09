"""Vistas Streamlit para explorar una ejecución guardada en memoria."""

import streamlit as st

from simulador.simulation import Result
from simulador.visualization import SERIES_GROUPS, energy_diagram, series_table, summary_table


def render_visual(result: Result):
    st.subheader("Explora el sistema paso a paso")
    st.caption("Recorre los intervalos calculados para ver cómo se reparte la energía. La reproducción es didáctica; no transcurre en tiempo real.")
    if st.session_state.pop("visual_finished", False):
        st.session_state["visual_playing"] = False
    controls = st.columns(2)
    playing = controls[0].toggle("Reproducir recorrido", key="visual_playing")
    stride = controls[1].selectbox("Intervalos por avance", [1, 5, 10, 30], key="visual_stride")

    def move_cursor(offset):
        current = st.session_state.get("visual_index", 0)
        st.session_state["visual_index"] = 0 if offset is None else max(0, min(len(result.rows) - 1, current + offset))

    @st.fragment(run_every=0.5 if playing else None)
    def player():
        last = len(result.rows) - 1
        pending = st.session_state.pop("visual_next_index", None)
        current = min(pending if playing and pending is not None else st.session_state.get("visual_index", 0), last)
        st.session_state["visual_index"] = current
        navigation = st.columns(3)
        navigation[0].button("Volver al inicio", disabled=playing, key="visual_restart",
                             on_click=move_cursor, args=(None,))
        navigation[1].button("Anterior", disabled=playing or current == 0, key="visual_previous",
                             on_click=move_cursor, args=(-stride,))
        navigation[2].button("Siguiente", disabled=playing or current == last, key="visual_next",
                             on_click=move_cursor, args=(stride,))
        if last:
            current = st.slider("Intervalo del recorrido", 0, last, key="visual_index", disabled=playing)
        row = result.rows[current]
        st.caption(f"Intervalo {current + 1} de {last + 1} · {row['time_s'] - row['dt_s']:.2f} a {row['time_s']:.2f} s. "
                   "Potencias promedio del intervalo; almacenamiento al final.")
        st.html(energy_diagram(result, row))
        st.progress(min(1.0, row["time_s"] / result.summary["duration_s"]),
                    text=f"Recorrido objetivo: {row['distance_target_km']:.3f} / {result.summary['distance_target_km']:.3f} km")
        st.caption("Las flechas indican el sentido del flujo; las líneas discontinuas indican que no hay intercambio. "
                   "La carga del banco proviene de la PEM; el modelo no recupera energía del frenado.")
        # El estado pertenece al intervalo que acaba de terminar: un evento en su
        # frontera final afecta al siguiente intervalo, como en el motor físico.
        visible_events = [event for event in result.events if event["time_s"] <= row["time_s"]]
        if visible_events:
            latest = visible_events[-1]
            st.info(f"Último evento hasta este instante: {latest['code']} · {latest['time_s']:.2f} s. {latest['detail']}")
        else:
            st.caption("Sin eventos registrados hasta este instante.")
        if playing:
            if current == last:
                st.session_state["visual_finished"] = True
                st.rerun()
            else:
                # El cursor se actualiza antes de crear el slider en el siguiente
                # fragmento; no se modifica una clave de widget ya renderizado.
                st.session_state["visual_next_index"] = min(last, current + stride)

    player()


def render_metrics(result: Result):
    st.subheader("Métricas de la ejecución completa")
    st.dataframe(summary_table(result), hide_index=True)
    st.caption("Las pérdidas corresponden a los elementos aguas arriba del bus. La distancia es la solicitada, sin estimar una distancia real alcanzable.")
    st.subheader("Tabla por intervalo")
    group = st.selectbox("Variables de la tabla", list(SERIES_GROUPS))
    first, last = result.rows[0]["time_s"], result.rows[-1]["time_s"]
    if first < last:
        start, end = st.slider("Rango de tiempo [s]", min_value=float(first), max_value=float(last),
                               value=(float(first), float(last)), key="table_time_range")
    else:
        start = end = first
        st.caption(f"La ejecución contiene un único intervalo, que termina en {last:g} s.")
    frame = series_table(result, group, start, end)
    st.caption(f"{len(frame)} de {len(result.rows)} intervalos. El tiempo identifica el final de cada intervalo.")
    if frame.empty:
        st.info("No hay intervalos en este rango; amplía la selección de tiempo.")
    else:
        st.dataframe(frame, hide_index=True)
    st.download_button("Descargar tabla filtrada CSV", frame.to_csv(index=False).encode("utf-8-sig"),
                       "tabla_filtrada.csv", "text/csv")
