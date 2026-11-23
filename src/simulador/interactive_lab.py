"""Laboratorio autónomo de manipulación directa del cilindro en HTML/Canvas."""

import json
from pathlib import Path

from simulador.config import Config
from simulador.tank import HYDROGEN_R_J_KG_K

ASSETS = Path(__file__).with_name("lab_assets")


def laboratory_html(config: Config) -> str:
    config.validate()
    bootstrap = {"tank": config.to_dict()["tank"], "gas_constant": HYDROGEN_R_J_KG_K}
    # El documento es autónomo: sin CDN, archivos externos ni peticiones de red.
    document = (ASSETS / "index.html").read_text(encoding="utf-8")
    assets = {
        "__LAB_CSS__": (ASSETS / "lab.css").read_text(encoding="utf-8"),
        "__LAB_BOOTSTRAP__": json.dumps(bootstrap, allow_nan=False).replace("<", "\\u003c"),
        "__LAB_PHYSICS__": (ASSETS / "physics.js").read_text(encoding="utf-8"),
        "__LAB_JS__": (ASSETS / "lab.js").read_text(encoding="utf-8"),
    }
    for marker, content in assets.items():
        document = document.replace(marker, content)
    return document


def render_laboratory(config: Config):
    import streamlit as st
    import streamlit.components.v1 as components

    document = laboratory_html(config)
    st.caption("Para ver la energía eléctrica que entrega la celda PEM, selecciona «Recorrido y métricas» y ejecuta una simulación.")
    components.html(document, height=1000, scrolling=True)
    st.download_button("Descargar laboratorio para abrir sin conexión", document,
                       "laboratorio_hidrogeno.html", "text/html")
    st.caption("Descarga el CSV para conservar las mediciones: la exploración se reinicia al cambiar de espacio o recargar la página. El modelo de recorrido usa su propio escenario y sus resultados.")
