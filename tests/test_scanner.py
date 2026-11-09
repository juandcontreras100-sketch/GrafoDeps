from grafodeps.scanner import extract_imports, find_modules, scan_project


def test_find_modules_names(sample_project):
    assert sorted(find_modules(sample_project)) == [
        "shop", "shop.cart", "shop.lonely", "shop.main", "shop.pricing", "shop.tax", "shop.utils"]


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
