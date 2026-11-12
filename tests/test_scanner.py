from grafodeps.scanner import extract_imports, find_modules, scan_project


def test_find_modules_names(sample_project):
    assert sorted(find_modules(sample_project)) == [
        "shop", "shop.cart", "shop.lonely", "shop.main", "shop.pricing", "shop.tax", "shop.utils"]


def test_find_modules_ignores_hidden_directories_and_pycache(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "module.py").write_text("", encoding="utf-8")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "secret.py").write_text("", encoding="utf-8")
    (tmp_path / "pkg" / "__pycache__").mkdir()
    (tmp_path / "pkg" / "__pycache__" / "cached.py").write_text("", encoding="utf-8")

    assert sorted(find_modules(tmp_path)) == ["pkg.module"]


def test_edges_ignore_external_libs_and_resolve_relative(sample_project):
    modules, edges = scan_project(sample_project)
    assert ("shop.main", "shop.cart") in edges          # import absoluto
    assert ("shop.main", "shop.utils") in edges         # from paquete import módulo
    assert ("shop.pricing", "shop.tax") in edges        # from . import tax
    assert ("shop.tax", "shop.pricing") in edges
    assert not any("os" in e or "json" in e for e in edges)
    assert all(a != b for a, b in edges)


def test_syntax_error_is_reported(tmp_path):
    import pytest
    (tmp_path / "bad.py").write_text("def (:\n")
    with pytest.raises(SyntaxError):
        extract_imports(tmp_path / "bad.py", "bad", {"bad"})


def test_relative_import_beyond_package_root_is_ignored(tmp_path):
    from grafodeps.scanner import scan_project

    package = tmp_path / "pkg"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "module.py").write_text("from .. import stray\n", encoding="utf-8")
    (tmp_path / "stray.py").write_text("", encoding="utf-8")

    _, edges = scan_project(tmp_path)

    assert ("pkg.module", "stray") not in edges


def test_python_source_encoding_cookie_is_respected(tmp_path):
    source = tmp_path / "legacy.py"
    source.write_bytes(b"# coding: latin-1\nname = 'caf\xe9'\n")

    assert extract_imports(source, "legacy", {"legacy"}) == set()


def test_src_layout_resolves_package_imports_from_project_root(tmp_path):
    source = tmp_path / "src"
    package = source / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text("from pkg import b\n", encoding="utf-8")
    (package / "b.py").write_text("", encoding="utf-8")

    modules, edges = scan_project(tmp_path)

    assert modules == ["pkg", "pkg.a", "pkg.b"]
    assert ("pkg.a", "pkg.b") in edges


def test_src_layout_resolves_imports_that_include_src_prefix(tmp_path):
    source = tmp_path / "src"
    package = source / "pkg"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "a.py").write_text(
        "from src.pkg import b\nimport src.pkg.b\n",
        encoding="utf-8",
    )
    (package / "b.py").write_text("", encoding="utf-8")

    modules, edges = scan_project(tmp_path)

    assert modules == ["pkg", "pkg.a", "pkg.b"]
    assert edges == [("pkg.a", "pkg.b")]
