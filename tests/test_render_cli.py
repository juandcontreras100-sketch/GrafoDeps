from grafodeps.cli import run
from grafodeps.model import build_digraph
from grafodeps.render import draw


def test_draw_writes_png(tmp_path):
    draw(build_digraph(["a", "b"], [("a", "b"), ("b", "a")]), tmp_path / "g.png")
    assert (tmp_path / "g.png").stat().st_size > 3000


def test_cli_end_to_end(sample_project, tmp_path, capsys):
    out = tmp_path / "grafo.png"
    code = run([str(sample_project), "--out", str(out), "--path", "shop.main", "shop.tax"])
    text = capsys.readouterr().out
    assert code == 0 and out.exists()
    assert "Dependencias circulares: 1" in text
    assert "shop.pricing -> shop.tax -> shop.pricing" in text
    assert "shop.main -> shop.cart -> shop.pricing -> shop.tax" in text


def test_cli_errors(tmp_path, sample_project):
    empty = tmp_path / "empty"
    empty.mkdir()
    assert run([str(empty)]) == 1
    assert run([str(sample_project), "--from", "nope"]) == 2


def test_cli_reports_syntax_error(tmp_path, capsys):
    (tmp_path / "bad.py").write_text("def (:\n")
    assert run([str(tmp_path)]) == 3
    assert "bad.py" in capsys.readouterr().err
