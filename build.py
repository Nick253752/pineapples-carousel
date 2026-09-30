#!/usr/bin/env python3
"""Bundle src/ into one file: dist/pineapples_carousel.py.

    python build.py

The templates (src/templates/*.html) and SCHEMA.md are embedded as strings in
place of the ASSETS block in src/pineapples_carousel.py.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "pineapples_carousel.py"
OUT = ROOT / "dist" / "pineapples_carousel.py"
BLOCK = re.compile(r"# >>> ASSETS.*?# <<< ASSETS\n", re.S)


def main():
    source = SRC.read_text(encoding="utf-8")
    if len(BLOCK.findall(source)) != 1:
        raise SystemExit("build: ASSETS block not found exactly once in src/pineapples_carousel.py")

    templates = {p.stem: p.read_text(encoding="utf-8").rstrip("\n")
                 for p in sorted((ROOT / "src" / "templates").glob("*.html"))}
    schema = (ROOT / "SCHEMA.md").read_text(encoding="utf-8")

    lines = ["# Embedded by build.py from src/templates/*.html and SCHEMA.md.", "TEMPLATES = {"]
    lines += [f"    {name!r}: {text!r}," for name, text in templates.items()]
    lines += ["}", f"SCHEMA_MD = {schema!r}", ""]
    bundled = BLOCK.sub(lambda _: "\n".join(lines), source)

    header = ("# GENERATED FILE: do not edit. Edit src/ and SCHEMA.md, then run: python build.py\n")
    bundled = bundled.replace('"""Pineapples carousel renderer.', header + '"""Pineapples carousel renderer.', 1)

    compile(bundled, str(OUT), "exec")

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(bundled, encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(bundled.encode('utf-8')):,} bytes, {len(templates)} templates)")


if __name__ == "__main__":
    main()
