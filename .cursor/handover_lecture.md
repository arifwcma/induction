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
- **Deadline: lecture is TODAY, Tue 14 July 2026, 2:00–3:00 pm.** 45 min talk + 15 min
  Q&A. It is now ~10:40 am — roughly 3 hours left. Steer everything toward rehearsal;
  only make edits Arif explicitly asks for.
- **The deck was rebuilt from scratch this morning (~10:00–10:30 am), on Arif's
  explicit instruction.** He rejected the Mon-night 13-slide deck as "complicated for
  general IT audience, not flowing well, too much for one session, not much take away"
  and dictated a new 5-phase structure himself (fundamentals, StatQuest-style
  jargon-in-context, embeddings as THE takeaway). The old deck is in git (commit
  `c0c021f`) if ever needed. The live artefacts are:
  - `lecture/deck.pptx` — 17 slides, 5-phase fundamentals narrative (see §4).
  - `lecture/transcript.md` — speaker prose, one section per slide, minute marks with
    running totals, sums to exactly 45.
  - `lecture/build_deck.py` — the generator. Source of truth for pptx content.
- **Arif committed the rebuild himself at 10:38 am (`ffd0bb6`), then HAND-EDITED
  `deck.pptx` in PowerPoint during review:** removed the "GUEST LECTURE · ICT108 ·
  SYDNEY MET" eyebrow, the MetMate subtitle line, the promise card and the phase strip
  from the title slide, and removed the "ICT108 · MetMate case study" text from every
  footer. These edits were detected via a text-dump diff and FOLDED INTO
  `build_deck.py` (verified: script output now textually identical to on-disk pptx).
  Everything committed + pushed ~10:45 am together with this handover. He gave no
  other feedback on the deck yet. NOTE: `deck.pptx` may still be OPEN in PowerPoint
  (`~$deck.pptx` lock file present, untracked — leave it alone); don't regenerate
  while it's open.
- **`notes.txt` (repo root) GREW during his review (~10:30–10:40 am) — the NEW lines
  are UNPROCESSED.** The file has two parts separated by `===`:
  - BELOW the `===` = Monday-night jottings, already absorbed into the redesign
    ("king queen" → slide 13, "ollama - local" → slide 4, "embedding not ai" → slides
    6/15, "terminologies" → term chips, "why not off the shelf" → phase 1).
  - ABOVE the `===` = NEW Tue-morning jottings. Verbatim gist: "weight-training is not
    everything — for chatbot we don't retrain weights, rather make it capable on
    understanding documents" (flagged by Arif himself as 'if possible and not
    distraction' — likely a fine-tuning-vs-RAG remark, candidate for slide 15 or a
    spoken aside); "full non ai / mix - why"; "chatgpt upload - hundreds subscription";
    "chatbot api - full doc + question (non ai ai - diff color) - photo"; "rag";
    "bm25 - prob, semantic - cut"; "hierarchical - still semantic"; "embedding - embed
    models - token". NOTE: most of these mirror the new deck's slide order, so they may
    be his REHEARSAL outline / talking points rather than change requests — but "photo"
    and "diff color" might be visual asks. DO NOT guess-implement. Ask him to walk
    through the new lines one by one: edit, talking point, or already covered.
- **`boyan.txt` (repo root, new, untracked-until-this-push) reads: "Intro /
  terminologies / MetMate".** Purpose unknown — possibly his opening-minutes outline,
  possibly notes for a person (Boyan?). Ask, don't assume.
- **What's left, in order:** walk through new `notes.txt` lines with Arif → any final
  wording tweaks → REHEARSAL (the real bottleneck, §6).

## 1. The engagement (fixed facts)
- Arif is a GUEST LECTURER for unit **ICT108** at **Sydney Met** (Sydney Metropolitan).
  In person + live-streamed. Tue 14 July 2026, 2:00–3:00 pm.
