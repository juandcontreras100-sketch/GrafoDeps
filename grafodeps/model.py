"""Capa de lógica: modelo matemático G = (V, E) y análisis con teoría de grafos."""
import networkx as nx


def build_digraph(modules: list[str], edges: list[tuple[str, str]]) -> nx.DiGraph:
    """V = módulos; (a, b) ∈ E ⊆ V×V significa «a importa b»."""
    g = nx.DiGraph()
    g.add_nodes_from(modules)
    g.add_edges_from(edges)
    return g


def find_cycles(g: nx.DiGraph) -> list[list[str]]:
    """Circuitos simples dirigidos (dependencias circulares), normalizados y ordenados."""
    cycles = []
    for c in nx.simple_cycles(g):
        i = c.index(min(c))
        cycles.append(c[i:] + c[:i])
    return sorted(cycles)


def degree_report(g: nx.DiGraph) -> dict[str, dict[str, int]]:
    """Valencia de entrada δe (cuántos lo importan) y de salida δs (a cuántos importa)."""
    return {v: {"in": g.in_degree(v), "out": g.out_degree(v)} for v in sorted(g)}


def topological_order(g: nx.DiGraph) -> list[str] | None:
    """Ordena los vértices para que cada origen preceda a sus destinos; None si hay ciclos."""
    if not nx.is_directed_acyclic_graph(g):
        return None
    return list(nx.lexicographical_topological_sort(g))


def shortest_dependency_path(g: nx.DiGraph, src: str, dst: str) -> list[str] | None:
    try:
        return nx.shortest_path(g, src, dst)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def dependency_subgraph(g: nx.DiGraph, root: str) -> nx.DiGraph:
    """Subgrafo inducido por `root` y todo lo que alcanza (sus dependencias transitivas)."""
    return g.subgraph({root} | nx.descendants(g, root)).copy()


def strongly_connected_groups(g: nx.DiGraph) -> list[list[str]]:
    """Componentes fuertemente conexas con más de un módulo (grupos con dependencia mutua)."""
    return sorted(sorted(c) for c in nx.strongly_connected_components(g) if len(c) > 1)
