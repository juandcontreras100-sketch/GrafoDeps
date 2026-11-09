from grafodeps import model
from grafodeps.scanner import scan_project


def graph(p):
    return model.build_digraph(*scan_project(p))


def test_cycle_detected(sample_project):
    assert model.find_cycles(graph(sample_project)) == [["shop.pricing", "shop.tax"]]
    assert model.strongly_connected_groups(graph(sample_project)) == [["shop.pricing", "shop.tax"]]


def test_topological_order_none_when_cyclic_and_valid_when_acyclic():
    cyc = model.build_digraph(["a", "b"], [("a", "b"), ("b", "a")])
    assert model.topological_order(cyc) is None
    dag = model.build_digraph(["a", "b", "c"], [("a", "b"), ("b", "c")])
    assert model.topological_order(dag) == ["c", "b", "a"]  # dependencias primero


def test_degrees_sum_equals_edge_count(sample_project):
    g = graph(sample_project)
    rep = model.degree_report(g)
    assert sum(d["in"] for d in rep.values()) == g.number_of_edges() == sum(d["out"] for d in rep.values())
    assert rep["shop.tax"] == {"in": 1, "out": 1}


def test_shortest_path_and_subgraph(sample_project):
    g = graph(sample_project)
    assert model.shortest_dependency_path(g, "shop.main", "shop.tax") == [
        "shop.main", "shop.cart", "shop.pricing", "shop.tax"]
    assert model.shortest_dependency_path(g, "shop.utils", "shop.main") is None
    sub = model.dependency_subgraph(g, "shop.cart")
    assert set(sub) == {"shop.cart", "shop.pricing", "shop.tax"}
