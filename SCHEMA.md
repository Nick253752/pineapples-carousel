# Pineapples carousel input

Write one JSON file per run, then render it. Read this file only; never the old HTML templates.

## Both carousels

```
python3 pc.py daily content.json out_dir     # or: trade
```

- All values are plain text (JSON strings), except `flyer` (true/false). Write `&`, `<`, quotes and emoji as-is; never HTML.
- Every field is required unless marked *optional*. Unknown fields are rejected.
- Lengths below are rough guides in characters (tested with every field at its limit at once). The renderer measures the real fit.
- List positions in messages count from 0: `radar[0]` is the first radar item.
- Old `pineapples-*.png` files of the same carousel in `out_dir` are deleted first.

Exit codes:

| Code | Meaning | What to do |
|---|---|---|
| 0 | Done. Prints the PNG paths, one per line. | Use them. |
| 1 | Bad input, e.g. `missing field: cover_headline`. No PNGs written. | Fix that field, rerun. |
| 2 | PNGs written, but text didn't fit, e.g. `overflow: slide 3 (pineapples-am-03.png) field pineapple_take_body: slide content is 84px too tall`. | Shorten the named field(s), rerun (at most twice). |

## Daily carousel (`daily`)

Five slides, `pineapples-am-01.png` … `-05.png` (or `pm`), 2160×2700.

| Field | Type | Meaning | Rough max |
|---|---|---|---|
| `edition` | `"am"` or `"pm"` | Sets MORNING/EVENING EDITION and the file names. | |
| `date_long` | text | e.g. `Wednesday, 30 September 2026` | 30 |
| `cover_headline` | text | Punchy Big Story headline, two lines at most. | 40 |
| `cover_subhead` | text | One sentence from the lead. | 150 |
| `cover_pullquote` | text | Short line from The Pineapple Take. | 90 |
| `ticker` | object | Keys `asx200`, `sp500`, `nasdaq`, `audusd`, `btc`; each `{"val", "chg", "dir"}`. Same figures as the email. `dir` is `up`, `down` or `flat`. | val 10, chg 16 |
| `big_story_headline` | text | Slide 2 headline. | 90 |
| `big_story_intro` | text | 2–3 sentences. | 300 |
| `stats` | list of 1–4 `{"k", "v"}` | Label/value rows, figures already in the email. | k 28, v 12 |
| `big_story_outro` | text | One closing sentence. | 120 |
| `pineapple_take_quote` | text | The core call in one sentence. | 120 |
| `pineapple_take_body` | text | The justification. | 400 |
| `radar` | list of 3–4 `{"time", "desc"}` | Same events as the email; `time` like `11:30am AEST`. | time 16, desc 110 |
| `index_figure` | text | e.g. `+2 🍍` or `−1.5 🍍` | 8 |
| `index_label` | text, *optional* | Defaults to `per 100 pineapples ($5k) in the index`. | 45 |
| `index_body` | text | One sentence in brand voice. Never a portfolio result. | 150 |

```json
{
  "edition": "am",
  "date_long": "Wednesday, 30 September 2026",
  "cover_headline": "Yields bite, and CPI day decides the ASX",
  "cover_subhead": "The US 10-year hit 5.28% overnight, and today's CPI print decides whether local stocks shrug it off.",
  "cover_pullquote": "Our read: a cautious open, then the 11:30am CPI print sets the tone.",
  "ticker": {
    "asx200": {"val": "8,709", "chg": "Fut. −15pts", "dir": "down"},
    "sp500": {"val": "7,412", "chg": "−0.19%", "dir": "down"},
    "nasdaq": {"val": "24,880", "chg": "−0.27%", "dir": "down"},
    "audusd": {"val": "0.6985", "chg": "−0.47%", "dir": "down"},
    "btc": {"val": "US$81,200", "chg": "+0.8%", "dir": "up"}
  },
  "big_story_headline": "US yields at an 18-year high put rate-sensitive ASX names on notice",
  "big_story_intro": "Wall Street slipped as the US 10-year touched 5.28%. Futures point to a softer ASX open, and August CPI at 11:30am is the day's big swing factor.",
  "stats": [
    {"k": "RBA cash rate", "v": "4.60%"},
    {"k": "US 10-year yield", "v": "5.28%"},
    {"k": "Nov RBA hike odds", "v": "~56%"},
    {"k": "Brent crude", "v": "US$104.80"}
  ],
  "big_story_outro": "A hot CPI firms a November hike; a soft one gives tech some room.",
  "pineapple_take_quote": "Expect a cautious, yield-watching morning that turns on the CPI print.",
  "pineapple_take_body": "The RBA has said it's prepared to keep lifting. If CPI lands hot, tech and REITs wear it; if it's soft, today's dip looks like a window for the patient.",
  "radar": [
    {"time": "11:30am AEST", "desc": "Australian August monthly CPI."},
    {"time": "11:30am AEST", "desc": "China official PMIs for September."},
    {"time": "10:15pm AEST", "desc": "US ADP private payrolls."},
    {"time": "Thu 12:00am AEST", "desc": "US August PCE inflation."}
  ],
  "index_figure": "−0.2 🍍",
  "index_body": "A fifth of a pineapple slips off the hundred at the open. Hardly a fruit salad."
}
```

