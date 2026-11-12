"""Genera los 3 diagramas del informe (arquitectura, casos de uso, módulos/clases) con matplotlib."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Ellipse


def box(ax, x, y, w, h, text, fc="#deebf7", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", fc=fc, ec="#333", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p, q, label="", style="-|>", offset=(0.15, 0)):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle=style, color="#222", lw=1.3))
    if label:
        lx = (p[0] + q[0]) / 2 + offset[0]
        ly = (p[1] + q[1]) / 2 + offset[1]
        ax.text(lx, ly, label, fontsize=8, color="#7a0000",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#ccc", lw=0.6, alpha=0.95))


def canvas(w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off")
    return fig, ax


def architecture(out):
    fig, ax = canvas(10, 6.5)
    ax.text(5, 6.2, "Arquitectura de 3 capas de GrafoDeps", ha="center", fontsize=12, fontweight="bold")
    box(ax, 1, 4.4, 8, 1.3, "CAPA DE VISTA\nCLI: cli.py + render.py  ·  Web: webapp.py + HTML/CSS/JavaScript/SVG\nServidor HTTP de la biblioteca estándar, limitado a loopback", "#fee8c8", 8.5)
    box(ax, 1, 2.5, 8, 1.3, "CAPA DE LÓGICA\nmodel.py: grafo dirigido G = (V, E), ciclos elementales, valencias,\norden topológico, rutas mínimas y subgrafos (NetworkX)", "#deebf7", 9)
    box(ax, 1, 0.6, 8, 1.3, "CAPA DE DATOS\nscanner.py: escaneo del sistema de archivos y extracción de imports con ast", "#e5f5e0", 9)
    arrow(ax, (4.5, 4.4), (4.5, 3.8), label="solicita análisis", offset=(1.2, 0))
    arrow(ax, (4.5, 2.5), (4.5, 1.9), label="pide módulos y aristas", offset=(1.5, 0))
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


def use_cases(out):
    fig, ax = canvas(10, 6.5)
    ax.text(5, 6.2, "Diagrama de Casos de Uso — GrafoDeps", ha="center", fontsize=12, fontweight="bold")
    # Actor Desarrollador
    ax.add_patch(plt.Circle((1.2, 4.9), 0.28, fc="#ffffff", ec="#222", lw=1.3))  # cabeza
    ax.plot([1.2, 1.2], [3.8, 4.62], color="#222", lw=1.3)                       # tronco
    ax.plot([0.6, 1.8], [4.25, 4.25], color="#222", lw=1.3)                     # brazos
    ax.plot([1.2, 0.75], [3.8, 3.1], color="#222", lw=1.3)                      # pierna izq
    ax.plot([1.2, 1.65], [3.8, 3.1], color="#222", lw=1.3)                      # pierna der
    ax.text(1.2, 2.7, "Usuario\n(CLI / navegador local)", ha="center", fontsize=9, fontweight="bold")

    cases = [
        "CU-01: Cargar proyecto Python",
        "CU-02: Ver grafo de dependencias",
        "CU-03: Detectar ciclos elementales",
        "CU-04: Consultar valencias (δe y δs)",
        "CU-05: Obtener orden de construcción",
        "CU-06: Buscar camino entre módulos",
        "CU-07: Ver subgrafo de un módulo",
        "CU-08: Explorar grafo en navegador"
    ]
    for i, t in enumerate(cases):
        y = 5.55 - i * 0.66
        ax.add_patch(Ellipse((6.2, y), 5.2, 0.58, fc="#deebf7", ec="#333", lw=1.1))
        ax.text(6.2, y, t, ha="center", va="center", fontsize=8.5)
        ax.plot([1.9, 3.6], [4.25, y], color="#777", lw=0.9, ls="--")
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


def modules(out):
    fig, ax = canvas(11, 7.2)
    ax.text(5.5, 6.8, "Diagrama de Módulos y Funciones — GrafoDeps", ha="center", fontsize=12, fontweight="bold")

    box(ax, 0.3, 4.7, 3.2, 1.6, "cli.py (Vista)\n\nrun(argv) -> int\n[Interfaz de comandos]", "#fee8c8", 8)
    box(ax, 3.9, 4.7, 3.2, 1.6, "render.py (Vista)\n\ndraw(g, out, title)\n[PNG con Matplotlib]", "#fee8c8", 8)
    box(ax, 7.5, 4.7, 3.2, 1.6, "webapp.py + web/ (Vista)\n\nServidor local, API JSON\nHTML/CSS/JS/SVG; usa scanner/model", "#fee8c8", 8)
    box(ax, 1.2, 2.2, 8.6, 1.7,
        "model.py (Capa Lógica)\n\nbuild_digraph · find_cycles · degree_report · topological_order\nshortest_dependency_path · dependency_subgraph",
        "#deebf7", 8.5)
    box(ax, 1.2, 0.2, 8.6, 1.4,
        "scanner.py (Capa Datos)\n\nfind_modules · extract_imports · scan_project",
        "#e5f5e0", 8.5)

    arrow(ax, (1.9, 4.7), (3.4, 3.9))
    arrow(ax, (5.5, 4.7), (5.5, 3.9))
    arrow(ax, (9.1, 4.7), (7.5, 3.9))
    arrow(ax, (5.5, 2.2), (5.5, 1.6), label="descubre módulos y aristas", offset=(1.5, 0))

    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/informe/img")
    d.mkdir(parents=True, exist_ok=True)
    architecture(d / "arquitectura.png"); use_cases(d / "casos_de_uso.png"); modules(d / "modulos.png")
    print("diagramas en", d)
