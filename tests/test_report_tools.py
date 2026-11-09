import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs" / "informe"))
from build_report import build            # noqa: E402
from check_report import check            # noqa: E402
from make_diagrams import architecture    # noqa: E402

GOOD = """Título del proyecto
Autores
# 1. Resumen
Texto corto del resumen.

Palabras clave: grafos, dependencias, Python
# 2. Introducción
x
# 3. Objetivos
## 3.1 Objetivo General
Desarrollar una herramienta.
## 3.2 Objetivos Específicos
1. Investigar.
2. Diseñar.
3. Implementar.
# 4. Justificación y Planteamiento del Problema
## 4.1 Planteamiento del Problema
x
## 4.2 Justificación
x
# 5. Marco de Referencia
## 5.1 Marco Teórico
x
## 5.2 Marco Conceptual
x
## 5.3 Marco Tecnológico
x
# 6. Marco Metodológico — Metodología del Desarrollo
Scrum. Tipo de investigación: aplicada. Técnicas de recolección: revisión. Fases: tres.
# 7. Alcance del Proyecto
Usuarios: estudiantes. NO incluye Java.
# 8. Requerimientos del Sistema
## 8.1 Requerimientos Funcionales (RF)
RF-01 RF-02 RF-03 RF-04 RF-05 RF-06 RF-07 RF-08
## 8.2 Requerimientos No Funcionales (RNF)
RNF-01 RNF-02 RNF-03 RNF-04
# 9. Diseño del Sistema
G = (V, E)
![a](img/a.png)
![b](img/a.png)
![c](img/a.png)
# 10. Herramientas y Tecnología
Lenguaje, librerías, herramientas de desarrollo, herramientas de diseño.
# 11. Beneficios e Impacto Esperado
Beneficios técnicos, académicos, para el usuario y para la industria.
# 12. Recomendaciones para Versiones Futuras
x
# 13. Referencias Bibliográficas
A (2020). x.
B (2019). x.
C (2018). x.
D (2017). x.
E (2016). x.
F (2015). x.
# 14. Apéndices
Apéndice A Apéndice B Apéndice C Apéndice D
"""


def test_checker_accepts_valid_and_rejects_broken(tmp_path):
    (tmp_path / "img").mkdir()
    architecture(tmp_path / "img" / "a.png")
    md = tmp_path / "informe.md"
    md.write_text(GOOD, encoding="utf-8")
    assert check(md) == []
    md.write_text(GOOD.replace("# 7. Alcance del Proyecto", "# 7. Otra cosa").replace("NO incluye", ""), encoding="utf-8")
    assert any("Sección 7" in e or "Título" in e for e in check(md))
    md.write_text(GOOD.replace("1. Investigar.\n2. Diseñar.\n3. Implementar.", "1. Solo uno."), encoding="utf-8")
    assert any("Objetivos específicos" in e for e in check(md))


def test_builder_makes_docx(tmp_path):
    from docx import Document
    (tmp_path / "img").mkdir()
    architecture(tmp_path / "img" / "a.png")
    md = tmp_path / "informe.md"
    md.write_text(GOOD + "\n| a | b |\n|---|---|\n| 1 | **2** |\n", encoding="utf-8")
    out = build(md, tmp_path / "o.docx")
    d = Document(out)
    assert len(d.inline_shapes) == 3 and len(d.tables) == 1
    assert any(p.text.startswith("1. Resumen") or p.text == "1. Resumen" for p in d.paragraphs)
