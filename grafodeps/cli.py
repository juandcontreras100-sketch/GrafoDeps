"""Punto de entrada: python -m grafodeps.cli PROYECTO [--out grafo.png] [--from MODULO] [--path A B]"""
import argparse
import sys

from grafodeps import model, render
from grafodeps.scanner import scan_project


def run(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows: evita UnicodeEncodeError con δ al redirigir la salida
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="grafodeps", description="Analiza dependencias entre módulos Python con grafos.")
    ap.add_argument("project", help="carpeta raíz del proyecto Python")
    ap.add_argument("--out", help="ruta del PNG a generar")
    ap.add_argument("--from", dest="root_module", help="muestra solo las dependencias transitivas de este módulo")
    ap.add_argument("--path", nargs=2, metavar=("ORIGEN", "DESTINO"), help="camino más corto de dependencia")
    args = ap.parse_args(argv)

    try:
        modules, edges = scan_project(args.project)
    except SyntaxError as exc:
        print(f"No se pudo analizar {exc.filename}: {exc.msg} (línea {exc.lineno})", file=sys.stderr)
        return 3
    if not modules:
        print("No se encontraron módulos .py", file=sys.stderr)
        return 1
    g = model.build_digraph(modules, edges)
    if args.root_module:
        if args.root_module not in g:
            print(f"Módulo desconocido: {args.root_module}", file=sys.stderr)
            return 2
        g = model.dependency_subgraph(g, args.root_module)

    print(f"Módulos |V| = {g.number_of_nodes()}   Dependencias |E| = {g.number_of_edges()}")

    cycles = model.find_cycles(g)
    print(f"Dependencias circulares: {len(cycles)}")
    for c in cycles:
        print("  " + " -> ".join(c + [c[0]]))
    order = model.topological_order(g)
    build_order = list(reversed(order)) if order else None
    print("Orden de construcción: " + (" , ".join(build_order) if build_order else "no existe (hay ciclos)"))
    print("Valencias (entrada/salida):")
    for v, d in model.degree_report(g).items():
        print(f"  {v}: δe={d['in']} δs={d['out']}")
    if args.path:
        p = model.shortest_dependency_path(g, *args.path)
        print("Camino: " + (" -> ".join(p) if p else "no existe"))
    if args.out:
        render.draw(g, args.out)
        print(f"Imagen guardada en {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
