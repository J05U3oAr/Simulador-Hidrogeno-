"""Ejecución por consola desde la raíz del repositorio."""

import argparse
import json

from simulador.config import load_config
from simulador.protection import Fault
from simulador.reporting import export_result
from simulador.route import load_route
from simulador.simulation import simulate


def main():
    parser = argparse.ArgumentParser(description="Simulación energética preliminar de vehículo PEM")
    parser.add_argument("--config", default="data/example.json")
    parser.add_argument("--route", default="data/routes/urban.csv")
    parser.add_argument("--step", type=float, default=1, help="Paso máximo [s]")
    parser.add_argument("--output", default="results/latest", help="Carpeta de salida; reemplaza archivos del mismo nombre")
    parser.add_argument("--fault", choices=["none", "hydrogen_alarm", "emergency_stop"], default="none")
    parser.add_argument("--fault-at", type=float, default=0, help="Instante del fallo [s]")
    args = parser.parse_args()
    try:
        config, provenance = load_config(args.config)
        result = simulate(config, load_route(args.route), args.step, Fault(args.fault, args.fault_at))
        directory = export_result(result, args.output, provenance)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result.summary, ensure_ascii=False, indent=2))
    print(f"Resultados: {directory.resolve()}")


if __name__ == "__main__":
    main()
