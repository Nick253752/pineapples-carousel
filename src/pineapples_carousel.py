#!/usr/bin/env python3
"""Pineapples carousel renderer.

Turns a short JSON file of one run's content into the carousel PNGs.

    python3 pineapples_carousel.py daily  content.json  out_dir
    python3 pineapples_carousel.py trade  content.json  out_dir
    python3 pineapples_carousel.py schema daily|trade

Exit codes:
    0  success; prints the PNG paths, one per line
    1  bad input (or bad usage); prints one line naming the problem, no PNGs written
    2  PNGs written, but some text overflowed; prints which slide and field

Needs only the standard library and Python Playwright (with Chromium installed).
The source lives in src/; build.py bundles it into dist/pineapples_carousel.py.
"""
import html
import json
import os
import re
import sys
from pathlib import Path

# >>> ASSETS (build.py replaces this block with the embedded templates and schema)
def _load_assets():
    here = Path(__file__).resolve().parent
    templates = {p.stem: p.read_text(encoding="utf-8").rstrip("\n")
                 for p in sorted((here / "templates").glob("*.html"))}
    schema = (here.parent / "SCHEMA.md").read_text(encoding="utf-8")
    return templates, schema


TEMPLATES, SCHEMA_MD = _load_assets()
# <<< ASSETS

if not os.environ.get("PLAYWRIGHT_BROWSERS_PATH") and os.path.isdir("/opt/pw-browsers"):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/opt/pw-browsers"

W, H = 1080, 1350

# Trade brand tokens (same values as the original build script)
GREEN = "#1F3D2B"
GOLD_DARK = "#B9791C"
CREAM = "#FBF3E4"
TERRACOTTA = "#9c4620"
MUTED = "#6b6459"
LABEL_GRAY = "#a89b7f"

TICKERS = ["asx200", "sp500", "nasdaq", "audusd", "btc"]
RESULTS = ["Not triggered", "Still in play", "Stop reached", "Target reached", "Closed at week's end"]
CONCLUDED = {"Stop reached", "Target reached", "Closed at week's end"}

# Result pill colours: (text, background). "Closed at week's end" is new; it uses
# the brand green as a solid pill so it reads as settled and differs from the rest.
PILL_COLORS = {
    "Not triggered": (MUTED, "#efe9db"),
    "Still in play": (GREEN, "#e3ecdf"),
    "Stop reached": (TERRACOTTA, "#f3e2d6"),
    "Target reached": (GOLD_DARK, "#faecd0"),
    "Closed at week's end": (CREAM, GREEN),
}
EXIT_COLORS = {"Stop reached": TERRACOTTA, "Target reached": GOLD_DARK, "Closed at week's end": GREEN}

DEFAULT_INDEX_LABEL = "per 100 pineapples ($5k) in the index"


class InputError(Exception):
    pass


# ---------------------------------------------------------------------------
# Input schema and validation
# ---------------------------------------------------------------------------
# A spec is "str", "bool", ("enum", [...]), ("obj", {key: spec}),
# ("list", min, max, item_spec) or ("opt", spec) for an optional object key.

def _obj(fields):
    return ("obj", fields)


DAILY_SPEC = _obj({
    "edition": ("enum", ["am", "pm"]),
    "date_long": "str",
    "cover_headline": "str",
    "cover_subhead": "str",
    "cover_pullquote": "str",
    "ticker": _obj({k: _obj({"val": "str", "chg": "str", "dir": ("enum", ["up", "down", "flat"])})
                    for k in TICKERS}),
    "big_story_headline": "str",
    "big_story_intro": "str",
    "stats": ("list", 1, 4, _obj({"k": "str", "v": "str"})),
    "big_story_outro": "str",
    "pineapple_take_quote": "str",
    "pineapple_take_body": "str",
    "radar": ("list", 3, 4, _obj({"time": "str", "desc": "str"})),
    "index_figure": "str",
    "index_label": ("opt", "str"),
    "index_body": "str",
})

TRADE_SPEC = _obj({
    "session": ("enum", ["ASX", "US"]),
    "date": "str",
    "hook_line": "str",
    "ideas": ("list", 0, 30, _obj({
        "ticker": "str",
        "dir": ("enum", ["Long", "Short"]),
        "entry": "str",
        "stop": "str",
        "target": "str",
        "rr": "str",
        "conf": "str",
        "flyer": ("opt", "bool"),
    })),
    "outcomes": ("list", 0, 30, _obj({
        "ticker": "str",
        "dir": ("enum", ["Long", "Short"]),
        "result": ("enum", RESULTS),
        "entry": "str",
        "exit": ("opt", "str"),
        "rr": ("opt", "str"),
    })),
})


