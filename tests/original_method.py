"""Today's render method, reproduced from the reference docs, for the parity test.

Daily: the carousel HTML template from reference/daily-automation.md (STEP 5),
{{tokens}} filled by plain text replacement, rendered per STEP 6.
Trade: the build script from reference/trade-carousel-template.md with the
overrides from reference/trade-suggestions-automation.md applied (emoji logo,
no Numbers slide), run exactly as the tasks run it today.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"


def daily_template(edition):
    text = (REF / "daily-automation.md").read_text(encoding="utf-8")
    am, pm = re.findall(r"--- CAROUSEL HTML TEMPLATE ---\n(.*?)--- END TEMPLATE ---", text, re.S)
    return am if edition == "am" else pm


def daily_tokens(d):
    t = {
        "date_long": d["date_long"],
        "edition_label": "MORNING EDITION" if d["edition"] == "am" else "EVENING EDITION",
        "index_label": d.get("index_label", "per 100 pineapples ($5k) in the index"),
    }
    for k in ("cover_headline", "cover_subhead", "cover_pullquote", "big_story_headline",
              "big_story_intro", "big_story_outro", "pineapple_take_quote",
              "pineapple_take_body", "index_figure", "index_body"):
        t[k] = d[k]
    for k, v in d["ticker"].items():
        t[f"{k}_val"], t[f"{k}_chg"], t[f"{k}_class"] = v["val"], v["chg"], v["dir"]
    for i, s in enumerate(d["stats"], start=1):
        t[f"stat{i}_k"], t[f"stat{i}_v"] = s["k"], s["v"]
    for i, r in enumerate(d["radar"], start=1):
        t[f"radar{i}_time"], t[f"radar{i}_desc"] = r["time"], r["desc"]
    return t


def render_daily(d, out_dir):
    from playwright.sync_api import sync_playwright
    out_dir.mkdir(parents=True, exist_ok=True)
    html = daily_template(d["edition"])
    for k, v in daily_tokens(d).items():
        html = html.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{\w+\}\}", html)
    assert not left, f"unfilled tokens: {left}"
    src = out_dir / "filled.html"
    src.write_text(html, encoding="utf-8")
    paths = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=2)
        page.goto(src.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        for n in range(1, 6):
            f = out_dir / f"pineapples-{d['edition']}-{n:02d}.png"
            page.locator(f"#s{n}").screenshot(path=str(f))
            paths.append(f)
        browser.close()
    return paths


def trade_script():
    text = (REF / "trade-carousel-template.md").read_text(encoding="utf-8")
    code = text[text.index("#!/usr/bin/env python3"):text.index("File naming & delivery")]
    code = code[:code.index('if __name__ == "__main__":')]
    # Override: emoji logo (trade-suggestions-automation.md, "Logo mark")
    code, n = re.subn(r"def logo\(uid, size=120, on_dark=True\):\n(?:    .*\n)+",
                      "def logo(uid, size=120, on_dark=True):\n"
                      "    return f'<div style=\"font-size:{int(size*0.8)}px;line-height:1;\">🍍</div>'\n",
                      code)
    assert n == 1
    # Override: Numbers slide removed
    code, n = re.subn(r"    slides\.append\(\(\"numbers\".*?\)\)\)\n", "", code, flags=re.S)
    assert n == 1
    return code


def render_trade(d, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    argv = sys.argv
    sys.argv = ["build_carousel.py", str(out_dir)]
    try:
        ns = {"__name__": "build_carousel"}
        exec(compile(trade_script(), "build_carousel.py", "exec"), ns)
    finally:
        sys.argv = argv
    asx = d["session"] == "ASX"
    ideas = [dict(i) for i in d["ideas"]]
    recap = [dict(o) for o in d["outcomes"]]
    paths = ns["render_all"](
        edition="Morning Edition" if asx else "Evening Edition",
        date_str=d["date"], session_label="AUS session" if asx else "US session",
        ideas=ideas, recap_results=recap, hook_line=d["hook_line"],
        current_balance=10000, start_balance=10000, week_delta=0, month_delta=0,
        quarter_delta=0, year_delta=0, data_as_of="", since_label="", numbers_available=False)
    return [Path(p) for p in paths]