- Speaker line: **Dr Mohammad Arifur Rahman, Analyst Programmer, Wimmera CMA, Victoria.**
- Goal (REVISED Tue morning): fundamentals of how a document chatbot works, built from
  basics with intuition; jargon defined in context as the story needs it (Arif's model:
  Josh Starmer / StatQuest). Show that much of an "AI system" is NOT AI. Reduced text,
  concrete toy examples throughout.
- **The single takeaway Arif wants: EMBEDDINGS.** His words: "if you want to take away
  only one thing from this lecture, I would be very glad if it is embedding." The
  embedding block (slides 11–14) is the heart — never compress it.
- **Emotional context (still matters):** first-ever hour-long lecture; nervous; candidly
  says the project was mostly built by Claude and he doesn't have strict end-to-end
  command of it. The real lever is delivery confidence via rehearsal. Reassure with
  facts, don't patronise.

## 2. The case study identity (stable — keep consistent)
Arif cannot use the real induction bot publicly (office IP), so everything runs on an
invented but structurally identical stand-in:
- **Name: MetMate** — a chatbot answering Sydney Met student questions about university
  rules (enrolment, library, exams).
- Invented example set, reused across slides — keep EXACTLY consistent:
  - **Library hours (Bug1 stand-in):** general rule = "8am–10pm on term days"; "Exam
    Period Appendix" = 24/7 access, exam period only. Keyword search ranks the appendix
    top for a "24/7" question in week 3 of term → confident wrong answer.
  - **Embedding toy (Arif's own design, Tue morning):** enrolment 5, registration 6,
    withdrawal −5 on one number line; then 2-D vectors enrolment [5,0], registration
    [6,0], withdrawal [−5,0], pass [0,5], fail [0,−5], course [2.5,2.5] (reuses axes, no
    new dimension). Production models ~300–3,000 dims.
  - **Semantic-search payoff:** question "How do I fix a mistake in my registration?"
    finds chunk "Enrolment corrections must be lodged before census" — zero shared
    words. (Deliberately does NOT use withdrawal as the payoff: in the toy geometry
    withdrawal is far from registration.)
  - The Bug2 / special-consideration / verifier story was CUT from the lecture in this
    redesign (too much for one session). Verification survives only as a one-line chip
    on slide 16. Don't resurrect without Arif asking.
- Real bug specifics live in the product-side `.cursor` docs; never leak real details
  into lecture materials.

## 3. Hard constraints (Arif's, non-negotiable)
1. No office IP: no real code/prompts/clause text/server/client specifics — gist only.
2. Plain language, BUT (revised Tue morning) technical terms ARE introduced — one at a
   time, in context, StatQuest-style, each in a teal "term chip". Terms now in the deck:
   KB, API, prompt, context, deterministic/non-deterministic, chunk, keyword search
   (BM25), lexical vs semantic, embedding, vector, dimension, representation learning,
   cosine similarity, RAG.
3. Circulated written materials (writeup, poster brief) are NEUTRAL third-person, no em
   dashes. Deck + transcript are internal working material — direct voice is fine.
4. Avoid phrasing that reads as less-academic.
5. Cosmetics (Arif, Tue morning): NO date/time on title slide; Wimmera logo top-right on
   ALL slides; name + designation bottom-right on ALL slides (footer).

## 4. The deck — 17 slides, 5-phase narrative (rebuilt Tue 14 July morning)
The spine: start from "upload a PDF to ChatGPT", let each phase break for a real reason,
and let the failure force the next idea. One concrete picture (the pipeline) grows
visibly across phases. RAG is NAMED ONLY AT THE END (slide 15) after the audience has
already built it — the payoff pattern.

Phase names: 1 "Just ask ChatGPT" · 2 "Our own bot" · 3 "Search first" ·
4 "Search by meaning" · 5 "Toward the real world".

Slide list (exact titles · minute mark · running total):
1. **Talk to Your Documents** (1' · 1) — title, MetMate framing, concepts-over-terminology
   promise card, phase strip at bottom.
2. **Upload a PDF, ask a question** (2' · 3) — ChatGPT UI mock → under the hood: ONE big
   string (document + question) → model. Text-only disclaimer.
3. **Why this doesn't scale** (2.5' · 5.5) — 3 problems (ChatGPT's product / seat per
   student / many evolving documents). First term chip: KB. "So we build."
4. **Our own bot — same trick, our pipes** (2.5' · 8) — browser → our server → OpenAI
   API; same big string through pipes. Term chip: API (ChatGPT=product, OpenAI=company).
   Ollama/local-model aside. "Rest of talk: OpenAI API."
5. **What the model actually receives** (2.5' · 10.5) — the Context/Question/Answer
   prompt template, big monospace card. Term chips: prompt, context. "If the fact isn't
   in the prompt, the model can only guess."
6. **How much of this is actually AI?** (3' · 13.5) — pipeline with teal frame around
   browser/server/glue ("ORDINARY CODE — deterministic") and amber frame around model
   ("AI — non-deterministic"). Term chips: deterministic, non-deterministic. Punchline:
   an AI system is mostly NOT AI.
7. **One question, two million words** (2.5' · 16) — phase 2 breaks: 300 PDFs ≈ 2M words
   → ALL sent per question → ~1 minute per answer (Arif's REAL first bot did this).
   Magic-box disclaimer card (we don't open the model today). "Send LESS → Phase 3."
8. **Send less: pick the right pieces** (3' · 19) — pipeline grows: split into chunks →
   pick top 5 → smaller prompt. Term chip: chunk. Amber card: "this choosing step is
   YOUR craft" (retrieval is the developer's skill, the model is not our department).
9. **Finding the pieces — no AI needed** (3.5' · 22.5) — the KB as a stored table of
   chunks; query "library opening hours" scored by shared words: A=3 wins, B=0, C=1.
   Term chip: keyword search (BM25). "Works surprisingly well… usually right."
10. **Right words, wrong rule** (3.5' · 26) — Bug1: week 3 of term, "Can I access the
    library 24/7?" → appendix shares 3 words, wins ✗; general rule shares 1, left
    behind. Quieter failure: enrolment vs registration = synonyms invisible. Terms:
    lexical vs SEMANTIC matching → phase 4.
11. **Math with words** (3' · 29) — number line: withdrawal −5, enrolment 5,
    registration 6. Term chip: embedding. Amber takeaway card ("take ONE thing home").
    Hook: where does "pass" go? One number isn't enough.
12. **One number isn't enough — vectors** (4' · 33) — 2-D plane, all six toy words
    plotted; course [2.5, 2.5] ringed (no new axis needed). Term chips: vector,
    dimension. Production: ~300–3,000 dims. "Distance IS similarity."
13. **Who assigns the numbers?** (2.5' · 35.5) — learned, not hand-typed: masked-word
    game ("Students must ___ before the census date" → enrol 62%, register 31%, party
    0.1%). Term chip: representation learning + king−man+woman≈queen as look-up-later.
14. **MetMate searches by meaning** (3.5' · 39) — stored KB = chunk + vector table;
    question → vector → nearest chunks. Term chip: similarity (cosine). Worked example:
    "fix a mistake in my registration" → "Enrolment corrections…" (zero shared words ✓).
    Library trap resolved: both library chunks retrieved, model answers with condition.
15. **The whole picture — you built RAG** (3' · 42) — full two-lane pipeline colour-coded
    by phase (grey=phase 2 skeleton, teal=phase 3 chunks/search, amber=phase 4 vectors);
    RETRIEVAL/AUGMENTED/GENERATION brackets; "the only AI box" badge on the model (even
    embeddings, once trained, are deterministic — Arif's "embedding not ai" point);
    "one way, not the standard way" footnote lives in the notes.
16. **What real chatbots add** (1.5' · 43.5) — six one-line chips: hierarchical
    chunking, context-aware chunking, hybrid search, reranking, conversation memory,
    verification. Overflow buffer: steal time from THIS slide if running late.
17. **Three things to take home** (1.5' · 45) — (1) AI product ≈ mostly ordinary
    software; (2) embeddings (THE one); (3) RAG. "Recipe is public — fitting it to your
    domain is yours." Thank you / questions.

## 5. Build workflow (important — avoid losing Arif's edits)
- `lecture/build_deck.py` is the source of truth for pptx CONTENT. Re-running it
  regenerates `deck.pptx` from scratch and SILENTLY DISCARDS any manual edits Arif made
  in PowerPoint since the last generation.
- Arif DOES sometimes hand-edit `deck.pptx` directly for small wording tweaks. Before
  re-running `build_deck.py`, ALWAYS dump the current pptx text and diff it against the
  script's strings, folding his hand-edits into the script. Dump recipe — do NOT print
  to the PowerShell console, Unicode ✓/✗ glyphs crash `cp1252` stdout; write a UTF-8
  file and Read it:
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
  (embedded into the pptx via `notes_slide`, each entry starts with its "[~N min]"
  mark) AND `lecture/transcript.md`. Edit one → edit the other. Minute marks must keep
  summing to 45.
- Visual style: deep-navy `#0B1B33` bg, teal `#2DD4BF` (terms/success), amber `#F5B342`
  (emphasis/takeaway), red `#E06C6C` (failures), `Segoe UI` + `Consolas` for prompt/
  vector text, rounded-rect cards. Helpers: `solid`, `no_line`, `txt`, `card`, `frame`,
  `circle`, `centered_label`, `arrow_right`, `straight_line`, `add_logo`, `add_footer`,
  `failure_chip`, `term_chip`, `flow_box`, `flow_row`. The TERM CHIP (teal border,
  bold teal term + muted definition) is the jargon-in-context device — reuse it for any
  new term.
- Preview mechanism (Windows host, no LibreOffice): export ALL slides at once via
  PowerPoint COM automation, then Read the PNGs:
  ```powershell
  $p = New-Object -ComObject PowerPoint.Application
  $pres = $p.Presentations.Open("<abs path to deck.pptx>", $true, $false, $false)
  $pres.Export("<abs output dir>", "PNG", 1600, 900)
  $pres.Close(); $p.Quit()
  ```
  Treat the output dir as scratch and delete it after. Works, used Tue 14 July.
- `python-pptx`: install globally with `python -m pip install python-pptx`. Had to be
  REINSTALLED Tue morning (system Python changed to 3.13) — check before assuming.
- Logo lives at `lecture/lecture_resources/logo-wimmera-white.png`. `build_deck.py`
  resolves it relative to its own file — portable. The OLDER `build_flyer.py` still
  hardcodes a stale absolute path from another machine; fix that first if you ever
  regenerate `flyer.pptx`.

## 6. What's actually left / how to steer
1. **Process the NEW `notes.txt` lines with Arif** (see §0) — line by line, each
   becomes an edit, a talking point, or "already covered". Keep the embedding block
   (11–14) intact; keep toy numbers consistent (§2).
2. **Rehearsal is the real bottleneck** (his own admission) and there are only ~3 hours
   left. Push him to read `transcript.md` aloud 2–3 full passes against the clock
   rather than polishing slides. The transcript carries running totals so he can check
   the clock mid-talk. If he overruns, steal from slide 16 — never from 11–14.
3. Everything is committed and pushed as of Tue ~10:45 am. If further edits happen,
   commit + push again before he leaves — he may present from a different machine.
4. Poster (external designer, from `design_brief.txt`) — outstanding for two sessions,
   lecture is today; almost certainly dead. Ask before spending any time.
5. Dead: the deep "query time" walkthrough (`lecture_project.md` TODO, `lesson.md`
   Part A), the Mon-night 13-slide deck structure, and the Bug2/verifier lecture story.
   `lecture_project.md` and `lesson.md` are STALE; THIS file is the live plan.

## 7. Conventions
- Lecture materials live in `lecture/`; this handover in `.cursor/`. Git remote
  `git@wcma:arifwcma/induction.git`, branch `main`. Never commit secrets.
- `lecture/deck.pptx`, `lecture/transcript.md`, `lecture/build_deck.py` are tracked —
  keep them committed so a fresh pull has the live state.
- Responses to Arif: labelled R1/R2/…, brief, one best option, numbered lists, invite
  elaboration instead of dumping it.
