import time

from grafodeps import model
from grafodeps.scanner import scan_project
from tests.conftest import write_project


def test_rnf01_50_modules_under_5_seconds(tmp_path):
    files = {"big/__init__.py": ""}
    for i in range(50):
        deps = "".join(f"import big.m{j}\n" for j in range(i + 1, min(i + 4, 50)))
        files[f"big/m{i}.py"] = deps
    write_project(tmp_path / "p", files)

    runs = []
    for _ in range(5):
        t = time.perf_counter()
        g = model.build_digraph(*scan_project(tmp_path / "p"))
        model.find_cycles(g)
        model.topological_order(g)
        runs.append(time.perf_counter() - t)

    assert max(runs) < 5
    assert g.number_of_nodes() == 51
    assert g.number_of_edges() == 144
