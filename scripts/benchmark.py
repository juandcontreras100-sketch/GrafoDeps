"""Mide el tiempo de análisis (escaneo + ciclos + orden topológico) sobre un proyecto sintético de 50 módulos."""
import tempfile
import time
from pathlib import Path

from grafodeps import model
from grafodeps.scanner import scan_project


def make_project(root: Path, n: int = 50) -> None:
    (root / "big").mkdir(parents=True)
    (root / "big" / "__init__.py").write_text("")
    for i in range(n):
        deps = "".join(f"import big.m{j}\n" for j in range(i + 1, min(i + 4, n)))
        (root / "big" / f"m{i}.py").write_text(deps)


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as d:
        make_project(Path(d))
        runs = []
        for _ in range(5):
            t = time.perf_counter()
            g = model.build_digraph(*scan_project(d))
            model.find_cycles(g)
            model.topological_order(g)
            runs.append(time.perf_counter() - t)
        print(f"Módulos: {g.number_of_nodes()}  Aristas: {g.number_of_edges()}")
        print(f"Tiempo medio de 5 corridas: {sum(runs) / len(runs):.4f} s   (RNF-01: < 5 s)")
