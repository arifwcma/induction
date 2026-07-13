# Handover — Sydney Met Guest Lecture (ICT108)

For the next agent. This is a SEPARATE workstream from the product itself: Arif is
preparing a guest lecture explaining THIS project (the induction chatbot) as a
real-world AI case study, to a university IT class. It is not a coding task in the
"fix a bug" sense, but the deck IS built by a python-pptx script — treat that script
as real code (readable, re-runnable), just for a non-product artefact. Read
`.cursor/instructions.md` for how Arif wants you to behave (brief, label replies
R1/R2…, one best option, no walls of text). This file holds only what is NOT in the
other `.cursor` docs.

## 0. START HERE — current state (read this first)
- **Deadline: lecture is Tue 14 July 2026, 2:00–3:00 pm.** If you are reading this on
  the 14th, everything below about "polish" is secondary — steer to rehearsal (§6).
- **Format (changed Mon 13 July evening): 45 min talk + 15 min Q&A**, not a 60-min talk.
- **The deck was rebuilt FROM SCRATCH on Mon 13 July evening (~9–10:30 pm).** The old
  9-slide "5 steps" deck is gone (git history has it). The live artefacts are:
  - `lecture/deck.pptx` — 13 slides, phase-based narrative (see §4).
  - `lecture/transcript.md` — same speaker-note text as standalone prose, one section per
    slide, with per-slide minute marks summing to ~45. Easier for Arif to review/rehearse
    without opening PowerPoint.
  - `lecture/build_deck.py` — the generator. Source of truth for pptx content.
- **NOT yet committed** — the rebuild happened after Arif's last push. Commit when he asks
  (he commits lecture work straight to `main` like the rest of this repo).
