"""Run all Step 1 tests against the bundled renderer (dist/pineapples_carousel.py).

    python build.py
    python tests/run_tests.py

Needs Playwright + Chromium, and Pillow for the pixel comparison.
Parity tests also need reference/ (not in the repo). Output goes to tests/out/.
"""
import importlib.util
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "pineapples_carousel.py"
SAMPLES = ROOT / "samples"
OUT = ROOT / "tests" / "out"
sys.path.insert(0, str(Path(__file__).resolve().parent))

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  -- {detail}" if detail else ""), flush=True)


def run(kind, sample, out_dir):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    p = subprocess.run([sys.executable, str(DIST), kind, str(SAMPLES / sample), str(out_dir)],
                       capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def load_bundle():
    spec = importlib.util.spec_from_file_location("pc_bundle", DIST)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pixel_diff(a, b):
    # Compare RGB: for RGBA images getbbox() only looks at the alpha channel.
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size:
        return None, f"size {ia.size} vs {ib.size}"
    diff = ImageChops.difference(ia, ib)
    bbox = diff.getbbox()
    if not bbox:
        return 0, ""
    r, g, b = diff.split()
    count = sum(ImageChops.lighter(ImageChops.lighter(r, g), b).histogram()[1:])
    return count, f"differing box {bbox}"


# ---------------------------------------------------------------- 1. parity
def test_parity():
    import original_method as om
    pairs = []
    for sample in ("daily-am.json", "daily-pm.json", "trade-asx.json"):
        data = json.loads((SAMPLES / sample).read_text(encoding="utf-8"))
        kind = "daily" if sample.startswith("daily") else "trade"
        old_dir, new_dir = OUT / "parity" / sample[:-5] / "old", OUT / "parity" / sample[:-5] / "new"
        for d in (old_dir, new_dir):
            if d.exists():
                shutil.rmtree(d)
        old = om.render_daily(data, old_dir) if kind == "daily" else om.render_trade(data, old_dir)
        code, out, err = run(kind, sample, new_dir)
        new = [Path(p) for p in out.splitlines()]
        if code != 0 or [p.name for p in old] != [p.name for p in new]:
            record(f"1 parity {sample}", False, f"exit {code} {err}; names {[p.name for p in old]} vs {[p.name for p in new]}")
            continue
        notes, all_same = [], True
        for a, b in zip(old, new):
            count, info = pixel_diff(a, b)
            size = Image.open(b).size
            if count != 0:
                all_same = False
                notes.append(f"{b.name}: {count} px differ {info}")
            pairs.append((sample, a, b, count, size))
        record(f"1 parity {sample} ({len(new)} PNGs, {size[0]}x{size[1]})", all_same,
               "pixel-identical" if all_same else "; ".join(notes))
    write_parity_page(pairs)


def write_parity_page(pairs):
    rows = []
    for sample, a, b, count, size in pairs:
        verdict = "identical" if count == 0 else f"{count:,} pixels differ"
        rows.append(f"""<tr><td colspan=2 class=cap>{sample} &middot; {b.name} &middot; {size[0]}&times;{size[1]} &middot; <b>{verdict}</b></td></tr>
<tr><td><img src="{a.relative_to(OUT).as_posix()}"></td><td><img src="{b.relative_to(OUT).as_posix()}"></td></tr>""")
    (OUT / "parity.html").write_text(f"""<!doctype html><meta charset=utf-8><title>Carousel parity: old vs new</title>
<style>body{{font-family:Arial,sans-serif;background:#eee;margin:16px}}table{{border-collapse:collapse;width:100%}}
td{{width:50%;padding:6px;vertical-align:top}}img{{width:100%;border:1px solid #ccc}}.cap{{padding-top:24px;font-size:15px}}
th{{text-align:left;font-size:18px}}</style>
<h1>Pineapples carousel: today's method (left) vs new renderer (right)</h1>
<table><tr><th>Old (today)</th><th>New (renderer)</th></tr>{''.join(rows)}</table>""", encoding="utf-8")


# ------------------------------------------------------ 2. real trade samples
def test_trade_samples():
    cases = {
        "trade-asx-real.json": ["cover", "opportunities-1", "results-1", "results-2", "results-3", "cta"],
        "trade-0-ideas.json": ["cover", "opportunities-1", "results-1", "cta"],
        "trade-1-idea.json": ["cover", "opportunities-1", "results-1", "cta"],
        "trade-7-ideas.json": ["cover", "opportunities-1", "opportunities-2", "opportunities-3", "results-1", "cta"],
    }
    for sample, expect in cases.items():
        code, out, err = run("trade", sample, OUT / "trade" / sample[:-5])
        names = [Path(p).name for p in out.splitlines()]
        want = [f"pineapples-{i:02d}-{n}.png" for i, n in enumerate(expect, start=1)]
        record(f"2 trade {sample}", code == 0 and names == want,
               f"exit {code}, {len(names)} slides" + (f"; got {names}; {err}" if names != want or code else ""))
    for sample in ("daily-pm-3-radar.json",):
        code, out, err = run("daily", sample, OUT / "daily" / sample[:-5])
        record(f"2b daily {sample}", code == 0, f"exit {code} {err}")


# --------------------------------------------------------------- 3. overflow
def test_overflow():
    for kind, sample, field in (("daily", "daily-overflow.json", "pineapple_take_body"),
                                ("trade", "trade-overflow.json", "hook_line")):
        code, out, err = run(kind, sample, OUT / "overflow" / sample[:-5])
        pngs = [p for p in out.splitlines() if Path(p).exists()]
        ok = code == 2 and field in err and len(pngs) >= 4
        record(f"3 overflow {sample}", ok, f"exit {code}, {len(pngs)} PNGs still written; message: {err}")


# ------------------------------------------------------------- 4. validation
def test_validation():
    code, out, err = run("daily", "daily-missing-field.json", OUT / "validation")
    record("4 validation daily-missing-field.json", code == 1 and err == "missing field: cover_headline"
           and not (OUT / "validation").exists(), f"exit {code}, message: {err}")

    # The examples in SCHEMA.md must themselves be valid, and `schema` mode must print them.
    import re
    pc = load_bundle()
    for kind in ("daily", "trade"):
        p = subprocess.run([sys.executable, str(DIST), "schema", kind], capture_output=True, text=True, encoding="utf-8")
        blocks = re.findall(r"```json\n(.*?)```", p.stdout, re.S)
        try:
            pc.validate(kind, json.loads(blocks[0]))
            other = "trade" if kind == "daily" else "daily"
            ok = p.returncode == 0 and len(blocks) == 1 and f"## {other.title()} carousel" not in p.stdout
            detail = f"`schema {kind}` prints {len(p.stdout.splitlines())} lines; its example JSON is valid"
        except Exception as e:
            ok, detail = False, repr(e)
        record(f"4b schema {kind}", ok, detail)


# --------------------------------------------------------------- 5. escaping
def test_escaping():
    from playwright.sync_api import sync_playwright
    pc = load_bundle()
    for kind, sample in (("daily", "daily-escaping.json"), ("trade", "trade-escaping.json")):
        data = json.loads((SAMPLES / sample).read_text(encoding="utf-8"))
        code, out, err = run(kind, sample, OUT / "escaping" / sample[:-5])
        pages = [pc.daily_html(data)] if kind == "daily" else [h for _, h in pc.trade_slides(data)]
        expected = {}
        if kind == "daily":
            expected = {"cover_headline": data["cover_headline"], "cover_pullquote": data["cover_pullquote"],
                        "stats[0].k": data["stats"][0]["k"], "stats[0].v": data["stats"][0]["v"],
                        "radar[0].desc": data["radar"][0]["desc"]}
        else:
            expected = {"hook_line": data["hook_line"], "ideas[0].ticker": data["ideas"][0]["ticker"],
                        "ideas[1].ticker": data["ideas"][1]["ticker"]}
        seen = {}
        with sync_playwright() as p:
            b = p.chromium.launch()
            page = b.new_page()
            for h in pages:
                page.set_content(h)
                for f in expected:
                    el = page.query_selector(f'[data-field="{f}"]')
                    if el:
                        seen[f] = el.text_content()
                seen["_injected_tags"] = seen.get("_injected_tags", 0) + page.evaluate(
                    "document.querySelectorAll('b, lead, live, close, watch').length")
            b.close()
        bad = {f: (seen.get(f), v) for f, v in expected.items() if seen.get(f) != v}
        ok = code == 0 and not bad and seen["_injected_tags"] == 0
        record(f"5 escaping {sample}", ok, "text shows exactly as written, no HTML injected" if ok
               else f"exit {code} {err}; mismatches {bad}; injected {seen['_injected_tags']}")


# ------------------------------------------------------------ 6. fonts offline
def test_fonts_offline():
    pc = load_bundle()
    data = json.loads((SAMPLES / "daily-am.json").read_text(encoding="utf-8"))
    normal = OUT / "parity" / "daily-am" / "new" / "pineapples-am-01.png"
    original = dict(pc.TEMPLATES)
    scenarios = {
        # Google Fonts unreachable (DNS fails at once, like an offline sandbox)
        "fonts-unreachable": lambda t: t.replace("https://fonts.googleapis.com/", "https://fonts.googleapis.invalid/"),
        # Google Fonts hangs (connection to a black-hole address never answers)
        "fonts-hang": lambda t: t.replace("https://fonts.googleapis.com/", "https://10.255.255.1/"),
    }
    pc.FONT_HOSTS = __import__("re").compile(r"^https://(fonts\.(googleapis|gstatic)\.com|10\.255\.255\.1)/")
    for name, patch in scenarios.items():
        pc.TEMPLATES.clear()
        pc.TEMPLATES.update({k: patch(v) for k, v in original.items()})
        start = time.time()
        try:
            paths, problems = pc.render("daily", data, OUT / "fonts" / name)
            secs = time.time() - start
            changed = pixel_diff(normal, paths[0])[0] if normal.exists() else None
            ok = len(paths) == 5 and all(Path(p).exists() for p in paths) and secs < 60 and changed != 0
            record(f"6 fonts offline ({name})", ok,
                   f"finished in {secs:.1f}s with fallback fonts; overflow flags: {len(problems)}; "
                   f"slide 1 differs from the web-font render: {changed != 0}")
        except Exception as e:
            record(f"6 fonts offline ({name})", False, repr(e))
    pc.TEMPLATES.clear()
    pc.TEMPLATES.update(original)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for test in (test_parity, test_trade_samples, test_overflow, test_validation, test_escaping,
                 test_fonts_offline):
        try:
            test()
        except Exception as e:
            record(test.__name__, False, repr(e))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)} passed, {len(failed)} failed")
    sys.exit(1 if failed else 0)
