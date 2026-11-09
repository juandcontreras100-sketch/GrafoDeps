"""Genera los 3 diagramas del informe (arquitectura, casos de uso, módulos/clases) con matplotlib."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse


def box(ax, x, y, w, h, text, fc="#deebf7", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, label="", style="-|>"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, color="#333", lw=1.2))
    if label:
        ax.text((p[0] + q[0]) / 2 + 0.1, (p[1] + q[1]) / 2, label, fontsize=8, color="#7a0000")


def canvas(w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def architecture(out):
    fig, ax = canvas(10, 6.5)
    ax.text(5, 6.2, "Arquitectura de 3 capas de GrafoDeps", ha="center", fontsize=12, fontweight="bold")
    box(ax, 1, 4.4, 8, 1.3, "CAPA DE VISTA\ncli.py (línea de comandos)  ·  render.py (PNG con matplotlib)", "#fee8c8")
    box(ax, 1, 2.5, 8, 1.3, "CAPA DE LÓGICA\nmodel.py: grafo dirigido G = (V, E), ciclos, valencias,\norden topológico, caminos, subgrafos (NetworkX)", "#deebf7")
    box(ax, 1, 0.6, 8, 1.3, "CAPA DE DATOS\nscanner.py: lee archivos .py del proyecto y extrae importaciones con ast", "#e5f5e0")
    arrow(ax, (5, 4.4), (5, 3.8), "solicita análisis"); arrow(ax, (5, 2.5), (5, 1.9), "pide módulos y aristas")
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


def use_cases(out):
    fig, ax = canvas(10, 6.5)
    ax.text(5, 6.2, "Casos de uso", ha="center", fontsize=12, fontweight="bold")
    ax.text(1, 3.2, "Desarrollador", ha="center", fontsize=10, fontweight="bold")
    ax.plot([1, 1], [3.6, 4.4], "k"); ax.add_patch(plt.Circle((1, 4.7), 0.3, fc="white", ec="k"))
    ax.plot([0.5, 1.5], [4.2, 4.2], "k"); ax.plot([1, 0.6], [3.6, 3.3], "k"); ax.plot([1, 1.4], [3.6, 3.3], "k")
    cases = ["CU-01 Cargar proyecto Python", "CU-02 Ver grafo de dependencias", "CU-03 Detectar ciclos",
             "CU-04 Consultar valencias", "CU-05 Obtener orden de construcción", "CU-06 Buscar camino entre módulos",
             "CU-07 Ver subgrafo de un módulo"]
    for i, t in enumerate(cases):
        y = 5.4 - i * 0.75
        ax.add_patch(Ellipse((6, y), 5, 0.6, fc="#deebf7", ec="#333"))
        ax.text(6, y, t, ha="center", va="center", fontsize=9)
        ax.plot([1.6, 3.5], [4.4, y], color="#888", lw=0.8)
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


def modules(out):
    fig, ax = canvas(11, 6)
    ax.text(5.5, 5.7, "Diagrama de módulos y funciones", ha="center", fontsize=12, fontweight="bold")
    box(ax, 0.3, 3.2, 2.8, 1.8, "cli.py\n\nrun(argv) -> int", "#fee8c8", 9)
    box(ax, 4.0, 3.2, 3.0, 1.8, "render.py\n\ndraw(g, out, title)", "#fee8c8", 9)
    box(ax, 4.0, 0.4, 3.2, 2.2, "model.py\n\nbuild_digraph\nfind_cycles\ndegree_report\ntopological_order\nshortest_dependency_path\ndependency_subgraph", "#deebf7", 8)
    box(ax, 8.0, 0.4, 2.8, 2.2, "scanner.py\n\nfind_modules\nextract_imports\nscan_project", "#e5f5e0", 8)
    arrow(ax, (1.7, 3.2), (4.3, 2.2), "usa"); arrow(ax, (3.1, 4.1), (4.0, 4.1), "usa")
    arrow(ax, (1.7, 3.2), (8.3, 2.6), "usa"); arrow(ax, (5.5, 3.2), (5.5, 2.6), "usa")
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/informe/img")
    d.mkdir(parents=True, exist_ok=True)
    architecture(d / "arquitectura.png"); use_cases(d / "casos_de_uso.png"); modules(d / "modulos.png")
    print("diagramas en", d)