## Trade carousel (`trade`)

Cover → Today's Opportunities (3 per page) → Trade Outcomes (3 per page) → call to action. Files `pineapples-01-cover.png`, `pineapples-02-opportunities-1.png` … `pineapples-NN-cta.png`, 1080×1350. Never use "trade tips", "fresh ideas" or "round" in any text.

| Field | Type | Meaning | Rough max |
|---|---|---|---|
| `session` | `"ASX"` or `"US"` | ASX = Morning Edition / AUS session; US = Evening Edition / US session. | |
| `date` | text | e.g. `Wednesday, 30 September 2026` | 30 |
| `hook_line` | text | Cover callout, e.g. `3 opportunities + recent trade outcomes`. Vary it. | 90 |
| `ideas` | list (0 or more) | This session's new suggestions. | |
| `ideas[].ticker` | text | e.g. `CDA`, `AUD/USD` | 12 |
| `ideas[].dir` | `"Long"` or `"Short"` | | |
| `ideas[].entry`, `.stop`, `.target` | text | Levels as published, e.g. `63.60` | 10 |
| `ideas[].rr` | text | Stated reward:risk, e.g. `2.0:1` | 7 |
| `ideas[].conf` | text | e.g. `45%` | 5 |
| `ideas[].flyer` | true/false, *optional* | Shows "Higher RR · lower confidence" (at most one idea). | |
| `outcomes` | list (0 or more) | Same recap set as the email. | |
| `outcomes[].ticker`, `.dir` | text, `"Long"`/`"Short"` | As above. | 12 |
| `outcomes[].result` | one of `Not triggered`, `Still in play`, `Stop reached`, `Target reached`, `Closed at week's end` | Exact spelling, straight apostrophe. | |
| `outcomes[].entry` | text | Originally published entry. | 10 |
| `outcomes[].exit` | text | Required for the last three results: the stop/target level reached, or the week-end close. Ignored otherwise. | 10 |
| `outcomes[].rr` | text | Required for the last three results: the idea's stated RR. Ignored otherwise. | 7 |

```json
{
  "session": "ASX",
  "date": "Wednesday, 30 September 2026",
  "hook_line": "3 opportunities + recent trade outcomes",
  "ideas": [
    {"ticker": "CDA", "dir": "Long", "entry": "63.60", "stop": "61.40", "target": "68.00", "rr": "2.0:1", "conf": "45%"},
    {"ticker": "AUD/USD", "dir": "Long", "entry": "0.6980", "stop": "0.6945", "target": "0.7050", "rr": "2.0:1", "conf": "40%", "flyer": true}
  ],
  "outcomes": [
    {"ticker": "NVDA", "dir": "Long", "result": "Not triggered", "entry": "227.00"},
    {"ticker": "BA", "dir": "Short", "result": "Still in play", "entry": "187.50"},
    {"ticker": "SIG", "dir": "Long", "result": "Closed at week's end", "entry": "98.55", "exit": "100.26", "rr": "2.0:1"}
  ]
}
```
