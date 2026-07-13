# Handover — Sydney Met Guest Lecture (ICT108)

For the next agent. This is a SEPARATE workstream from the product itself: Arif is
preparing tutoring material to explain THIS project (the induction chatbot) as a
real-world AI case study, to a university IT class. It is not a coding task in the
"fix a bug" sense, but the deck IS built by a python-pptx script — treat that script
as real code (readable, re-runnable), just for a non-product artefact. Read
`.cursor/instructions.md` for how Arif wants you to behave (brief, label replies
R1/R2…, one best option, no walls of text). This file holds only what is NOT in the
other `.cursor` docs.

## 0. START HERE — current state (read this first)
- Arif retired for the night after this session; git has been pushed. Resume seamlessly,
  git pull first if picking up from another PC.
- **Pivot from the original plan:** the original sequence in `.cursor/lecture_project.md`
  was (1) build Arif's end-to-end mental model fully → (2) build the deck → (3) transcripts.
  That was ABANDONED mid-way under a 2-hour deadline crunch: Arif said "we will get back to
  getting intuitive understanding on it later" and asked to jump straight to slides +
  transcript. `lecture_project.md` and `lesson.md` are now STALE for sequencing (still
  useful for their content — Part A ingestion mental model — but do not treat their TODO
  checklist as the live plan). This file supersedes them for "what's next."
- **The deck is BUILT and is the live plan now.** `lecture/deck.pptx` (13 slides,
  REBUILT from scratch on the night of Mon 13 July — see §4 for the new structure) +
  `lecture/transcript.md` (the same speaker-note text as a standalone doc, easier for Arif
  to review without opening PowerPoint, now with per-slide minute marks summing to 45) +
  `lecture/build_deck.py` (the generator script —
  edit this, don't hand-edit the pptx, EXCEPT Arif does sometimes hand-edit the pptx directly
  for small wording tweaks; see §4 workflow note, this WILL cause drift you must reconcile).
- **Full restructure on Mon 13 July (evening):** Arif changed the format to 45 min talk +
  15 min Q&A and proposed a new narrative: phases instead of steps. Phase 1 = bare-minimum
  word-match bot → breaks (Bug1 stand-in) → Phase 2 = meaning search + scope labels →
  Phase 3 = verifier added → breaks (Bug2 stand-in) → fix + honest abstention. Agreed
  trims for a weaker cohort: max three big ideas, old "step 5" folded into two sentences at
  the end of phase 3, deep machinery (reranking, hybrid retrieval, query rewriting, etc.)
  moved to a single "What we skipped — look these up later" slide. New elements: terminology
  disclaimer on slide 1, three-API-provider framing (OpenAI/Anthropic/Cohere) on the
  birdseye slide, mini-map with magnifying-glass lens on every phase slide, full
  architecture slide colour-coded by phase, closing slide = domain-specific inspiration
  (GIS/weather/finance bots), teaser on slide 3 that the closing slide calls back.
- **Where we left off:** 13-slide deck + transcript rebuilt and previewed, not yet
  reviewed by Arif slide-by-slide. Likely next asks: wording review, then REHEARSAL
  (his real bottleneck, see §5).
- **Deadline:** lecture is Tue 14 July 2026, 2:00–3:00 pm. Recompute remaining runway from
  today's date.

## 1. The engagement (unchanged facts)
- Arif is a GUEST LECTURER for a 1-hour session in unit **ICT108** at **Sydney Met**
  (Sydney Metropolitan). In person + live-streamed.
