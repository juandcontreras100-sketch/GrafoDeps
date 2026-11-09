"""Capa de vista: dibuja el grafo de dependencias en PNG (módulos en ciclos, en rojo)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from grafodeps.model import find_cycles


def draw(g: nx.DiGraph, out, title: str = "Grafo de dependencias") -> None:
    in_cycle = {v for c in find_cycles(g) for v in c}
    pos = nx.spring_layout(g, seed=42, k=1.4 / max(len(g), 1) ** 0.5)
    fig, ax = plt.subplots(figsize=(max(6, len(g) * 0.35), max(5, len(g) * 0.3)))
    colors = ["#e34a33" if v in in_cycle else "#9ecae1" for v in g]
    nx.draw_networkx_nodes(g, pos, node_color=colors, node_size=700, edgecolors="black", ax=ax)
    nx.draw_networkx_labels(g, pos, font_size=7, ax=ax)
    nx.draw_networkx_edges(g, pos, arrows=True, arrowstyle="-|>", node_size=700, edge_color="#555", ax=ax)
    ax.set_title(title + (f" — {len(in_cycle)} módulos en ciclos (rojo)" if in_cycle else " — sin ciclos"))
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
