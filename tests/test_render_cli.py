from matplotlib import image as mpl_image

from grafodeps.cli import run
from grafodeps.model import build_digraph
from grafodeps.render import draw


def test_draw_writes_deterministic_png_and_highlights_cycles(tmp_path):
    graph = build_digraph(["a", "b"], [("a", "b"), ("b", "a")])
    first, second = tmp_path / "first.png", tmp_path / "second.png"
    draw(graph, first)
    draw(graph, second)

    pixels = mpl_image.imread(first)
    assert first.stat().st_size > 3000
    assert first.read_bytes() == second.read_bytes()
    assert ((pixels[:, :, 0] > 0.7) & (pixels[:, :, 1] < 0.5) & (pixels[:, :, 2] < 0.4)).any()


def test_cli_help_is_in_spanish(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc_info:
        run(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "Analiza dependencias" in output
    assert "carpeta raíz" in output


def test_cli_report_is_deterministic(sample_project, capsys):
    run([str(sample_project)])
    first = capsys.readouterr().out
    run([str(sample_project)])
    second = capsys.readouterr().out

    assert first == second


def test_cli_end_to_end(sample_project, tmp_path, capsys):
    out = tmp_path / "grafo.png"
    code = run([str(sample_project), "--out", str(out), "--path", "shop.main", "shop.tax"])
    text = capsys.readouterr().out
    assert code == 0 and out.exists()
    assert "Dependencias circulares: 1" in text
    assert "shop.pricing -> shop.tax -> shop.pricing" in text
    assert "shop.main -> shop.cart -> shop.pricing -> shop.tax" in text


def test_cli_from_restricts_report_to_transitive_dependencies(sample_project, capsys):
    code = run([str(sample_project), "--from", "shop.cart", "--path", "shop.cart", "shop.tax"])
    text = capsys.readouterr().out
    assert code == 0
    assert "Módulos |V| = 3   Dependencias |E| = 3" in text
    assert "Dependencias circulares: 1" in text
    assert "shop.cart -> shop.pricing -> shop.tax" in text
    assert "shop.main" not in text
    assert "shop.utils" not in text


def test_cli_errors(tmp_path, sample_project, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run([str(empty)]) == 1
    assert "No se encontraron módulos" in capsys.readouterr().err
    assert run([str(sample_project), "--from", "nope"]) == 2
    assert "Módulo desconocido: nope" in capsys.readouterr().err


def test_cli_reports_syntax_error(tmp_path, capsys):
    (tmp_path / "bad.py").write_text("def (:\n")
    assert run([str(tmp_path)]) == 3
    assert "bad.py" in capsys.readouterr().err