- Speaker line: **Dr Mohammad Arifur Rahman, Analyst Programmer, Wimmera CMA, Victoria.**
- Goal: explain a real AI project at a conceptual level — ideas + real problems, not code.
- **Emotional context (still matters):** first-ever hour-long lecture; nervous; candidly
  says the project was mostly built by Claude and he doesn't yet have strict end-to-end
  command of it. Content risk is low (it's his own project, real bugs, real fixes); the real
  lever is delivery confidence via rehearsal, not more content depth. Reassure with facts,
  don't patronise.

## 2. The case study identity (NEW — decided this session)
Because Arif cannot use the real induction bot publicly (office IP), the whole deck now
runs on an invented but structurally identical stand-in:
- **Name: MetMate** — a chatbot answering Sydney Met student questions about university
  rules (enrolment, library, exams), same shape as the real induction bot without touching
  real content.
- Concrete example rules invented for MetMate, reused across multiple slides — keep these
  consistent if you touch the deck again:
  - **Library hours**: general rule = 8am–10pm term time. A separate "Exam Period Appendix"
    says 24/7 access, but ONLY during exam period. This is the Bug1 (lexical-match-over-
    relevance) stand-in.
  - **Special consideration categories**: Medical, Bereavement, Carer, Equipment fault,
    Misadventure, Religious (six, invented). This is the Bug2 (false-abstention-on-coverage)
    stand-in — a master index lists all six, but a naive verifier only trusts the ones with
    a directly retrieved passage and wrongly refuses the rest.
- Do NOT swap in real EA clause numbers, real document names, or real server/client details
  anywhere in lecture materials — Arif is strict about this (see hard constraints below,
  unchanged from before).

## 3. Hard constraints (Arif's, for this lecture — unchanged, restated for completeness)
1. No office IP, no real code/prompts/clause text/server/client specifics — gist only.
2. Plain language: "PDF / documents", never "knowledge base / KB".
3. Circulated written materials (writeup, poster brief) are NEUTRAL third-person, not
   "you're invited" voice, not addressing the audience directly.
4. No em dashes in circulated writeups (the deck/transcript.md is fine to use them, that's
   internal working material, not circulated).
5. Avoid phrasing that reads as less-academic (he rejected "no heavy coding").

## 4. The deck — structure, wording decisions, and the build workflow
**Slide list (13 slides, in order, exact current titles — rebuilt Mon 13 July evening):**
1. Title — "Talk to Your Documents" + MetMate framing + terminology-disclaimer card
   ("concepts over terminology... look them up later") + Wimmera logo top-right.
2. "Why not just upload it to ChatGPT?" — the old step-1 hook promoted to the warm-up:
   handbook.pdf → ChatGPT works for one person/seat, doesn't scale to every student.
3. "Why not any ready-made chatbot?" — Chrome-vs-chatbot analogy, the 4 reasons
   (diversified expectations / young field / no-code tools limited / field moves fast),
   plus an amber teaser line ("every domain adds needs of its own — hold that thought")
   that slide 13 calls back.
4. "MetMate at a glance" — coarse two-lane birdseye (built once: Documents → Index; live:
   Question → Search → Draft → Check → Reply) + three context chips: chatbot as the classic
   first LLM-course project (buildable locally), no standard blueprint yet (this is one
   way: ours), real users → three API providers (OpenAI = meaning-points + fast chores,
   Anthropic = writes answers, Cohere = re-ranks results).
5. "Phase 1 — just match the words" — word-overlap search mechanism, passage A/B/C bars.
6. "Phase 1 breaks: right words, wrong rule" — library 24/7 vs Exam Period Appendix
   (Bug1 stand-in), match scores shown, "phase 1 is dead".
7. "Phase 2 — search by meaning" — embeddings, queen − female + male ≈ king ("half the fix").
8. "Phase 2 — say when each rule applies" — scope tags (EXAM PERIOD ONLY / TERM TIME)
   attached at storage; MetMate now answers the library question correctly.
9. "Phase 3 — it refuses what it knows" — verifier added, then the special-consideration
   false-refusal (Bug2 stand-in): master list has six, passages only two, answer killed.
10. "Phase 3 — the right evidence per claim" — existence/how-many → master list; detail →
    actual passage; plus the folded-in honesty capstone (search once more → honest
    "I don't know"). The old standalone "never make it up" step-5 slide was CUT (too many
    concepts for this cohort) and reduced to this slide's bottom strip.
11. "The whole system — built by its failures" — full two-lane architecture colour-coded
    by phase (grey = phase 1 skeleton, teal = phase 2 meaning+applicability, amber =
    phase 3 verification+honesty), with legend + payoff line "every coloured box exists
    because a failure forced it".
12. "What we skipped (look these up later)" — six chips: hybrid retrieval, reranking,
    query rewriting, question splitting, conversation memory, two-model design. Fulfils
    the slide-1 terminology promise; keeps the deep machinery out of the main story.
13. "Make it fit the domain" — callback to slide 3's teaser; GIS (aware of user's live map
    view/actions), weather (must forecast), finance (analyses in idle time) + "the recipe
    is public — fitting it to a domain is yours" + thank-you/questions line.

Phase slides (5–10) carry a top-right MINI-MAP (Docs/Index over Question/Search/Draft/
Check/Reply) with the active box teal-filled and an amber magnifying-glass lens over it —
implemented in `add_mini_map()` in `build_deck.py`. Slide 11 reuses the same two-lane
shape expanded. If you add/remove phase slides, keep the mini-map's active box honest.