def _check(value, spec, path):
    name = path or "(top level)"
    if spec == "str":
        if not isinstance(value, str):
            raise InputError(f"wrong type for field {name}: expected text")
        if not value.strip():
            raise InputError(f"empty field: {name}")
    elif spec == "bool":
        if not isinstance(value, bool):
            raise InputError(f"wrong type for field {name}: expected true or false")
    elif spec[0] == "enum":
        if value not in spec[1]:
            raise InputError(f"invalid value for field {name}: must be one of " + ", ".join(spec[1]))
    elif spec[0] == "list":
        _, lo, hi, item = spec
        if not isinstance(value, list):
            raise InputError(f"wrong type for field {name}: expected a list")
        if not lo <= len(value) <= hi:
            raise InputError(f"wrong number of items in field {name}: need {lo} to {hi}, got {len(value)}")
        for i, v in enumerate(value):
            _check(v, item, f"{path}[{i}]")
    elif spec[0] == "obj":
        if not isinstance(value, dict):
            raise InputError(f"wrong type for field {name}: expected an object")
        prefix = f"{path}." if path else ""
        for key, sub in spec[1].items():
            optional = isinstance(sub, tuple) and sub[0] == "opt"
            if key not in value:
                if optional:
                    continue
                raise InputError(f"missing field: {prefix}{key}")
            _check(value[key], sub[1] if optional else sub, prefix + key)
        for key in value:
            if key not in spec[1]:
                raise InputError(f"unknown field: {prefix}{key}")
    else:
        raise AssertionError(spec)


def validate(kind, data):
    _check(data, DAILY_SPEC if kind == "daily" else TRADE_SPEC, "")
    if kind == "trade":
        for i, o in enumerate(data["outcomes"]):
            if o["result"] in CONCLUDED:
                for key in ("exit", "rr"):
                    if key not in o:
                        raise InputError(f"missing field: outcomes[{i}].{key} (needed for {o['result']})")


# ---------------------------------------------------------------------------
# HTML building
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r"\{\{(\w+)\}\}")


def fill(template, **values):
    """Replace {{name}} tokens. Values must already be safe HTML."""
    return _TOKEN.sub(lambda m: str(values[m.group(1)]), TEMPLATES[template])


def esc(text):
    return html.escape(text, quote=True)


def daily_html(d):
    t = d["ticker"]
    values = {
        "date_long": esc(d["date_long"]),
        "edition_label": "MORNING EDITION" if d["edition"] == "am" else "EVENING EDITION",
        "stat_rows": "\n".join(fill("daily_stat", i=i, k=esc(s["k"]), v=esc(s["v"]))
                               for i, s in enumerate(d["stats"])),
        "radar_rows": "\n".join(fill("daily_radar", i=i, time=esc(r["time"]), desc=esc(r["desc"]))
                                for i, r in enumerate(d["radar"])),
        "index_label": esc(d.get("index_label", DEFAULT_INDEX_LABEL)),
    }
    for key in ("cover_headline", "cover_subhead", "cover_pullquote", "big_story_headline",
                "big_story_intro", "big_story_outro", "pineapple_take_quote",
                "pineapple_take_body", "index_figure", "index_body"):
        values[key] = esc(d[key])
    for k in TICKERS:
        values[f"{k}_val"] = esc(t[k]["val"])
        values[f"{k}_chg"] = esc(t[k]["chg"])
        values[f"{k}_class"] = t[k]["dir"]
    return fill("daily", **values)


def _chunk(items, size=3):
    return [items[i:i + size] for i in range(0, len(items), size)] or [[]]


def _empty_note(text):
    return (f'<div style="font-family:\'Karla\',sans-serif;font-size:27px;color:{MUTED};'
            f'text-align:center;">{text}</div>')


def _idea_card(i, idea):
    return fill("trade_idea_card", i=i,
                ticker=esc(idea["ticker"]), dir=esc(idea["dir"]),
                dir_color=GREEN if idea["dir"] == "Long" else TERRACOTTA,
                entry=esc(idea["entry"]), stop=esc(idea["stop"]), target=esc(idea["target"]),
                rr=esc(idea["rr"]), conf=esc(idea["conf"]),
                flyer_badge=TEMPLATES["trade_flyer_badge"] if idea.get("flyer") else "")


