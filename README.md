# U.S. AutoForce Safety Huddle Generator

A weekly, branded safety briefing sheet for U.S. AutoForce drivers. Pick a week, get a one-page letter PDF built from a rotating pool of 24 topics, in **English or Spanish** — no typing, no design work.

The same tool also has a separate **warehouse** variant (see below).

## What you get

A single printable page per week containing:

- The U.S. AutoForce logo and the week's date range, with a topic callout.
- The week's topic broken into short, readable items and a checklist.
- A bottom strip covering the three fixed reminders — **cameras, phones, three points of contact** — which appear every week regardless of the topic.
- A footer with the tagline and the discussion questions.

Everything fits on **one page**, and that is verified rather than assumed: all 53 ISO weeks were rendered in both languages and checked with `pdfinfo` (106 PDFs, 0 failures).

Real output is checked into [`samples/`](samples/) so you can see what you get before running anything:

- [`samples/driver-wk42-en.pdf`](samples/driver-wk42-en.pdf) — driver sheet, English
- [`samples/driver-wk42-es.pdf`](samples/driver-wk42-es.pdf) — driver sheet, Spanish
- [`samples/warehouse-wk42-both.pdf`](samples/warehouse-wk42-both.pdf) — warehouse sheet, bilingual side-by-side (2 pages, since it carries both languages)

## Two ways to run it

### 1. The HTML generator (this is the one for the work laptop)

`safety-huddle-generator.html` in this repo — a self-contained 148 KB file with the logo, all 24 topics, the CSS and the JavaScript inlined. No Python, no network, no dependencies. Download it, double-click it on the Windows work laptop, and it opens in Edge or Chrome.

Controls along the top:

| Control | What it does |
| --- | --- |
| Prev / This / Next Week | Step through ISO weeks |
| Show Topic Pool | List all 24 topics |
| Zoom − / + | Bigger or smaller on screen |
| **Español / English** | Toggle language for the whole sheet |
| **3D Deck: On/Off** | Toggle the animated command-deck background |
| Print | Print / Save as PDF |

The 3D deck is a screen-only decoration. It is stripped out by the `@media print` block, so the printed PDF is identical whether it is on or off.

Two URL parameters are handy for sharing a specific sheet directly:

- `?week=42` — open straight to that ISO week
- `?lang=es` — open in Spanish

The chosen language also persists in `localStorage`, so once you switch to Spanish it stays there.

### 2. The Python CLI (this PC)

`safety_huddle.py` in this repo — no third-party packages, just the standard library.

```bash
python3 safety_huddle.py              # this week's sheet
python3 safety_huddle.py --week 35    # a specific ISO week
python3 safety_huddle.py --lang es    # Spanish
python3 safety_huddle.py --list       # list all topics
python3 safety_huddle.py --preview    # generate, then open in a browser
```

Output lands as `safety-huddle-wkNN.html` and `.pdf` (on this PC, in `~/Desktop/work/`), where `NN` is the zero-padded ISO week.

The repo also includes the double-click launchers used on this PC — `Safety-Huddle.desktop` and `Generate-Safety-Huddle.sh`. They hardcode `~/Desktop/work`, so they are a reference for recreating a launcher rather than something portable.

## How the weekly rotation works

Topics are picked deterministically from the ISO week number, so the same week always produces the same sheet — you can regenerate last week's handout and get exactly what you handed out. The three bottom-strip reminders are fixed and repeat every week on purpose.

## Topics

All 24 are driver topics:

1. Accident Prevention — Top 5 Causes
2. Pre-Trip & Post-Trip — Non-Negotiable
3. Air Brake Quick-Check Numbers
4. DOT Weight Limits — Know Your Numbers
5. Defensive Driving — Stay Sharp
6. Hours of Service — Stay Compliant
7. Seatbelt Usage — Zero Exceptions
8. Phone & Device Rules — Zero Tolerance
9. Backing Safety — GOAL
10. If You're in an Accident — Immediate Steps
11. Adverse Weather Driving
12. Cargo Securement — Before Every Trip
13. Delivery Site & Parking Lot Safety
14. Road Rage & Aggressive Drivers
15. Fatigue Management — Don't Push It
16. Fuel Management & Emissions
17. Samsara Dash Cameras
18. Work Zone Safety — Slow Down
19. CSA Program — Your Score Matters
20. Driver Wellness — Take Care of Yourself
21. Intersection Safety — Look Twice
22. Railroad Crossings — Stop, Look, Listen
23. 3 Points of Contact — Every Time
24. Roadside Inspections — Be Ready

Each topic carries `title` / `items` (or `checklist`) / `callout` in English and `es_title` / `es_items` / `es_callout` in Spanish. Spanish falls back to English wherever a translation is missing, so a half-translated topic still renders.

## Editing a topic