**Build workflow (important, avoid losing Arif's edits):**
- `lecture/build_deck.py` is the source of truth for the pptx CONTENT (text, layout, colors).
  Re-running it regenerates `deck.pptx` from scratch and will SILENTLY DISCARD any manual
  edits Arif made directly in PowerPoint since the last generation.
- Arif DOES sometimes hand-edit `deck.pptx` directly for small wording tweaks (happened this
  session: he trimmed the title subtitle and added a bullet on slide 3 before asking for
  further changes). Before you re-run `build_deck.py` for a new change, DUMP the current
  pptx text first and diff it mentally against the script's hardcoded strings, so you fold
  his hand-edits into the script rather than reverting them. Quick dump recipe (avoid
  printing to the PowerShell console directly — Unicode ✓/✗ glyphs crash `cp1252` stdout,
  write to a UTF-8 file and Read it instead):
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
  Delete `lecture/_dump.txt` after use (scratch file, not a deliverable).
- Speaker notes (the spoken transcript) live in TWO places kept in sync: embedded in the
  pptx via `slide.notes_slide.notes_text_frame.text` (set from the `NOTES` dict in
  `build_deck.py`), AND mirrored in `lecture/transcript.md` as plain prose per slide, for
  Arif to read without opening PowerPoint. If you edit one, edit the other — `transcript.md`
  slide numbers must match the deck's actual slide order (they drifted once already this
  session when the architecture slide was inserted; re-numbered by hand, double check if you
  add/remove/reorder slides again).
- Visual style is intentionally identical to `lecture/build_flyer.py` (deep-navy `#0B1B33`
  background, teal `#2DD4BF` / amber `#F5B342` accents, `Segoe UI`, rounded-rectangle
  cards). `build_deck.py` duplicates the same helper functions (`solid`, `no_line`, `txt`,
  `card`, `circle`, `arrow_right`, etc.) rather than importing from `build_flyer.py` — keep
  them in sync by eye if the palette ever changes, there's no shared module.
- Preview mechanism (Windows, no LibreOffice on this host): export ALL slides at once via
  PowerPoint COM automation — much faster than one at a time:
  ```powershell
  $p = New-Object -ComObject PowerPoint.Application
  $pres = $p.Presentations.Open("<abs path to deck.pptx>", $true, $false, $false)
  $pres.Export("<abs output dir>", "PNG", 1600, 900)
  $pres.Close(); $p.Quit()
  ```
  This drops `Slide1.PNG` … `SlideN.PNG` into the output dir in one call — read them with
  the Read tool to sanity-check layout before handing back. Treat the output dir as scratch
  and delete it after (it was recreated and deleted twice this session; don't let it
  accumulate in `lecture/`).
- `python-pptx` is NOT preinstalled in any repo venv on this machine (checked this session —
  no `.venv` existed here despite an old note claiming one). Installed globally via
  `python -m pip install python-pptx`. If a fresh machine, install it before running
  `build_deck.py`.
- **Logo path correction:** the logo actually lives at
  `lecture/lecture_resources/logo-wimmera-white.png` (a subfolder), NOT at the repo root as
  an earlier version of this handover said and as the OLDER `build_flyer.py` hardcodes
  (`build_flyer.py` still points at a stale absolute path from a different machine/user
  profile — if you ever need to regenerate `flyer.pptx` again, fix that path first;
  `build_deck.py` already resolves it correctly via `os.path.dirname(__file__)`, relative,
  portable).

## 5. Time budget / what's actually left
- Rehearsal, not content, is Arif's real bottleneck (per his own admission — he's not
  nervous about the material, he's nervous about delivery). Once the deck wording is
  finalized, steer him toward reading it out loud 2–3 times rather than continuing to
  polish slides indefinitely.
- Still open from the original plan, not yet revisited: the deeper "query time" mental-model
  walkthrough (`lecture_project.md` §TODO, `lesson.md` has only Part A / ingestion done in
  full prose). Arif deferred this ("we will get back to getting intuitive understanding on
  it later") — do not assume it's needed before the lecture; it was explicitly deprioritized
  in favour of shipping slides + transcript under time pressure. Only resume it if Arif asks.
- Poster (external designer, from `design_brief.txt`) and its missing inputs (host logo,
  headshot, venue name, stream link/passcode, QR code, footer CRICOS/website, Wimmera
  co-branding decision) — still outstanding, untouched this session, see the original §6 of
  the prior version of this file if you need the full list again (also still in git history).

## 6. Convention
- Lecture materials live in `lecture/`; this handover in `.cursor/`. Git remote
  `git@wcma:arifwcma/induction.git`, branch `main` (Arif commits lecture work straight to
  main like the rest of this repo). Never commit secrets.
- `lecture/deck.pptx`, `lecture/transcript.md`, `lecture/build_deck.py` are all committed;
  keep them that way so a fresh pull has the live state.