def _outcome_row(i, o):
    fg, bg = PILL_COLORS[o["result"]]
    detail = (f'<span style="color:{LABEL_GRAY};">Entry</span> '
              f'<span style="font-weight:700;color:{GREEN};">{esc(o["entry"])}</span>')
    if o["result"] in CONCLUDED:
        sep = "&nbsp;&nbsp;&middot;&nbsp;&nbsp;"
        detail += (f'{sep}<span style="color:{LABEL_GRAY};">Exit</span> '
                   f'<span style="font-weight:700;color:{EXIT_COLORS[o["result"]]};">{esc(o["exit"])}</span>'
                   f'{sep}<span style="color:{LABEL_GRAY};">RR</span> '
                   f'<span style="font-weight:700;color:{GREEN};">{esc(o["rr"])}</span>')
    return fill("trade_outcome_row", i=i, ticker=esc(o["ticker"]), dir=esc(o["dir"]),
                pill_fg=fg, pill_bg=bg, result=esc(o["result"]), detail=detail)


def trade_slides(d):
    """Return [(name, html)] in deck order."""
    asx = d["session"] == "ASX"
    edition = "Morning Edition" if asx else "Evening Edition"
    session_label = "AUS session" if asx else "US session"

    def page(body, bg):
        return fill("trade_page", bg=bg, body=body)

    slides = [("cover", page(fill("trade_cover", date=esc(d["date"]), edition=edition,
                                  hook_line=esc(d["hook_line"])), GREEN))]

    chunks = _chunk(list(enumerate(d["ideas"])))
    for n, chunk in enumerate(chunks, start=1):
        rows = "".join(_idea_card(i, idea) for i, idea in chunk) or _empty_note(
            "No new opportunities this session.")
        body = fill("trade_opportunities", brand_row=TEMPLATES["trade_brand_row"],
                    heading="Today's Opportunities" if n == 1 else "Today's Opportunities (cont.)",
                    page_note=f"{n} of {len(chunks)}" if len(chunks) > 1 else "", rows=rows)
        slides.append((f"opportunities-{n}", page(body, CREAM)))

    chunks = _chunk(list(enumerate(d["outcomes"])))
    for n, chunk in enumerate(chunks, start=1):
        rows = "".join(_outcome_row(i, o) for i, o in chunk) or _empty_note(
            "No trade outcomes to report this session.")
        body = fill("trade_outcomes", brand_row=TEMPLATES["trade_brand_row"],
                    heading="Trade Outcomes" if n == 1 else "Trade Outcomes (cont.)",
                    page_note=f"{n} of {len(chunks)}" if len(chunks) > 1 else "",
                    session_label=session_label, rows=rows)
        slides.append((f"results-{n}", page(body, CREAM)))

    slides.append(("cta", page(fill("trade_cta"), CREAM)))
    return slides


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

FONT_HOSTS = re.compile(r"^https://fonts\.(googleapis|gstatic)\.com/")
FONT_FETCH_TIMEOUT_MS = 10000
FONTS_READY_TIMEOUT_MS = 8000
LOAD_TIMEOUT_MS = 30000

WAIT_FONTS_JS = """(ms) => Promise.race([
  document.fonts.ready.then(() => true),
  new Promise(r => setTimeout(() => r(false), ms)),
])"""

# Finds text that doesn't fit. Returns [{fields: [...], how: "..."}] for one slide.
OVERFLOW_JS = r"""(sel) => {
  const TOL = 1;
  const root = document.querySelector(sel);
  const rr = root.getBoundingClientRect();
  const out = [];
  const fieldsIn = el => Array.from(el.querySelectorAll('[data-field]'));
  const name = f => f.dataset.field;
  // 1. The slide (or a fixed-height box inside it) holds more than fits.
  for (const b of [root, ...root.querySelectorAll('[data-box]')]) {
    const over = b.scrollHeight - b.clientHeight;
    if (over > TOL) {
      const fs = fieldsIn(b).sort((a, c) => c.getBoundingClientRect().height - a.getBoundingClientRect().height);
      out.push({fields: fs.slice(0, 3).map(name), how: `slide content is ${Math.ceil(over)}px too tall`});
    }
  }
  // 2. A box is wider than its space (e.g. one very long word or number).
  for (const el of root.querySelectorAll('*')) {
    if (el instanceof SVGElement) continue;
    const d = getComputedStyle(el).display;
    if (d === 'inline' || d === 'contents' || d === 'none') continue;
    const over = el.scrollWidth - el.clientWidth;
    if (over > TOL) {
      const own = el.closest('[data-field]');
      const fs = own ? [own] : fieldsIn(el);
      out.push({fields: fs.map(name), how: `text is ${Math.ceil(over)}px too wide`});
    }
  }
  // 3. A field sits partly outside the slide.
  for (const f of fieldsIn(root)) {
    const r = f.getBoundingClientRect();
    if (r.right > rr.right + TOL || r.bottom > rr.bottom + TOL || r.left < rr.left - TOL || r.top < rr.top - TOL)
      out.push({fields: [name(f)], how: 'runs off the edge of the slide'});
  }
  // 4. A field comes within GAP px of fixed text pinned to the slide (e.g. "Swipe").
  const GAP = 40;
  for (const a of root.querySelectorAll('[data-avoid]')) {
    const ar = a.getBoundingClientRect();
    for (const f of fieldsIn(root)) {
      const r = f.getBoundingClientRect();
      if (r.left < ar.right + GAP && r.right > ar.left - GAP && r.top < ar.bottom + GAP && r.bottom > ar.top - GAP)
        out.push({fields: [name(f)], how: `runs into "${a.textContent.trim()}"`});
    }
  }
  return out;
}"""


