"""Convierte docs/informe/informe.md (subconjunto de Markdown) en .docx con python-docx.

Soporta: encabezados #..###, párrafos, viñetas '- ', listas '1. ', tablas con pipes,
imágenes ![alt](ruta) y **negrita**. Las líneas antes del primer '# ' forman la portada.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.shared import Cm


def _runs(par, text):
    for i, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        if chunk:
            par.add_run(chunk).bold = (i % 2 == 1)


def build(md_path, out_path):
    md_path = Path(md_path)
    doc = Document()
    lines = md_path.read_text(encoding="utf-8").splitlines()
    i, in_cover, first_cover = 0, True, True
    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("# ") and in_cover:
            in_cover = False
            doc.add_page_break()
        if in_cover:
            if line.strip():
                if first_cover:
                    doc.add_heading(line.strip(), 0); first_cover = False
                else:
                    doc.add_paragraph(line.strip())
            i += 1
            continue
        m = re.match(r"^(#{1,3}) (.+)$", line)
        img = re.match(r"^!\[(.*?)\]\((.+?)\)$", line.strip())
        if m:
            doc.add_heading(m.group(2), len(m.group(1)))
        elif img:
            p = md_path.parent / img.group(2)
            doc.add_picture(str(p), width=Cm(14))
            cap = doc.add_paragraph(img.group(1)); cap.italic = True
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            t = doc.add_table(rows=len(rows), cols=len(rows[0]))
            t.style = "Light Grid Accent 1"
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    t.cell(r, c).text = val
            continue
        elif line.startswith("- "):
            _runs(doc.add_paragraph(style="List Bullet"), line[2:])
        elif re.match(r"^\d+\. ", line):
            _runs(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", line))
        elif line.strip():
            _runs(doc.add_paragraph(), line.strip())
        i += 1
    doc.save(out_path)
    return Path(out_path)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "docs/informe/informe.md"
    dst = sys.argv[2] if len(sys.argv) > 2 else "Proyecto_de_Aula_GrafoDeps.docx"
    print(build(src, dst))
