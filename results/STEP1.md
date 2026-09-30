# Carousel renderer — Step 1 results

30 Sep 2026. For Nick and for Claude (Cowork), who will switch the four tasks over.

## In short

- The slide-building now lives in one downloadable file. A task writes a short JSON file and runs the renderer, which produces the PNGs.
- For the same content, the output matches today's method **pixel for pixel** (daily AM, daily PM and trade).
- All tests pass (17 of 17 checks).
- The code is in a **private** GitHub repository. The tasks download it with a read-only access token. The token expires **29 Sep 2027 14:00 UTC (midnight at the start of Thu 30 Sep 2027, Sydney time)**.
- Nothing was posted to Discord, no email was sent, and the scheduled tasks were not touched.

## What was built, and where

Folder `C:\Pineapples\carousel`, mirrored in the private repo `Nick253752/pineapples-carousel`:

| Path | What it is |
|---|---|
| `src/pineapples_carousel.py` | Renderer code (readable). |
| `src/templates/*.html` | Slide templates, copied from today's templates. Hidden `data-field` tags were added so the overflow check can name fields; they don't change the image. |
| `build.py` | `python build.py` bundles `src/` and `SCHEMA.md` into one file. |
| `dist/pineapples_carousel.py` | **The file the tasks download and run.** Standard library + Playwright only. |
| `SCHEMA.md` | The only thing a task reads: every field, its meaning, length guide, and a full example for each carousel. `python3 pc.py schema daily\|trade` prints the same text. |
| `samples/` | Test inputs (real 30 Sep ASX session data, plus edge cases). |
| `tests/run_tests.py` | All six tests. `tests/original_method.py` reproduces today's method for the parity test. `tests/secret_scan.py` is the pre-push scan. |
| `results/` | This file and `SWITCHOVER.md`. |

Not in the repo (ignored): `reference/`, `secrets/`, the local Python/Chromium install (`.venv`, `.pw-browsers`), test output, and `BUILD-STEP1.md`.

Usage and exit codes are exactly as briefed: `daily|trade content.json out_dir`. Exit **0** prints the PNG paths only. Exit **1** prints one line naming the field, e.g. `missing field: cover_headline`, and writes no PNGs. Exit **2** writes the PNGs but prints `overflow: slide N (file) field X: …`.

## Test results

| # | Test | Result |
|---|---|---|
| 1 | **Parity**: today's method vs the renderer, same content. Daily AM (5 PNGs), daily PM (5), trade (4). | **PASS, pixel-identical**, every slide. Daily 2160×2700, trade 1080×1350. |
| 2 | **Trade from real data**: 30 Sep ASX ideas (CDA, MP1, AUD/USD) plus a 7-row recap with all five states. Also 0 ideas, 1 idea and 7 ideas (three opportunity pages). | **PASS**: 6, 4, 4 and 6 slides, correctly named and ordered. A daily with 3 radar items and 3 stats also passes. |
| 3 | **Overflow**: over-long text must exit 2 and name the field. | **PASS**. Daily: `slide 3 … field pineapple_take_body, pineapple_take_quote: slide content is 58px too tall`. Trade: `slide 1 … field hook_line: runs into "Swipe →"`. PNGs still written. |
| 4 | **Validation**: a missing field must exit 1 and name it. | **PASS**: `missing field: cover_headline`, no PNGs written. The examples in SCHEMA.md are also checked and valid. |
| 5 | **Escaping**: `&`, `<`, `>` and both kinds of quote. | **PASS**. Text shows exactly as typed (e.g. `Banks & miners <lead> a "risk-on" day's rally`), and no HTML is injected. |
| 6 | **Fonts offline**: Google Fonts unreachable, and Google Fonts hanging. | **PASS**. It finishes with the Georgia/Arial fallbacks in 2.4s (unreachable) and 12.9s (hanging), and never blocks. |

Also checked: the files download from the private repo with the token (HTTP 200, byte-identical); without the token GitHub refuses (404); a write attempt with the token is refused (403, read-only); and the downloaded copy renders a full deck.

The old-vs-new PNGs were opened side by side for Nick to confirm (`tests/out/parity.html` on his PC).

