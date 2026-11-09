"""Capa de datos: lee un proyecto Python y extrae V (módulos) y E (importaciones internas)."""
import ast
from pathlib import Path


def module_name(root: Path, file: Path) -> str:
    """app/util/__init__.py -> 'app.util'; app/main.py -> 'app.main'."""
    parts = list(file.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def find_modules(root: str | Path) -> dict[str, Path]:
    root = Path(root)
    mods = {}
    for f in sorted(root.rglob("*.py")):
        if any(p.startswith(".") or p == "__pycache__" for p in f.relative_to(root).parts):
            continue
        name = module_name(root, f)
        if name:
            mods[name] = f
    return mods


def _longest_known(name: str, known: set[str]) -> str | None:
    parts = name.split(".")
    while parts:
        cand = ".".join(parts)
        if cand in known:
            return cand
        parts.pop()
    return None


def extract_imports(file: Path, current: str, known: set[str]) -> set[str]:
    """Módulos internos importados por `file`. Ignora librerías externas y autoimportaciones."""
    is_pkg = file.name == "__init__.py"
    package = current if is_pkg else current.rpartition(".")[0]
    deps: set[str] = set()
    tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _longest_known(alias.name, known)
                if hit:
                    deps.add(hit)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package.split(".") if package else []
                base_parts = base_parts[: len(base_parts) - (node.level - 1)] if node.level > 1 else base_parts
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            for alias in node.names:
                hit = _longest_known(f"{base}.{alias.name}" if base else alias.name, known) \
                    or _longest_known(base, known)
                if hit:
                    deps.add(hit)
    deps.discard(current)
    return deps


def scan_project(root: str | Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Devuelve (módulos ordenados, aristas ordenadas (importador, importado))."""
    mods = find_modules(root)
    known = set(mods)
    edges = sorted((m, d) for m, f in mods.items() for d in extract_imports(f, m, known))
    return sorted(mods), edges