def _guard_fonts(page):
    """Fetch Google Fonts with a hard timeout so a slow or blocked font server
    can never hang the render; on failure the Georgia/Arial fallbacks are used."""
    def handle(route):
        try:
            route.fulfill(response=route.fetch(timeout=FONT_FETCH_TIMEOUT_MS))
        except Exception:
            try:
                route.abort()
            except Exception:
                pass
    page.route(FONT_HOSTS, handle)


def _load(page, html_text):
    from playwright.sync_api import TimeoutError as PWTimeout
    try:
        page.set_content(html_text, wait_until="networkidle", timeout=LOAD_TIMEOUT_MS)
    except PWTimeout:
        pass
    try:
        page.evaluate(WAIT_FONTS_JS, FONTS_READY_TIMEOUT_MS)
    except Exception:
        pass


def _overflow_lines(page, selector, slide_no, filename):
    lines, seen = [], set()
    for item in page.evaluate(OVERFLOW_JS, selector):
        fields = ", ".join(dict.fromkeys(item["fields"])) or "fixed text"
        line = f"overflow: slide {slide_no} ({filename}) field {fields}: {item['how']}"
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return lines


def _clear_old(out_dir, pattern):
    for old in out_dir.glob(pattern):
        old.unlink()


def render(kind, data, out_dir):
    """Render PNGs into out_dir. Returns (paths, overflow_lines)."""
    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    paths, problems = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            if kind == "daily":
                prefix = f"pineapples-{data['edition']}"
                _clear_old(out_dir, f"{prefix}-0[1-5].png")
                page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
                _guard_fonts(page)
                _load(page, daily_html(data))
                for n in range(1, 6):
                    f = out_dir / f"{prefix}-{n:02d}.png"
                    problems += _overflow_lines(page, f"#s{n}", n, f.name)
                    page.locator(f"#s{n}").screenshot(path=str(f))
                    paths.append(str(f))
            else:
                _clear_old(out_dir, "pineapples-[0-9][0-9]-*.png")
                page = browser.new_page(viewport={"width": W, "height": H})
                _guard_fonts(page)
                for n, (name, html_text) in enumerate(trade_slides(data), start=1):
                    f = out_dir / f"pineapples-{n:02d}-{name}.png"
                    _load(page, html_text)
                    problems += _overflow_lines(page, ".slide", n, f.name)
                    page.screenshot(path=str(f))
                    paths.append(str(f))
        finally:
            browser.close()
    return paths, problems


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

USAGE = "usage: pineapples_carousel.py daily|trade content.json out_dir  |  schema daily|trade"


def schema_text(kind):
    """The shared part of SCHEMA.md plus the section for one carousel type."""
    sections = re.split(r"(?m)^(?=## )", SCHEMA_MD)
    keep = [s for s in sections
            if not s.startswith("## ") or s.startswith("## Both")
            or s.lower().startswith(f"## {kind}")]
    return "".join(keep).strip() + "\n"


def main(argv):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if len(argv) == 3 and argv[1] == "schema" and argv[2] in ("daily", "trade"):
        sys.stdout.write(schema_text(argv[2]))
        return 0
    if len(argv) != 4 or argv[1] not in ("daily", "trade"):
        print(USAGE, file=sys.stderr)
        return 1
    kind, src, out_dir = argv[1], Path(argv[2]), Path(argv[3])
    try:
        try:
            data = json.loads(src.read_text(encoding="utf-8-sig"))
        except OSError as e:
            raise InputError(f"cannot read {src}: {e.strerror}")
        except json.JSONDecodeError as e:
            raise InputError(f"invalid JSON in {src}: {e.msg} at line {e.lineno} column {e.colno}")
        validate(kind, data)
    except InputError as e:
        print(e, file=sys.stderr)
        return 1

    paths, problems = render(kind, data, out_dir)
    print("\n".join(paths))
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