A note on test 1: I first compared images with a method that only looked at transparency. I caught this when the fonts test showed "identical" for visibly different images. I fixed the comparison to compare colour, re-ran everything, and parity is still exact.

## Hosting

- Repo: https://github.com/Nick253752/pineapples-carousel (**private**, at Nick's request instead of public).
- Renderer: `https://raw.githubusercontent.com/Nick253752/pineapples-carousel/main/dist/pineapples_carousel.py`
- Schema: `https://raw.githubusercontent.com/Nick253752/pineapples-carousel/main/SCHEMA.md`
- Both need the header `Authorization: Bearer <GITHUB_TOKEN>`.
- **Token:** fine-grained, only this repository, Contents read-only. It's saved only in `C:\Pineapples\carousel\secrets\github-token.txt` and is not in the repo or in these write-ups. Nick adds it to the tasks at switchover.
- **Token expiry:** 29 Sep 2027 14:00 UTC, which is midnight at the start of Thu 30 Sep 2027 in Sydney. The last full day it works is Wed 29 Sep 2027. After that, downloads fail with HTTP 401/404 until Nick creates a new token and updates the four tasks. Suggested reminder: early September 2027.
- The pre-push scan found nothing (no webhook, mailbox names, email addresses, keys or tokens). Commits use GitHub's private no-reply address.

## Decisions I made

1. **"Closed at week's end" pill:** a solid **Fruit Crate Green `#1F3D2B`** pill with **Ivory Cream `#FBF3E4`** text. This is the only solid pill, so it reads as "settled" and is distinct from the other four. Its Exit figure is green `#1F3D2B` (Stop uses terracotta and Target uses gold, as today). It shows Entry, Exit and RR like the other concluded states.
2. **Empty pages:** with 0 ideas, the Opportunities page says "No new opportunities this session." With 0 outcomes, the Trade Outcomes page says "No trade outcomes to report this session." Today's script would have shown a blank page. The deck order is unchanged.
3. **Fewer than 4 stats or radar items:** the daily template has exactly 4 of each. The renderer accepts 1–4 stats and 3–4 radar items and simply leaves out the missing rows, rather than rendering blank ones.
4. **Less for the task to fill in:** the edition label comes from `edition` (am → MORNING EDITION). The trade edition and session label come from `session` (ASX → Morning Edition / AUS session, US → Evening Edition / US session). `index_label` defaults to the fixed wording.
5. **Strict input:** unknown fields are rejected, so a typo fails loudly instead of leaving a field out. `exit`/`rr` are required for Stop reached, Target reached and Closed at week's end, and ignored for the other two states.
6. **Overflow rules:** text counts as overflowing if a slide holds more than fits, a word is too wide for its box, text leaves the slide, or the trade cover's hook line comes within 40px of "SWIPE →" (so it's flagged before it crowds it).
7. **Fonts:** Google Fonts requests get a 10s hard timeout, and the renderer waits up to 8s for fonts to be ready. The trade deck now also waits for fonts to be ready (today's script only waited for network idle), which can only prevent an occasional fallback-font slide.
8. **Old files:** before rendering, the renderer deletes that carousel's old `pineapples-*.png` files in the output folder, so a shorter deck never leaves stale slides behind.
9. **Length guides** in SCHEMA.md were measured, not guessed. Every field was set to its guide length at once and rendered cleanly. The daily cover is the tight one: a headline over ~40 characters goes to three lines and pushes the cover over.

## Differences from today's output

- **None for the same content.** Parity was pixel-identical on all 14 slides.
- New, by design: the "Closed at week's end" pill, the two empty-page messages, and missing rows omitted when there are fewer than 4 stats or radar items.
- Unchanged: daily PNGs are 2160×2700 and trade PNGs are 1080×1350, exactly as today's scripts produce them. The file names are unchanged too.
- Parity was run on Nick's PC (Chromium 153, Windows emoji). In the cloud sandbox both methods use the same Linux Chromium and emoji font, so the switch changes nothing there either.

## Housekeeping

- The local test install (`.venv`, `.pw-browsers`, about 500 MB) can be deleted any time. It's only needed to rerun tests here.
- To change a design later: edit `src/templates/`, run `python build.py`, run `python tests/run_tests.py` and `python tests/secret_scan.py`, then commit and push.
