"""Capa de datos: lee un proyecto Python y extrae V (módulos) y E (importaciones internas)."""
import ast
import tokenize
from pathlib import Path


def module_name(root: Path, file: Path) -> str:
    """app/util/__init__.py -> 'app.util'; app/main.py -> 'app.main'."""
    parts = list(file.relative_to(root).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def find_modules(root: str | Path) -> dict[str, Path]:
    root = Path(root)
    source_root = root / "src"
    if source_root.is_dir() and any(source_root.rglob("*.py")):
        root = source_root
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


def _normalize_absolute_import(name: str, src_layout: bool) -> str:
    if src_layout and name.startswith("src."):
        return name[4:]
    return name


def extract_imports(
    file: Path,
    current: str,
    known: set[str],
    *,
    src_layout: bool = False,
) -> set[str]:
    """Módulos internos importados por `file`. Ignora librerías externas y autoimportaciones."""
    is_pkg = file.name == "__init__.py"
    package = current if is_pkg else current.rpartition(".")[0]
    deps: set[str] = set()
    with tokenize.open(file) as source:
        tree = ast.parse(source.read(), filename=str(file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hit = _longest_known(_normalize_absolute_import(alias.name, src_layout), known)
                if hit:
                    deps.add(hit)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base_parts = package.split(".") if package else []
                if node.level > len(base_parts):
                    continue
                base_parts = base_parts[: len(base_parts) - (node.level - 1)] if node.level > 1 else base_parts
                base = ".".join(base_parts + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            for alias in node.names:
                candidate = f"{base}.{alias.name}" if base else alias.name
                normalized_base = _normalize_absolute_import(base, src_layout)
                candidate = _normalize_absolute_import(candidate, src_layout)
                hit = _longest_known(candidate, known) or _longest_known(normalized_base, known)
                if hit:
                    deps.add(hit)
    deps.discard(current)
    return deps


def scan_project(root: str | Path) -> tuple[list[str], list[tuple[str, str]]]:
    """Devuelve (módulos ordenados, aristas ordenadas (importador, importado))."""
    root = Path(root)
    source_root = root / "src"
    src_layout = source_root.is_dir() and any(source_root.rglob("*.py"))
    mods = find_modules(root)
    known = set(mods)
    edges = sorted(
        (module, dependency)
        for module, file in mods.items()
        for dependency in extract_imports(file, module, known, src_layout=src_layout)
    )
    return sorted(mods), edges