Edit `safety_huddle.py` — the `TOPICS` list is plain data. Then rebuild the HTML file so the laptop copy picks it up:

```bash
python3 safety_huddle_build_html.py
```

The builder imports the module from its own folder and reuses its `TOPICS` and `CSS` verbatim, so the Python and HTML versions cannot drift apart on content. The rebuild is byte-stable — running it twice on unchanged sources produces an identical file, and it matches the HTML checked into this repo.

The **3D command-deck theme and the language toggle live only in the HTML generator**, added by the builder. The Python version is the plain print path and intentionally has neither, since its whole job is to produce the PDF.

## The warehouse variant

The repo also carries a **Warehouse Safety Huddle** generator for warehouse and tire-distribution staff — forklifts, pallet jacks, batteries and charging, scissor and aerial lifts, loading docks, racking and tire storage, LOTO, PPE, housekeeping, ergonomics.

It is a separate tool with its own sources and its own topic pool: **32 topics, each written in both English and Spanish**, with a three-way language switch:

```bash
python3 ~/scripts/warehouse_huddle.py --lang en     # English sheet
python3 ~/scripts/warehouse_huddle.py --lang es     # Spanish sheet
python3 ~/scripts/warehouse_huddle.py --lang both   # bilingual, side by side
```

The `both` mode is what produces the `-wkNN-both.html` / `.pdf` files — one sheet an English-speaking and a Spanish-speaking employee can read together, rather than two handouts. Its single-file generator, `warehouse-safety-huddle-generator.html`, has the same control bar and the same screen-only 3D deck as the driver version.

The two tools share no code beyond the brand logo, so changing one never affects the other.

## Repository layout

| Path | What it is |
| --- | --- |
| `safety_huddle.py` | Driver topics — Python CLI + the canonical `TOPICS` and CSS |
| `safety_huddle_build_html.py` | Builds the driver HTML generator |
| `safety-huddle-generator.html` | The built driver generator (EN/ES) — **this is the file for the work laptop** |
| `warehouse_huddle.py` | Warehouse topics — Python CLI + `TOPICS` (32 × EN/ES) and CSS |
| `warehouse_huddle_build_html.py` | Builds the warehouse HTML generator |
| `warehouse-safety-huddle-generator.html` | The built warehouse generator (EN/ES/both) |
| `brand/logo-print-b64.txt` | The AutoForce logo as base64 JPEG, embedded into every sheet |
| `Generate-Safety-Huddle.sh`, `Safety-Huddle.desktop` | Double-click launchers (see note below) |

Both `.py` generators are the source of truth; the two `.html` files are **built artifacts that are checked in on purpose**, because the work laptop needs them and has no Python. Rebuild them after any topic edit.

## Rebuilding from a clone

The build scripts resolve their imports and the logo relative to their own location, so a plain clone works:

```bash
git clone https://github.com/joshwheeler8206-cell/safety-huddle.git
cd safety-huddle
python3 safety_huddle_build_html.py
python3 warehouse_huddle_build_html.py
```

Output goes to `~/Desktop/work/` when that folder exists (the normal setup on this PC), and falls back to the repo folder otherwise. The result is byte-identical to the checked-in HTML as long as the sources are unchanged, so rebuilding on a clone is a safe way to confirm nothing was edited by hand.

On this machine the live sources also sit at `~/scripts/safety_huddle.py` and `~/Desktop/work/safety_huddle.py` — those are the **same files**, not copies, so editing any of them works.

## Publishing an update

The live working copies are in `~/scripts/` (that is what the desktop launchers and the normal editing habit use). After changing a topic, push it back out so the repo and the laptop copy stay in step:

```bash
# 1. edit the live source
nano ~/scripts/safety_huddle.py

# 2. rebuild the browser version
python3 ~/scripts/safety_huddle_build_html.py

# 3. copy the changed files into a clone and push
cd ~/safety-huddle
cp ~/scripts/safety_huddle.py ~/scripts/safety_huddle_build_html.py .
cp ~/Desktop/work/safety-huddle-generator.html .
git add -A && git commit -m "Update <topic>" && git push
```

`~/safety-huddle/` is the local clone of this repo. If you skip step 3 the repo keeps the old topic — the browser file on the work laptop is only as fresh as the last push.

## Gotchas

- **One-page fit is fragile.** The CSS spacing and the `@page` margin are tuned against the *longest* topics (weeks 13, 52 and 53 have six-item bottom strips). After changing any size, re-render all 53 weeks in both languages and check `pdfinfo` page counts rather than eyeballing one week.
- **Headless Chrome and `localStorage` do not mix.** Each headless invocation gets a fresh profile, which is why the `?lang=es` URL parameter exists — pass the language in the URL instead of relying on the stored preference.
- **The `.desktop` launchers run the Python path**, so they always produce English. For a Spanish sheet on this PC, run the CLI with `--lang es`, or use the HTML generator and press the language button.
