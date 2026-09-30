"""Measure roughly how many characters each text field holds before it overflows.

Each field is grown with ordinary prose (other fields keep their sample values)
until the renderer's overflow check fires. Used to set the "Rough max" column
in SCHEMA.md. Uses fallback-free layout, i.e. whatever fonts load.
"""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("pc", ROOT / "dist" / "pineapples_carousel.py")
pc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc)

PROSE = ("The market opened softer as yields climbed and the dollar firmed while miners and banks "
         "traded mixed ahead of the inflation print and a busy week of data across the region ") * 10
NUMBERY = "1234567890" * 10

DAILY = json.loads((ROOT / "samples" / "daily-am.json").read_text(encoding="utf-8"))
TRADE = json.loads((ROOT / "samples" / "trade-asx.json").read_text(encoding="utf-8"))

daily_fields = {
    ("cover_headline",): PROSE, ("cover_subhead",): PROSE, ("cover_pullquote",): PROSE,
    ("date_long",): PROSE,
    ("ticker", "asx200", "val"): NUMBERY, ("ticker", "asx200", "chg"): PROSE,
    ("big_story_headline",): PROSE, ("big_story_intro",): PROSE, ("big_story_outro",): PROSE,
    ("stats", 0, "k"): PROSE, ("stats", 0, "v"): NUMBERY,
    ("pineapple_take_quote",): PROSE, ("pineapple_take_body",): PROSE,
    ("radar", 0, "time"): PROSE, ("radar", 0, "desc"): PROSE,
    ("index_figure",): NUMBERY, ("index_label",): PROSE, ("index_body",): PROSE,
}
trade_fields = {
    ("hook_line",): PROSE, ("date",): PROSE,
    ("ideas", 0, "ticker"): PROSE.replace(" ", ""), ("ideas", 0, "entry"): NUMBERY,
    ("outcomes", 0, "ticker"): PROSE.replace(" ", ""), ("outcomes", 0, "entry"): NUMBERY,
}


def setp(d, path, v):
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = v


def overflows(page, kind, data):
    if kind == "daily":
        page.set_content(pc.daily_html(data), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        return any(page.evaluate(pc.OVERFLOW_JS, f"#s{n}") for n in range(1, 6))
    for _, h in pc.trade_slides(data):
        page.set_content(h, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        if page.evaluate(pc.OVERFLOW_JS, ".slide"):
            return True
    return False


def fit(page, kind, base, path, text):
    lo, hi = 1, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        d = copy.deepcopy(base)
        setp(d, path, text[:mid].strip() or "x")
        if overflows(page, kind, d):
            hi = mid - 1
        else:
            lo = mid
    return lo


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width": 1080, "height": 1350})
        for kind, base, fields in (("daily", DAILY, daily_fields), ("trade", TRADE, trade_fields)):
            for path, text in fields.items():
                cur = base
                for k in path:
                    cur = cur[k] if not (isinstance(k, str) and k not in cur) else ""
                n = fit(page, kind, base, path, text)
                print(f"{kind:5} {'.'.join(map(str, path)):28} sample {len(cur) if isinstance(cur, str) else '-':>4}  fits up to ~{n}")
        b.close()
