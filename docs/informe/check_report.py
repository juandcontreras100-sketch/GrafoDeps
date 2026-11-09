"""Verifica que informe.md cumpla la rúbrica del documento «Proyecto de Aula». Salida 0 = todo bien."""
import re
import sys
from pathlib import Path

TITLES = ["Resumen", "Introducción", "Objetivos", "Justificación y Planteamiento del Problema",
          "Marco de Referencia", "Marco Metodológico", "Alcance del Proyecto", "Requerimientos del Sistema",
          "Diseño del Sistema", "Herramientas y Tecnología", "Beneficios e Impacto Esperado",
          "Recomendaciones para Versiones Futuras", "Referencias Bibliográficas", "Apéndices"]


def sections(text: str) -> dict[int, str]:
    parts = re.split(r"^# (\d+)\. .*$", text, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def words(s: str) -> int:
    return len(re.findall(r"\w+", s, flags=re.U))


def check(md_path) -> list[str]:
    md_path = Path(md_path)
    text = md_path.read_text(encoding="utf-8")
    errs: list[str] = []
    heads = re.findall(r"^# (\d+)\. (.+)$", text, flags=re.M)
    if [int(n) for n, _ in heads] != list(range(1, 15)):
        errs.append(f"Se esperaban las secciones 1..14 en orden; hay {[n for n, _ in heads]}")
    for (n, t) in heads:
        if int(n) <= 14 and not t.lower().startswith(TITLES[int(n) - 1].lower()[:12]):
            errs.append(f"Título de la sección {n} inesperado: «{t}»")
    s = sections(text)
    if len(s) < 14:
        return errs
    body = re.sub(r"Palabras clave:.*", "", s[1])
    if words(body) > 250:
        errs.append(f"Resumen: {words(body)} palabras (máx. 250)")
    kw = re.search(r"Palabras clave:\s*(.+)", s[1])
    if not kw or not 3 <= len([k for k in kw.group(1).split(",") if k.strip()]) <= 5:
        errs.append("Resumen: faltan palabras clave (3 a 5, separadas por comas)")
    for sub in ("3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "5.3", "8.1", "8.2"):
        if not re.search(rf"^## {re.escape(sub)} ", text, flags=re.M):
            errs.append(f"Falta el subtítulo {sub}")
    spec = re.search(r"## 3\.2 .*?\n(.*?)(?=\n# |\n## |\Z)", text, flags=re.S)
    n_spec = len(re.findall(r"^\d+\. ", spec.group(1), flags=re.M)) if spec else 0
    if not 3 <= n_spec <= 5:
        errs.append(f"Objetivos específicos: {n_spec} (deben ser de 3 a 5)")
    if not re.search(r"^## 3\.1 .*?\n+\s*(Desarrollar|Diseñar|Implementar|Analizar)", text, flags=re.S | re.M):
        errs.append("El objetivo general debe empezar con verbo en infinitivo")
    for kwd in ("Tipo de investigación", "Técnicas de recolección", "Fases"):
        if kwd.lower() not in s[6].lower():
            errs.append(f"Sección 6: falta «{kwd}»")
    if not any(m in s[6] for m in ("Scrum", "Cascada", "Prototipado")):
        errs.append("Sección 6: debe nombrar la metodología (Scrum, Cascada o Prototipado)")
    if "NO incluye" not in s[7] or "usuarios" not in s[7].lower():
        errs.append("Sección 7: debe decir qué NO incluye y a qué usuarios se dirige")
    rf = set(re.findall(r"RF-\d{2}", s[8])); rnf = set(re.findall(r"RNF-\d{2}", s[8]))
    if len(rf) < 8 or len(rnf) < 4:
        errs.append(f"Sección 8: {len(rf)} RF y {len(rnf)} RNF (mínimo 8 y 4)")
    imgs = re.findall(r"!\[.*?\]\((.+?)\)", s[9])
    if len(imgs) < 3:
        errs.append("Sección 9: se requieren 3 diagramas (arquitectura, casos de uso, módulos)")
    if "G = (V, E)" not in s[9]:
        errs.append("Sección 9: falta el modelo matemático «G = (V, E)»")
    for img in re.findall(r"!\[.*?\]\((.+?)\)", text):
        if not (md_path.parent / img).exists():
            errs.append(f"Imagen inexistente: {img}")
    for cat in ("Lenguaje", "librerías", "desarrollo", "diseño"):
        if cat.lower() not in s[10].lower():
            errs.append(f"Sección 10: falta la categoría «{cat}»")
    for tipo in ("técnic", "académic", "usuario", "industria"):
        if tipo not in s[11].lower():
            errs.append(f"Sección 11: falta el beneficio {tipo}")
    refs = [l for l in s[13].splitlines() if re.search(r"\(\d{4}\)", l)]
    if len(refs) < 6:
        errs.append(f"Referencias: {len(refs)} con formato APA «(año)»; mínimo 6")
    for ap in "ABCD":
        if f"Apéndice {ap}" not in s[14]:
            errs.append(f"Falta el Apéndice {ap}")
    for marker in re.findall(r"\[COMPLETAR:[^\]]*\]", text):
        errs.append(f"Dato sin completar: {marker}")
    return errs


if __name__ == "__main__":
    problems = check(sys.argv[1] if len(sys.argv) > 1 else "docs/informe/informe.md")
    print("\n".join(problems) if problems else "OK: el informe cumple la rúbrica estructural")
    raise SystemExit(1 if problems else 0)
