#!/usr/bin/env python3
# GENERATED FILE: do not edit. Edit src/ and SCHEMA.md, then run: python build.py
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

# Embedded by build.py from src/templates/*.html and SCHEMA.md.
TEMPLATES = {
    'daily': '<!DOCTYPE html>\n<html>\n<head>\n<meta charset="UTF-8">\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@400;700&family=Karla:wght@400;700&display=swap" rel="stylesheet">\n<style>\n:root{\n--green:#1f3d2b;\n--gold:#e8a93b;\n--cream:#FBF3E4;\n--rust:#C1592B;\n--ink:#2a2a26;\n--up:#3f7d4f;\n--down:#a8433a;\n--line:rgba(31,61,43,0.14);\n}\n*{box-sizing:border-box; margin:0; padding:0;}\nbody{ font-family: Karla, Arial, Helvetica, sans-serif; }\n.slide{ width:1080px; height:1350px; position:relative; overflow:hidden; }\n.eyebrow{ font-size:29px; letter-spacing:2.5px; text-transform:uppercase; font-weight:700; }\n.serif{ font-family: Bitter, Georgia, \'Times New Roman\', serif; }\n.footer-mark{ margin-top:auto; display:flex; align-items:center; gap:14px; padding-top:24px; }\n.footer-mark .logo-emoji{ font-size:30px; line-height:1; }\n.footer-mark .wm{ font-family:Bitter,Georgia,serif; font-weight:700; font-size:26px; letter-spacing:1px; }\n.footer-mark .pagenum{ margin-left:auto; font-size:23px; font-weight:700; }\n#s1{ background: var(--green); color:var(--cream); padding:80px 76px 64px; display:flex; flex-direction:column; }\n#s1 .brandrow{ display:flex; align-items:center; gap:20px; }\n#s1 .brandrow .logo-emoji{ font-size:80px; line-height:1; }\n#s1 .wordmark{ font-size:48px; color:var(--gold); font-weight:700; letter-spacing:1px; font-family:Bitter,Georgia,serif;}\n#s1 .tagline{ margin-top:8px; font-size:27px; color:var(--cream); opacity:0.78; letter-spacing:1px;}\n#s1 .datebar{ margin-top:60px; font-size:29px; color:var(--gold); font-weight:700; }\n#s1 .headline{ margin-top:24px; font-size:76px; line-height:1.12; font-weight:700; }\n#s1 .subhead{ margin-top:32px; font-size:32px; line-height:1.5; color:var(--cream); opacity:0.9; max-width:920px;}\n#s1 .spacer{ flex:1; }\n#s1 .quote-block{ margin-top:56px; padding:36px 40px; background:rgba(251,243,228,0.07); border:1px solid rgba(251,243,228,0.2); border-radius:20px; font-family:Bitter,Georgia,serif; font-size:33px; line-height:1.5; font-style:italic; color:var(--cream); max-width:900px; }\n#s1 .ticker{ display:flex; flex-wrap:wrap; gap:0; border-top:1px solid rgba(251,243,228,0.25); border-bottom:1px solid rgba(251,243,228,0.25); padding:30px 0; }\n#s1 .tick{ width:33.33%; padding:12px 18px 12px 0; }\n#s1 .tick .name{ font-size:22px; opacity:0.68; letter-spacing:0.5px; text-transform:uppercase;}\n#s1 .tick .val{ font-size:34px; font-weight:700; margin-top:5px; }\n#s1 .tick .chg{ font-size:22px; font-weight:700; margin-top:3px; }\n#s1 .up{ color:#8fd39f; } #s1 .down{ color:#e79b91; } #s1 .flat{ color:#d8cfa9; }\n#s1 .swipe{ margin-top:34px; font-size:27px; color:var(--gold); font-weight:700; }\n.content{ background:var(--cream); color:var(--ink); padding:76px; display:flex; flex-direction:column; }\n.content .eyebrow{ color:var(--green); }\n.content .bar{ width:70px; height:9px; background:var(--gold); margin-top:18px; border-radius:5px;}\n.content .headline{ margin-top:36px; font-size:58px; line-height:1.2; font-weight:700; color:var(--green); }\n.content .body{ margin-top:36px; font-size:31px; line-height:1.56; color:#3a372f; }\n.content .stat{ display:flex; justify-content:space-between; align-items:baseline; padding:20px 0; border-bottom:1px solid var(--line); font-size:29px; }\n.content .stat .k{ color:#5a5648; }\n.content .stat .v{ font-weight:700; }\n.content .footer-mark .wm{ color:var(--green); }\n.content .footer-mark .pagenum{ color:#8a8672; }\n.radar-item{ padding:26px 0; border-bottom:1px solid var(--line); }\n.radar-item:last-child{ border-bottom:none; }\n.radar-item .time{ font-size:24px; font-weight:700; color:#b9832a; text-transform:uppercase; letter-spacing:0.5px;}\n.radar-item .desc{ font-size:30px; margin-top:8px; line-height:1.42; color:#3a372f;}\n#s3{ background:var(--green); color:var(--cream); padding:76px; display:flex; flex-direction:column; }\n#s3 .eyebrow{ color:var(--gold); }\n#s3 .bar{ width:70px; height:9px; background:var(--gold); margin-top:18px; border-radius:5px;}\n#s3 .quote{ margin-top:44px; font-family:Bitter,Georgia,serif; font-size:47px; line-height:1.4; font-weight:700; }\n#s3 .body2{ margin-top:38px; font-size:31px; line-height:1.58; color:var(--cream); opacity:0.94; }\n#s3 .disclaimer{ margin-top:26px; font-size:24px; opacity:0.68; }\n#s3 .footer-mark .wm{ color:var(--gold); }\n#s3 .footer-mark .pagenum{ color:rgba(251,243,228,0.6); }\n#s5{ background:var(--green); color:var(--cream); padding:80px 76px 64px; display:flex; flex-direction:column; }\n#s5 .eyebrow{ color:var(--gold); }\n#s5 .idxcard{ margin-top:44px; background:rgba(251,243,228,0.08); border:1px solid rgba(251,243,228,0.22); border-radius:24px; padding:56px 48px; text-align:center; }\n#s5 .idxcard .figure{ font-family:Bitter,Georgia,serif; font-size:120px; font-weight:700; color:var(--gold); line-height:1; }\n#s5 .idxcard .figure-label{ margin-top:14px; font-size:28px; font-weight:700; letter-spacing:0.5px; }\n#s5 .idxcard .idx-sub{ margin-top:24px; font-size:27px; line-height:1.5; color:var(--cream); opacity:0.85; }\n#s5 .spacer{ flex:1; }\n#s5 .cta{ font-size:40px; font-weight:700; color:var(--cream); line-height:1.32; }\n#s5 .handles{ margin-top:20px; font-size:28px; color:var(--gold); font-weight:700; }\n#s5 .risk{ margin-top:36px; font-size:23px; line-height:1.55; color:var(--cream); opacity:0.75; border-top:1px solid rgba(251,243,228,0.25); padding-top:28px; }\n</style>\n</head>\n<body>\n\n<div class="slide" id="s1">\n<div class="brandrow">\n<div class="logo-emoji">🍍</div>\n<div><div class="wordmark">PINEAPPLES</div></div>\n</div>\n<div class="tagline">DAILY MARKET BRIEF · WEALTH, WELCOMED.</div>\n<div class="datebar" data-field="date_long">{{date_long}} · {{edition_label}}</div>\n<div class="headline" data-field="cover_headline">{{cover_headline}}</div>\n<div class="subhead" data-field="cover_subhead">{{cover_subhead}}</div>\n<div class="quote-block" data-field="cover_pullquote">{{cover_pullquote}}</div>\n<div class="spacer"></div>\n<div class="ticker">\n<div class="tick"><div class="name">ASX 200</div><div class="val" data-field="ticker.asx200.val">{{asx200_val}}</div><div class="chg {{asx200_class}}" data-field="ticker.asx200.chg">{{asx200_chg}}</div></div>\n<div class="tick"><div class="name">S&amp;P 500</div><div class="val" data-field="ticker.sp500.val">{{sp500_val}}</div><div class="chg {{sp500_class}}" data-field="ticker.sp500.chg">{{sp500_chg}}</div></div>\n<div class="tick"><div class="name">Nasdaq</div><div class="val" data-field="ticker.nasdaq.val">{{nasdaq_val}}</div><div class="chg {{nasdaq_class}}" data-field="ticker.nasdaq.chg">{{nasdaq_chg}}</div></div>\n<div class="tick"><div class="name">AUD/USD</div><div class="val" data-field="ticker.audusd.val">{{audusd_val}}</div><div class="chg {{audusd_class}}" data-field="ticker.audusd.chg">{{audusd_chg}}</div></div>\n<div class="tick"><div class="name">Bitcoin</div><div class="val" data-field="ticker.btc.val">{{btc_val}}</div><div class="chg {{btc_class}}" data-field="ticker.btc.chg">{{btc_chg}}</div></div>\n<div class="tick"></div>\n</div>\n<div class="swipe">Swipe for the full brief →</div>\n</div>\n\n<div class="slide content" id="s2">\n<div class="eyebrow">01 · The Big Story</div>\n<div class="bar"></div>\n<div class="headline" data-field="big_story_headline">{{big_story_headline}}</div>\n<div class="body" data-field="big_story_intro">{{big_story_intro}}</div>\n<div style="margin-top:32px;">\n{{stat_rows}}\n</div>\n<div class="body" style="margin-top:30px;" data-field="big_story_outro">{{big_story_outro}}</div>\n<div class="footer-mark"><div class="logo-emoji" style="font-size:28px;">🍍</div><div class="wm">PINEAPPLES</div><div class="pagenum">1 / 3 HEADLINES</div></div>\n</div>\n\n<div class="slide" id="s3">\n<div class="eyebrow">02 · The Pineapple Take</div>\n<div class="bar"></div>\n<div class="quote" data-field="pineapple_take_quote">{{pineapple_take_quote}}</div>\n<div class="body2" data-field="pineapple_take_body">{{pineapple_take_body}}</div>\n<div class="disclaimer">Our read, not a forecast — and not personal advice. Markets carry real risk of loss.</div>\n<div class="footer-mark"><div class="logo-emoji" style="font-size:28px;">🍍</div><div class="wm">PINEAPPLES</div><div class="pagenum">2 / 3 HEADLINES</div></div>\n</div>\n\n<div class="slide content" id="s4">\n<div class="eyebrow">03 · On The Radar</div>\n<div class="bar"></div>\n<div class="headline" style="font-size:50px;">What could move the next session</div>\n<div style="margin-top:26px;">\n{{radar_rows}}\n</div>\n<div class="footer-mark"><div class="logo-emoji" style="font-size:28px;">🍍</div><div class="wm">PINEAPPLES</div><div class="pagenum">3 / 3 HEADLINES</div></div>\n</div>\n\n<div class="slide" id="s5">\n<div class="brandrow" style="display:flex; align-items:center; gap:16px;"><div class="logo-emoji" style="font-size:46px;">🍍</div><div class="wordmark" style="font-family:Bitter,Georgia,serif; color:var(--gold); font-weight:700; font-size:32px;">PINEAPPLES</div></div>\n<div class="eyebrow" style="margin-top:40px;">🍍 The Pineapple Index</div>\n<div class="idxcard">\n<div class="figure" data-field="index_figure">{{index_figure}}</div>\n<div class="figure-label" data-field="index_label">{{index_label}}</div>\n<div class="idx-sub" data-field="index_body">{{index_body}}</div>\n</div>\n<div class="spacer"></div>\n<div class="cta">The full brief lands in your inbox daily, before every session.</div>\n<div class="handles">wearepineapples.com · @Pineapple_Desk (IG / X) · Pineapple Desk (FB)</div>\n<div class="risk">General information only, not personal financial advice — we don\'t know your circumstances, goals or risk tolerance. Trading and investing carry a real risk of loss, including of your full capital. Past performance doesn\'t predict future results.</div>\n</div>\n\n</body>\n</html>',
    'daily_radar': '<div class="radar-item"><div class="time" data-field="radar[{{i}}].time">{{time}}</div><div class="desc" data-field="radar[{{i}}].desc">{{desc}}</div></div>',
    'daily_stat': '<div class="stat"><div class="k" data-field="stats[{{i}}].k">{{k}}</div><div class="v" data-field="stats[{{i}}].v">{{v}}</div></div>',
    'trade_brand_row': '\n    <div style="display:flex;align-items:center;gap:16px;">\n      <div style="font-size:44px;line-height:1;">🍍</div>\n      <div style="font-family:\'Bitter\',serif;font-weight:700;font-size:26px;color:#1F3D2B;">Pineapples</div>\n    </div>',
    'trade_cover': '\n    <div class="slide" style="width:1080px;height:1350px;background:#1F3D2B;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 84px;text-align:center;position:relative;overflow:hidden;">\n\n    <svg width="1080" height="1350" style="position:absolute;top:0;left:0;opacity:0.07;" xmlns="http://www.w3.org/2000/svg">\n      <defs>\n        <pattern id="hatch-cov" width="46" height="46" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">\n          <line x1="0" y1="0" x2="0" y2="46" stroke="#B9791C" stroke-width="2"></line>\n        </pattern>\n      </defs>\n      <rect width="1080" height="1350" fill="url(#hatch-cov)"></rect>\n    </svg>\n      <div style="position:absolute;top:0;left:0;right:0;height:16px;background:#E8A93B;"></div>\n      <div style="font-size:152px;line-height:1;">🍍</div>\n      <div style="font-family:\'Bitter\',serif;font-weight:900;font-size:96px;line-height:1.02;color:#FBF3E4;margin-top:34px;">Pineapples</div>\n      <div style="font-family:\'Karla\',sans-serif;font-weight:500;font-size:31px;letter-spacing:0.03em;color:#E8A93B;margin-top:14px;">Wealth, welcomed.</div>\n      <div style="width:110px;height:3px;background:#E8A93B;margin:40px 0 36px 0;"></div>\n      <div style="font-family:\'Bitter\',serif;font-weight:700;font-size:56px;line-height:1.15;color:#FBF3E4;max-width:860px;">Market Opportunities</div>\n      <div style="font-family:\'Karla\',sans-serif;font-size:27px;color:#cddbc9;margin-top:16px;" data-field="date">{{date}} &middot; {{edition}}</div>\n      <div style="background:rgba(232,169,59,0.14);border:2px solid #E8A93B;border-radius:16px;padding:22px 30px;margin-top:40px;max-width:820px;">\n        <div style="font-family:\'Bitter\',serif;font-weight:700;font-size:32px;line-height:1.3;color:#FBF3E4;" data-field="hook_line">{{hook_line}}</div>\n      </div>\n      <div data-avoid style="position:absolute;bottom:66px;font-family:\'Karla\',sans-serif;font-weight:800;font-size:25px;letter-spacing:0.08em;color:#E8A93B;text-transform:uppercase;">Swipe &rarr;</div>\n    </div>',
    'trade_cta': '\n    <div class="slide" style="width:1080px;height:1350px;background:#FBF3E4;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 90px;text-align:center;position:relative;">\n      <div style="font-size:128px;line-height:1;">🍍</div>\n      <div style="font-family:\'Bitter\',serif;font-weight:900;font-size:62px;color:#1F3D2B;margin-top:34px;line-height:1.15;">Come Get Your<br>Pineapples</div>\n      <div style="font-family:\'Karla\',sans-serif;font-size:27px;color:#6b6459;margin-top:26px;max-width:780px;line-height:1.5;">Markets, side hustles, and the occasional philosophical detour &mdash; for people who already have a job and want to make smarter moves with the time they\'ve got.</div>\n      <div style="width:110px;height:3px;background:#E8A93B;margin:40px 0;"></div>\n      <div style="font-family:\'Bitter\',serif;font-weight:700;font-size:34px;color:#1F3D2B;">wearepineapples.com</div>\n      <div style="font-family:\'Karla\',sans-serif;font-weight:600;font-size:25px;color:#9c4620;margin-top:10px;">Follow @Pineapple_Desk</div>\n      <div style="position:absolute;bottom:60px;font-family:\'Karla\',sans-serif;font-size:17px;color:#a89b7f;">Not financial advice &middot; General information only.</div>\n    </div>',
    'trade_flyer_badge': '<div style="font-family:\'Karla\',sans-serif;font-weight:700;font-size:16px;letter-spacing:0.04em;color:#B9791C;background:#fdf1da;border:1.5px solid #E8A93B;border-radius:8px;padding:5px 10px;display:inline-block;margin-top:10px;text-transform:uppercase;">Higher RR &middot; lower confidence</div>',
    'trade_idea_card': '\n        <div style="display:flex;flex-direction:column;background:#ffffff;border:2px solid #e6dcc4;border-radius:18px;padding:30px 32px;margin-bottom:24px;">\n          <div style="display:flex;justify-content:space-between;align-items:center;">\n            <div style="font-family:\'Bitter\',serif;font-weight:700;font-size:40px;color:#1F3D2B;" data-field="ideas[{{i}}].ticker">{{ticker}}</div>\n            <div style="font-family:\'Karla\',sans-serif;font-weight:800;font-size:24px;color:#ffffff;background:{{dir_color}};padding:9px 24px;border-radius:22px;text-transform:uppercase;letter-spacing:0.04em;" data-field="ideas[{{i}}].dir">{{dir}}</div>\n          </div>\n          <div style="display:flex;gap:26px;margin-top:20px;font-family:\'Karla\',sans-serif;font-size:22px;color:#6b6459;flex-wrap:wrap;">\n            <div data-field="ideas[{{i}}].entry"><span style="color:#a89b7f;">Entry</span><br><span style="font-weight:700;color:#1F3D2B;font-size:29px;">{{entry}}</span></div>\n            <div data-field="ideas[{{i}}].stop"><span style="color:#a89b7f;">Stop</span><br><span style="font-weight:700;color:#9c4620;font-size:29px;">{{stop}}</span></div>\n            <div data-field="ideas[{{i}}].target"><span style="color:#a89b7f;">Target</span><br><span style="font-weight:700;color:#1F3D2B;font-size:29px;">{{target}}</span></div>\n            <div data-field="ideas[{{i}}].rr"><span style="color:#a89b7f;">RR</span><br><span style="font-weight:700;color:#1F3D2B;font-size:29px;">{{rr}}</span></div>\n            <div data-field="ideas[{{i}}].conf"><span style="color:#a89b7f;">Conf.</span><br><span style="font-weight:700;color:#B9791C;font-size:29px;">{{conf}}</span></div>\n          </div>\n          {{flyer_badge}}\n        </div>',
    'trade_opportunities': '\n    <div class="slide" style="width:1080px;height:1350px;background:#FBF3E4;display:flex;flex-direction:column;padding:64px 56px 50px 56px;">\n      {{brand_row}}\n      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:32px;">\n        <div style="font-family:\'Bitter\',serif;font-weight:900;font-size:54px;color:#1F3D2B;line-height:1.1;max-width:760px;">{{heading}}</div>\n        <div style="font-family:\'Karla\',sans-serif;font-size:20px;color:#a89b7f;">{{page_note}}</div>\n      </div>\n      <div style="font-family:\'Karla\',sans-serif;font-size:23px;color:#6b6459;margin-top:8px;">Not financial advice &middot; general information only</div>\n      <div data-box style="flex:1;display:flex;flex-direction:column;justify-content:center;margin-top:12px;">{{rows}}</div>\n    </div>',
    'trade_outcome_row': '\n        <div style="display:flex;flex-direction:column;background:#ffffff;border:2px solid #e6dcc4;border-radius:16px;padding:26px 30px;margin-bottom:20px;">\n          <div style="display:flex;justify-content:space-between;align-items:center;">\n            <div style="font-family:\'Karla\',sans-serif;font-weight:700;font-size:30px;color:#1F3D2B;" data-field="outcomes[{{i}}].ticker">{{ticker}} <span style="font-weight:500;color:#6b6459;font-size:22px;">({{dir}})</span></div>\n            <div style="font-family:\'Karla\',sans-serif;font-weight:800;font-size:22px;color:{{pill_fg}};background:{{pill_bg}};padding:10px 20px;border-radius:20px;" data-field="outcomes[{{i}}].result">{{result}}</div>\n          </div>\n          <div style="font-family:\'Karla\',sans-serif;font-size:21px;margin-top:14px;" data-field="outcomes[{{i}}].entry">{{detail}}</div>\n        </div>',
    'trade_outcomes': '\n    <div class="slide" style="width:1080px;height:1350px;background:#FBF3E4;display:flex;flex-direction:column;padding:64px 56px 50px 56px;">\n      {{brand_row}}\n      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-top:32px;">\n        <div style="font-family:\'Bitter\',serif;font-weight:900;font-size:50px;color:#1F3D2B;line-height:1.15;max-width:760px;">{{heading}}</div>\n        <div style="font-family:\'Karla\',sans-serif;font-size:20px;color:#a89b7f;">{{page_note}}</div>\n      </div>\n      <div style="font-family:\'Karla\',sans-serif;font-size:21px;color:#6b6459;margin-top:8px;font-style:italic;">{{session_label}} &middot; estimated from public market data, not an account statement</div>\n      <div data-box style="flex:1;display:flex;flex-direction:column;justify-content:center;margin-top:12px;">{{rows}}</div>\n    </div>',
    'trade_page': '<!DOCTYPE html><html><head><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bitter:wght@400;700;900&family=Karla:wght@400;500;700;800&display=swap">\n<style>\n  * { box-sizing: border-box; margin:0; padding:0; }\n  html,body { width:1080px; height:1350px; background:{{bg}}; font-family:\'Karla\',sans-serif; overflow:hidden; }\n</style></head><body>{{body}}</body></html>',
}
SCHEMA_MD = '# Pineapples carousel input\n\nWrite one JSON file per run, then render it. Read this file only; never the old HTML templates.\n\n## Both carousels\n\n```\npython3 pc.py daily content.json out_dir     # or: trade\n```\n\n- All values are plain text (JSON strings), except `flyer` (true/false). Write `&`, `<`, quotes and emoji as-is; never HTML.\n- Every field is required unless marked *optional*. Unknown fields are rejected.\n- Lengths below are rough guides in characters (tested with every field at its limit at once). The renderer measures the real fit.\n- List positions in messages count from 0: `radar[0]` is the first radar item.\n- Old `pineapples-*.png` files of the same carousel in `out_dir` are deleted first.\n\nExit codes:\n\n| Code | Meaning | What to do |\n|---|---|---|\n| 0 | Done. Prints the PNG paths, one per line. | Use them. |\n| 1 | Bad input, e.g. `missing field: cover_headline`. No PNGs written. | Fix that field, rerun. |\n| 2 | PNGs written, but text didn\'t fit, e.g. `overflow: slide 3 (pineapples-am-03.png) field pineapple_take_body: slide content is 84px too tall`. | Shorten the named field(s), rerun (at most twice). |\n\n## Daily carousel (`daily`)\n\nFive slides, `pineapples-am-01.png` … `-05.png` (or `pm`), 2160×2700.\n\n| Field | Type | Meaning | Rough max |\n|---|---|---|---|\n| `edition` | `"am"` or `"pm"` | Sets MORNING/EVENING EDITION and the file names. | |\n| `date_long` | text | e.g. `Wednesday, 30 September 2026` | 30 |\n| `cover_headline` | text | Punchy Big Story headline, two lines at most. | 40 |\n| `cover_subhead` | text | One sentence from the lead. | 150 |\n| `cover_pullquote` | text | Short line from The Pineapple Take. | 90 |\n| `ticker` | object | Keys `asx200`, `sp500`, `nasdaq`, `audusd`, `btc`; each `{"val", "chg", "dir"}`. Same figures as the email. `dir` is `up`, `down` or `flat`. | val 10, chg 16 |\n| `big_story_headline` | text | Slide 2 headline. | 90 |\n| `big_story_intro` | text | 2–3 sentences. | 300 |\n| `stats` | list of 1–4 `{"k", "v"}` | Label/value rows, figures already in the email. | k 28, v 12 |\n| `big_story_outro` | text | One closing sentence. | 120 |\n| `pineapple_take_quote` | text | The core call in one sentence. | 120 |\n| `pineapple_take_body` | text | The justification. | 400 |\n| `radar` | list of 3–4 `{"time", "desc"}` | Same events as the email; `time` like `11:30am AEST`. | time 16, desc 110 |\n| `index_figure` | text | e.g. `+2 🍍` or `−1.5 🍍` | 8 |\n| `index_label` | text, *optional* | Defaults to `per 100 pineapples ($5k) in the index`. | 45 |\n| `index_body` | text | One sentence in brand voice. Never a portfolio result. | 150 |\n\n```json\n{\n  "edition": "am",\n  "date_long": "Wednesday, 30 September 2026",\n  "cover_headline": "Yields bite, and CPI day decides the ASX",\n  "cover_subhead": "The US 10-year hit 5.28% overnight, and today\'s CPI print decides whether local stocks shrug it off.",\n  "cover_pullquote": "Our read: a cautious open, then the 11:30am CPI print sets the tone.",\n  "ticker": {\n    "asx200": {"val": "8,709", "chg": "Fut. −15pts", "dir": "down"},\n    "sp500": {"val": "7,412", "chg": "−0.19%", "dir": "down"},\n    "nasdaq": {"val": "24,880", "chg": "−0.27%", "dir": "down"},\n    "audusd": {"val": "0.6985", "chg": "−0.47%", "dir": "down"},\n    "btc": {"val": "US$81,200", "chg": "+0.8%", "dir": "up"}\n  },\n  "big_story_headline": "US yields at an 18-year high put rate-sensitive ASX names on notice",\n  "big_story_intro": "Wall Street slipped as the US 10-year touched 5.28%. Futures point to a softer ASX open, and August CPI at 11:30am is the day\'s big swing factor.",\n  "stats": [\n    {"k": "RBA cash rate", "v": "4.60%"},\n    {"k": "US 10-year yield", "v": "5.28%"},\n    {"k": "Nov RBA hike odds", "v": "~56%"},\n    {"k": "Brent crude", "v": "US$104.80"}\n  ],\n  "big_story_outro": "A hot CPI firms a November hike; a soft one gives tech some room.",\n  "pineapple_take_quote": "Expect a cautious, yield-watching morning that turns on the CPI print.",\n  "pineapple_take_body": "The RBA has said it\'s prepared to keep lifting. If CPI lands hot, tech and REITs wear it; if it\'s soft, today\'s dip looks like a window for the patient.",\n  "radar": [\n    {"time": "11:30am AEST", "desc": "Australian August monthly CPI."},\n    {"time": "11:30am AEST", "desc": "China official PMIs for September."},\n    {"time": "10:15pm AEST", "desc": "US ADP private payrolls."},\n    {"time": "Thu 12:00am AEST", "desc": "US August PCE inflation."}\n  ],\n  "index_figure": "−0.2 🍍",\n  "index_body": "A fifth of a pineapple slips off the hundred at the open. Hardly a fruit salad."\n}\n```\n\n## Trade carousel (`trade`)\n\nCover → Today\'s Opportunities (3 per page) → Trade Outcomes (3 per page) → call to action. Files `pineapples-01-cover.png`, `pineapples-02-opportunities-1.png` … `pineapples-NN-cta.png`, 1080×1350. Never use "trade tips", "fresh ideas" or "round" in any text.\n\n| Field | Type | Meaning | Rough max |\n|---|---|---|---|\n| `session` | `"ASX"` or `"US"` | ASX = Morning Edition / AUS session; US = Evening Edition / US session. | |\n| `date` | text | e.g. `Wednesday, 30 September 2026` | 30 |\n| `hook_line` | text | Cover callout, e.g. `3 opportunities + recent trade outcomes`. Vary it. | 90 |\n| `ideas` | list (0 or more) | This session\'s new suggestions. | |\n| `ideas[].ticker` | text | e.g. `CDA`, `AUD/USD` | 12 |\n| `ideas[].dir` | `"Long"` or `"Short"` | | |\n| `ideas[].entry`, `.stop`, `.target` | text | Levels as published, e.g. `63.60` | 10 |\n| `ideas[].rr` | text | Stated reward:risk, e.g. `2.0:1` | 7 |\n| `ideas[].conf` | text | e.g. `45%` | 5 |\n| `ideas[].flyer` | true/false, *optional* | Shows "Higher RR · lower confidence" (at most one idea). | |\n| `outcomes` | list (0 or more) | Same recap set as the email. | |\n| `outcomes[].ticker`, `.dir` | text, `"Long"`/`"Short"` | As above. | 12 |\n| `outcomes[].result` | one of `Not triggered`, `Still in play`, `Stop reached`, `Target reached`, `Closed at week\'s end` | Exact spelling, straight apostrophe. | |\n| `outcomes[].entry` | text | Originally published entry. | 10 |\n| `outcomes[].exit` | text | Required for the last three results: the stop/target level reached, or the week-end close. Ignored otherwise. | 10 |\n| `outcomes[].rr` | text | Required for the last three results: the idea\'s stated RR. Ignored otherwise. | 7 |\n\n```json\n{\n  "session": "ASX",\n  "date": "Wednesday, 30 September 2026",\n  "hook_line": "3 opportunities + recent trade outcomes",\n  "ideas": [\n    {"ticker": "CDA", "dir": "Long", "entry": "63.60", "stop": "61.40", "target": "68.00", "rr": "2.0:1", "conf": "45%"},\n    {"ticker": "AUD/USD", "dir": "Long", "entry": "0.6980", "stop": "0.6945", "target": "0.7050", "rr": "2.0:1", "conf": "40%", "flyer": true}\n  ],\n  "outcomes": [\n    {"ticker": "NVDA", "dir": "Long", "result": "Not triggered", "entry": "227.00"},\n    {"ticker": "BA", "dir": "Short", "result": "Still in play", "entry": "187.50"},\n    {"ticker": "SIG", "dir": "Long", "result": "Closed at week\'s end", "entry": "98.55", "exit": "100.26", "rr": "2.0:1"}\n  ]\n}\n```\n'

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
