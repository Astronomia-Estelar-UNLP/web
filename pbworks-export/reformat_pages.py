#!/usr/bin/env python3
"""
reformat_pages.py
Reformatea todas las páginas exportadas de PBworks:
  - Corrige rutas rotas de _files (14 páginas con nombres Chrome)
  - Extrae el contenido de #wikipage-inner
  - Aplica el template académico de la cátedra
  - Reescribe links internos de PBworks a archivos locales
"""

import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

PAGES_DIR = Path("pbworks-export/pages")

# Regex para rutas viejas de Chrome (nombres con espacios y corchetes)
OLD_FILES_RE = re.compile(
    r"\./astronomiaestelarlp \[licensed for non-commercial use only\] _ [^/\"']+_files/",
    re.I,
)

# Regex para links PBworks internos (absolutos y relativos)
PBWORKS_ABS_RE = re.compile(
    r'https?://astronomiaestelarlp\.pbworks\.com/w/page/(\d+)(?:/[^"\'#\s]*)?',
    re.I,
)
PBWORKS_REL_RE = re.compile(
    r'/w/page/(\d+)(?:/[^"\'#\s]*)?',
    re.I,
)

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — Astronomía Estelar UNLP</title>
  <link rel="stylesheet" href="../../assets/styles.css">
  <link rel="stylesheet" href="page-content.css">
</head>
<body>
  <header class="site-header">
    <div class="container nav-shell">
      <a class="brand" href="../../index.html">
        <span class="brand-kicker">FCAGLP · UNLP</span>
        <strong>Astronomía Estelar</strong>
      </a>
      <nav class="site-nav" aria-label="Principal">
        <a href="../../programa.html">Programa</a>
        <a href="../../trabajos-practicos.html">Trabajos prácticos</a>
        <a href="../../material-complementario.html">Material complementario</a>
      </nav>
    </div>
  </header>

  <main>
    <div class="page-article">
      <div class="container">
        <nav class="breadcrumb" aria-label="Navegación">
          <a href="../../programa.html">Programa</a>
          <span aria-hidden="true">›</span>
          <span>{title_escaped}</span>
        </nav>
        <h1 class="article-title">{title_escaped}</h1>
        <div class="article-content">
{content}
        </div>
      </div>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container footer-row">
      <p class="footer-copy">Cátedra de Astronomía Estelar · FCAGLP · UNLP</p>
    </div>
  </footer>
</body>
</html>
"""


def load_id_to_filename() -> dict:
    """Devuelve {id_str: html_filename} para todas las páginas locales."""
    id_map = {}
    for f in PAGES_DIR.glob("*.html"):
        parts = f.name.split("__", 1)
        if parts[0].isdigit():
            id_map[parts[0]] = f.name
    return id_map


def fix_files_refs(html: str, stem: str) -> str:
    """Reemplaza rutas Chrome-style de _files por la ruta correcta."""
    correct = f"./{stem}_files/"
    return OLD_FILES_RE.sub(correct, html)


def extract_title(soup: BeautifulSoup) -> str:
    """Extrae el título de la página PBworks."""
    tag = soup.find("h1", class_="pagetitle")
    if tag:
        return tag.get_text(strip=True)
    title_tag = soup.find("title")
    if title_tag:
        t = title_tag.get_text()
        # Quitar prefijo "workspace / "
        t = re.sub(r"^[^/]+/\s*", "", t).strip()
        return t or "Sin título"
    return "Sin título"


def extract_content_tag(soup: BeautifulSoup):
    """Devuelve el tag con el contenido principal."""
    return soup.find(id="wikipage-inner") or soup.find(id="wikicontent")


def strip_pbworks_cruft(tag):
    """Elimina elementos no deseados de PBworks dentro del contenido."""
    for sel in [
        ".page-history",
        "#lockinfo",
        "#new-revision-available",
        "#pb-page-star",
        "script",
        "noscript",
    ]:
        for el in tag.select(sel):
            el.decompose()
    # Eliminar tracking pixels
    for img in tag.find_all("img"):
        src = img.get("src", "")
        if "quantserve" in src or "pixel" in src or "tracker" in src.lower():
            img.decompose()


def rewrite_pbworks_links(tag, id_map: dict):
    """Reescribe links de PBworks a archivos locales donde existan."""
    for a in tag.find_all("a", href=True):
        href = a["href"]
        for pattern in (PBWORKS_ABS_RE, PBWORKS_REL_RE):
            m = pattern.match(href)
            if m:
                pid = m.group(1)
                if pid in id_map:
                    a["href"] = id_map[pid]
                break


def process_page(fp: Path, id_map: dict) -> str:
    """Procesa una página. Retorna 'ok', 'skip' o 'error'."""
    pid = fp.name.split("__")[0]
    if not pid.isdigit():
        return "skip"

    try:
        html = fp.read_text(encoding="utf-8", errors="ignore")

        # 1. Corregir rutas _files rotas
        html = fix_files_refs(html, fp.stem)

        # 2. Parsear
        soup = BeautifulSoup(html, "html.parser")

        # 3. Extraer título y contenido
        title = extract_title(soup)
        content_tag = extract_content_tag(soup)
        if content_tag is None:
            print(f"  SKIP {fp.name}: no content div", file=sys.stderr)
            return "skip"

        # 4. Limpiar cruft de PBworks
        strip_pbworks_cruft(content_tag)

        # 5. Reescribir links internos
        rewrite_pbworks_links(content_tag, id_map)

        content_html = content_tag.decode_contents()

        # 6. Aplicar template
        title_escaped = (
            title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        new_html = HTML_TEMPLATE.format(
            title=title_escaped,
            title_escaped=title_escaped,
            content=content_html,
        )

        fp.write_text(new_html, encoding="utf-8")
        return "ok"

    except Exception as e:
        print(f"  ERROR {fp.name}: {e}", file=sys.stderr)
        return "error"


def main():
    id_map = load_id_to_filename()
    html_files = sorted(PAGES_DIR.glob("*.html"))

    counts = {"ok": 0, "skip": 0, "error": 0}
    for fp in html_files:
        result = process_page(fp, id_map)
        counts[result] += 1
        if result == "ok":
            print(f"  ✓ {fp.name}")

    print(f"\nResultado: {counts['ok']} procesadas, {counts['skip']} saltadas, {counts['error']} errores")


if __name__ == "__main__":
    main()
