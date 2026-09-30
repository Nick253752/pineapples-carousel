# Switchover text for the four scheduled tasks

For Claude (Cowork). Paste-ready replacements for the carousel "build" and "render" steps. Everything else in each prompt (research, writing, the email, ordering, caption, chat delivery, Discord, run summary) stays as it is.

- **Daily (AM and PM):** the text below replaces the whole of **STEP 5 — BUILD THE CAROUSEL** (including the `--- CAROUSEL HTML TEMPLATE ---` … `--- END TEMPLATE ---` block) and **STEP 6 — RENDER**. Use it twice, changing only the one line marked AM/PM.
- **Trade (ASX and US):** the text below replaces the carousel build step: "build the PNGs with the Python/Playwright script", the pasted build script, and any carousel template reading. Use it twice, changing only the one line marked ASX/US.
- `<GITHUB_TOKEN>` is a placeholder. Nick pastes the real token from `C:\Pineapples\carousel\secrets\github-token.txt` into all four prompts at switchover. It is read-only and expires 29 Sep 2027 (UTC).
- Remove any instruction to read the old templates (`pineapple-social-carousel-template.md`, the carousel HTML template). The schema replaces them.

---

## Daily version (AM and PM)

```text
STEP 5 — BUILD THE CAROUSEL (renderer). The email has already been sent in STEP 4; nothing in this step can affect it.

a) DOWNLOAD the renderer and its schema (private repo, read-only token):
   mkdir -p carousel && cd carousel
   TOKEN='<GITHUB_TOKEN>'
   BASE=https://raw.githubusercontent.com/Nick253752/pineapples-carousel/main
   curl -fsSL -H "Authorization: Bearer $TOKEN" "$BASE/dist/pineapples_carousel.py" -o pc.py \
     && curl -fsSL -H "Authorization: Bearer $TOKEN" "$BASE/SCHEMA.md" -o SCHEMA.md; echo "download exit=$?"
   If the download fails (non-zero exit, retry once), skip the carousel, caption and Discord steps and put "Carousel skipped: renderer download failed (<error>). If this is HTTP 401/404 after 29 Sep 2027, the GitHub token has expired." in the FINAL RUN SUMMARY. Do not try to rebuild the slides by hand.

b) READ SCHEMA.md (the "Both carousels" and "Daily carousel" sections). It is the only carousel reference you need. Never look for or rebuild the old HTML template.

c) WRITE content.json from the content you already wrote in STEP 2, following SCHEMA.md exactly. Rules that still apply:
   - "edition": "am"   ← AM task. PM task: "pm".
   - Every figure must match the email exactly; never invent numbers. Ticker = the same 5 snapshot values/changes as the email, each with "dir" up / down / flat.
   - Skip Trade School (not used on social).
   - cover_headline = a punchy version of the Big Story headline (two lines at most, ~40 characters); cover_subhead = one sentence from lead_body; cover_pullquote = a short line from The Pineapple Take.
   - stats: up to 4 label/value pairs using only figures already in the email (fewer is fine; never pad with a made-up number).
   - radar: the same 3–4 events as the email.
   - index_figure like "+2 🍍" or "−1.5 🍍"; index_body is one brand-voice sentence and never a portfolio result. Leave out index_label (the fixed wording is built in).
   - Write plain text only (no HTML); &, <, quotes and emoji are fine as-is.

d) RENDER (Playwright + Chromium are preinstalled; the renderer finds /opt/pw-browsers itself; never run `playwright install`):
   python3 pc.py daily content.json out; echo "render exit=$?"
   - exit 0: stdout lists the 5 PNGs (out/pineapples-am-01.png … -05.png, or -pm- for PM). Done; no need to open them to check for overflow.
   - exit 1: one line names a bad or missing field (e.g. "missing field: cover_headline"). Fix that field in content.json and rerun.
   - exit 2: the PNGs were written, but stderr names the slide and field(s) whose text didn't fit. Shorten the named field(s) and rerun, at most twice. If it still reports overflow after two reruns, use the last PNGs and mention the overflow in the FINAL RUN SUMMARY.
   Use the PNG paths from the last successful render in the steps below.

STEP 6 — (merged into STEP 5.)
```