- **Arif is mid-review.** At ~10:45 pm he had `notes.txt` (repo root) open — raw, cryptic
  review jottings, UNPROCESSED, no instructions attached yet. Verbatim gist of the lines:
  "why not off the shelf - last slide", "embedding - king queen", "pdf simplify",
  "openai api, anthropic api, cohere, embedding", "ollama - local", "terminologies",
  "additional - context - AI - reasonaning", "birds eye view - only one way - top-level",
  "embedding not ai". These look like slide-by-slide reactions / things he wants changed
  or wants to say out loud (e.g. "embedding not ai" may mean he wants the deck/transcript
  to stop implying embeddings are AI, or it's a point he wants to make; "ollama - local"
  likely relates to the birdseye slide's "build locally" chip). DO NOT guess-implement
  these. When he returns, ask him to walk through `notes.txt` line by line and turn each
  into a concrete edit or a rehearsal point.
- **Likely next asks, in order:** process `notes.txt` → wording tweaks → rehearsal
  support (his real bottleneck, §6) → commit + push.

## 1. The engagement (fixed facts)
- Arif is a GUEST LECTURER for unit **ICT108** at **Sydney Met** (Sydney Metropolitan).
  In person + live-streamed. Tue 14 July 2026, 2:00–3:00 pm.
- Speaker line: **Dr Mohammad Arifur Rahman, Analyst Programmer, Wimmera CMA, Victoria.**
- Goal: explain a real AI project at a CONCEPTUAL level — ideas + real problems, not code.
- **Audience calibration (decided this session):** students are not top-tier ("low grade
  uni", Arif's words). Agreed ceiling of THREE big ideas for the whole session:
  (1) search by meaning, not words; (2) a right-looking answer can be the wrong rule
  (scope); (3) never show an unchecked answer (verification + honesty). Everything deeper
  was deliberately pushed to one "look these up later" slide. If Arif proposes adding
  concepts back, remind him of this agreement once, then do what he says.
- **Emotional context (still matters):** first-ever hour-long lecture; nervous; candidly
  says the project was mostly built by Claude and he doesn't have strict end-to-end
  command of it. Content risk is low (his own project, real bugs, real fixes); the real
  lever is delivery confidence via rehearsal. Reassure with facts, don't patronise.

## 2. The case study identity (stable — keep consistent)
Arif cannot use the real induction bot publicly (office IP), so everything runs on an
invented but structurally identical stand-in:
- **Name: MetMate** — a chatbot answering Sydney Met student questions about university
  rules (enrolment, library, exams).
- Invented example rules, reused across slides — keep these EXACTLY consistent:
  - **Library hours:** general rule = 8am–10pm term time; a separate "Exam Period
    Appendix" says 24/7 access, exam period only. This is the Bug1 stand-in
    (lexical-match-over-relevance → confident wrong answer).
  - **Special consideration categories:** Medical, Bereavement, Carer, Equipment fault,
    Misadventure, Religious (six, invented). This is the Bug2 stand-in (false abstention:
    master list knows six, retrieval fetched passages for only two, naive verifier killed
    the whole correct answer).
- The real bugs behind the stand-ins are documented in the product-side `.cursor` docs if
  you need grounding, but never leak real specifics into lecture materials.

## 3. Hard constraints (Arif's, non-negotiable)
1. No office IP: no real code/prompts/clause text/server/client specifics — gist only.
2. Plain language: "PDF / documents", never "knowledge base / KB".
3. Circulated written materials (writeup, poster brief) are NEUTRAL third-person, not
   "you're invited" voice. (Deck + transcript.md are internal working material — fine to
   use em dashes and direct voice there; circulated writeups must avoid em dashes.)
4. Avoid phrasing that reads as less-academic (he rejected "no heavy coding").
5. Terminology used sparingly and flagged as look-up-able — this is now baked into slide 1
   (the "concepts over terminology" promise) and paid off by slide 12. Keep that
   promise-and-payoff pair intact if you restructure.

## 4. The deck — 13 slides, phase narrative (rebuilt Mon 13 July)
The spine: build the laziest bot, watch a real failure kill it, let the failure force the
next idea. "Phases", not "steps". Steps 5–10 carry a top-right MINI-MAP (two lanes:
Docs/Index over Question/Search/Draft/Check/Reply) with the active box teal-filled under
an amber magnifying-glass lens — implemented in `add_mini_map()` in `build_deck.py`. If
you add/remove/reorder phase slides, keep the mini-map's active box honest.

Slide list (exact current titles):
1. **Title** — "Talk to Your Documents", MetMate framing, terminology-disclaimer card
   ("concepts over terminology… look them up later"), Wimmera logo top-right.
2. **"Why not just upload it to ChatGPT?"** — warm-up hook: handbook.pdf → ChatGPT works
   for one person/one paid seat; scaling = build your own ChatGPT-like product or a seat
   per student; neither scales.
3. **"Why not any ready-made chatbot?"** — Chrome-vs-chatbot analogy + 4 reasons
   (diversified expectations / young field / no-code tools limited / moves fast), plus an
   amber TEASER line ("every domain adds needs of its own — hold that thought") that
   slide 13 explicitly calls back. Keep teaser and callback in sync.
4. **"MetMate at a glance"** — deliberately coarse two-lane birdseye (built once:
   Documents → Index; live: Question → Search → Draft → Check → Reply) + three context
   chips: (a) chatbot = the classic first LLM-course project, buildable fully locally
   with decent hardware; (b) no standard blueprint yet — this diagram is ONE way, ours;
   (c) real users → three API providers: OpenAI (text into meaning-points + fast
   mechanical chores), Anthropic (writes the final answers), Cohere (re-ranks results).
5. **"Phase 1 — just match the words"** — word-overlap search, passage A/B/C score bars,
   "decades-old search, no AI needed".
6. **"Phase 1 breaks: right words, wrong rule"** — library 24/7 vs Exam Period Appendix,
   match scores shown, "phase 1 is dead". Transcript notes TWO things broke: words≠meaning
   AND nothing checked applicability — sets up the two-part phase-2 fix.
7. **"Phase 2 — search by meaning"** — embeddings, queen − female + male ≈ king diagram,
   ends "that's half the fix".
8. **"Phase 2 — say when each rule applies"** — scope tags (EXAM PERIOD ONLY / TERM TIME)
   attached at storage time; MetMate now answers the library question correctly.
   Transcript calls this "the most transferable lesson of the lecture".
9. **"Phase 3 — it refuses what it knows"** — verifier added for the right reasons, then
   the special-consideration false-refusal: master list six vs passages two.
10. **"Phase 3 — the right evidence per claim"** — existence/how-many → master list;
    detail of one rule → actual passage; bottom strip = the folded-in honesty capstone
    (unsupported → search once more → answer or honest "I don't know"). The old
    standalone "never make it up" slide was CUT deliberately (three-ideas ceiling, §1) —
    don't resurrect it without Arif asking.
11. **"The whole system — built by its failures"** — full two-lane architecture
    colour-coded by phase (grey/PANEL_LINE = phase 1 skeleton, teal = phase 2
    meaning+applicability, amber = phase 3 verification+honesty), legend, payoff line
    "every coloured box exists because a failure forced it".
12. **"What we skipped (look these up later)"** — six chips: hybrid retrieval, reranking,
    query rewriting, question splitting, conversation memory, two-model design. Pays off
    slide 1's promise; keeps deep machinery out of the main story.
13. **"Make it fit the domain"** — callback to slide 3's teaser; three invented-but-real
    inspiration examples: GIS assistant (aware of the user's live map view/actions —
    Arif's own field), weather assistant (must forecast, documents only describe the
    past), finance assistant (analyses in idle time, prepares likely answers). Ends
    "the recipe is public — fitting it to a domain is yours" + thank-you/questions.

Timing budget (transcript minute marks): 2 / 3 / 4 / 4.5 / 3 / 4 / 5 / 4 / 4 / 4 / 3 /
1.5 / 3 ≈ 45. Slides 5–6 and 12 are the "few seconds per point" fast slides; 4 and 7
are the slow ones.

## 5. Build workflow (important — avoid losing Arif's edits)
- `lecture/build_deck.py` is the source of truth for pptx CONTENT. Re-running it
  regenerates `deck.pptx` from scratch and SILENTLY DISCARDS any manual edits Arif made
  in PowerPoint since the last generation.
- Arif DOES sometimes hand-edit `deck.pptx` directly for small wording tweaks (happened
  in a previous session). Before re-running `build_deck.py`, ALWAYS dump the current pptx
  text and diff it against the script's strings, folding his hand-edits into the script.
  (Checked at rebuild time Mon 13 July: no drift existed then.) Dump recipe — do NOT
  print to the PowerShell console, Unicode ✓/✗ glyphs crash `cp1252` stdout; write a
  UTF-8 file and Read it:
  ```python
  from pptx import Presentation
  prs = Presentation('lecture/deck.pptx')
  with open('lecture/_dump.txt', 'w', encoding='utf-8') as f:
      for i, slide in enumerate(prs.slides, 1):
          f.write(f'--- Slide {i} ---\n')
          for shape in slide.shapes:
              if shape.has_text_frame and shape.text_frame.text.strip():
                  f.write(repr(shape.text_frame.text) + '\n')
  ```
  Delete the dump (and any helper script) after use — scratch, not deliverables.
- Speaker notes live in TWO places kept in sync: the `NOTES` dict in `build_deck.py`
  (embedded into the pptx via `notes_slide`) AND `lecture/transcript.md`. Edit one →
  edit the other. Transcript slide numbers must match actual deck order; they have
  drifted before when slides were inserted.
- Visual style matches `lecture/build_flyer.py`: deep-navy `#0B1B33` bg, teal `#2DD4BF`
  and amber `#F5B342` accents, red `#E06C6C` for failures, `Segoe UI`, rounded-rect
  cards. Helper functions (`solid`, `no_line`, `txt`, `card`, `circle`, `arrow_right`,
  `straight_line`, `failure_chip`, `add_mini_map`) are duplicated in `build_deck.py`,
  not shared with the flyer script — keep in sync by eye.
- Preview mechanism (Windows host, no LibreOffice): export ALL slides at once via
  PowerPoint COM automation, then Read the PNGs:
  ```powershell
  $p = New-Object -ComObject PowerPoint.Application
  $pres = $p.Presentations.Open("<abs path to deck.pptx>", $true, $false, $false)
  $pres.Export("<abs output dir>", "PNG", 1600, 900)
  $pres.Close(); $p.Quit()
  ```
  Treat the output dir as scratch and delete it after. Works, used Mon 13 July.
- `python-pptx` is installed GLOBALLY on this machine (`python -m pip install
  python-pptx`); there is no repo venv for lecture work. On a fresh machine, install it
  first.
- Logo lives at `lecture/lecture_resources/logo-wimmera-white.png`. `build_deck.py`
  resolves it relative to its own file — portable. The OLDER `build_flyer.py` still
  hardcodes a stale absolute path from another machine; fix that first if you ever
  regenerate `flyer.pptx`.

## 6. What's actually left / how to steer
1. **Process `notes.txt` with Arif** (see §0) — line-by-line, each becomes an edit or a
   talking point. Highest-priority open item.
2. **Rehearsal is the real bottleneck** (his own admission — nervous about delivery, not
   material). Once wording settles, push him to read `transcript.md` aloud 2–3 full
   passes against the clock rather than polishing slides indefinitely. Useful support:
   listen for slides that overrun their minute mark; the 45-min budget has no slack for
   a 5-min tangent.
3. **Commit + push** the rebuilt `deck.pptx`, `transcript.md`, `build_deck.py` (and this
   file) when he says so — he may present from a different machine.
4. Poster (external designer, from `design_brief.txt`) and its missing inputs (host logo,
   headshot, venue name, stream link/passcode, QR code, footer CRICOS/website, Wimmera
   co-branding decision) — outstanding, untouched for two sessions. Given the lecture is
   tomorrow, it may be dead; ask before spending time on it.
5. Deferred and probably dead: the deep "query time" mental-model walkthrough
   (`lecture_project.md` TODO, `lesson.md` Part A only). Arif explicitly deprioritized
   it; only resume if he asks. `lecture_project.md` and `lesson.md` are STALE for
   sequencing (their content on ingestion is still accurate); THIS file is the live plan.

## 7. Conventions
- Lecture materials live in `lecture/`; this handover in `.cursor/`. Git remote
  `git@wcma:arifwcma/induction.git`, branch `main`. Never commit secrets.
- `lecture/deck.pptx`, `lecture/transcript.md`, `lecture/build_deck.py` are tracked —
  keep them committed so a fresh pull has the live state.
- Responses to Arif: labelled R1/R2/…, brief, one best option, numbered lists, invite
  elaboration instead of dumping it.