Leave STEP 7 (caption) and STEP 8 (deliver + Discord) unchanged. They already use `pineapples-am-01.png` … `-05.png` (or `-pm-`), which is exactly what the renderer writes, now inside `out/`.

---

## Trade version (ASX and US)

```text
BUILD THE CAROUSEL (renderer). The subscriber email has already been sent; nothing in this step can affect it. Build from the same suggestions and recap already produced this run; don't re-derive anything.

a) DOWNLOAD the renderer and its schema (private repo, read-only token):
   mkdir -p carousel && cd carousel
   TOKEN='<GITHUB_TOKEN>'
   BASE=https://raw.githubusercontent.com/Nick253752/pineapples-carousel/main
   curl -fsSL -H "Authorization: Bearer $TOKEN" "$BASE/dist/pineapples_carousel.py" -o pc.py \
     && curl -fsSL -H "Authorization: Bearer $TOKEN" "$BASE/SCHEMA.md" -o SCHEMA.md; echo "download exit=$?"
   If the download fails (non-zero exit, retry once), skip the carousel and its Discord post and put "Carousel skipped: renderer download failed (<error>). If this is HTTP 401/404 after 29 Sep 2027, the GitHub token has expired." in the run summary. Do not fall back to the old build script.

b) READ SCHEMA.md (the "Both carousels" and "Trade carousel" sections). It is the only carousel reference you need. Don't read pineapple-social-carousel-template.md or write a build script.

c) WRITE content.json following SCHEMA.md exactly:
   - "session": "ASX"   ← ASX task. US task: "US".
   - "date": today's date, e.g. "Wednesday, 30 September 2026".
   - "hook_line": short and specific, varied each run (e.g. "3 opportunities + recent trade outcomes").
   - "ideas": this session's new suggestions only, in published order: ticker, dir (Long/Short), entry, stop, target, rr (the stated RR), conf; add "flyer": true on the (at most one) higher-RR / lower-confidence idea. An empty list is fine.
   - "outcomes": the same recap set as the email's "How Last Round Went" (previous session's ideas plus any week-end closes recorded this run). "result" is exactly one of: Not triggered · Still in play · Stop reached · Target reached · Closed at week's end ("Expired — not triggered" is written as "Not triggered"). "entry" always; "exit" and "rr" for Stop reached / Target reached / Closed at week's end (exit = the public stop/target level reached, or the week-end close; rr = the idea's stated RR). An empty list is fine.
   - Never use the words "trade tips", "fresh ideas" or "round" in any text. No Numbers slide and no example-account figures: the renderer has none, and don't read the spreadsheet.
   - Write plain text only (no HTML); &, <, quotes and emoji are fine as-is.

d) RENDER (Playwright + Chromium are preinstalled; the renderer finds /opt/pw-browsers itself; never run `playwright install`):
   python3 pc.py trade content.json out; echo "render exit=$?"
   - exit 0: stdout lists the PNGs in swipe order (out/pineapples-01-cover.png, -02-opportunities-1.png, … -NN-cta.png). Done.
   - exit 1: one line names a bad or missing field. Fix that field in content.json and rerun.
   - exit 2: the PNGs were written, but stderr names the slide and field(s) whose text didn't fit. Shorten the named field(s) and rerun, at most twice. If it still reports overflow after two reruns, use the last PNGs and note it in the run summary.

Then DELIVER exactly as before: SendUserFile all PNGs into this run's chat, and POST them to the Discord webhook with the hook line as content (at most 10 files per message; split across POSTs if there are more).
```

---

## Checklist for Cowork at switchover

1. In each of the four prompts, replace the steps named above and delete the old template or script text.
2. Put Nick's token in place of `<GITHUB_TOKEN>` (four places; he supplies it).
3. Set the one AM/PM or ASX/US line per task.
4. Watch the first run of each task. Its summary should show `download exit=0` and `render exit=0` (or a handled exit 2).
