# Handover — Sydney Met Guest Lecture (ICT108)

For the next agent. This is a SEPARATE workstream from the product itself: Arif is
preparing tutoring material to explain THIS project (the induction chatbot) as a
real-world AI case study, to a university IT class. It is not a coding task. Read
`.cursor/instructions.md` for how Arif wants you to behave (brief, label replies
R1/R2…, one best option, no walls of text). This file holds only what is NOT in the
other `.cursor` docs.

## 1. The engagement
- Arif is a GUEST LECTURER for a 1-hour session in unit **ICT108** at **Sydney Met**
  (Sydney Metropolitan). He is delivering it in person + live-streamed.
- Fixed logistics (confirmed): **Tuesday 14 July 2026, 2:00–3:00 pm**, in person +
  live stream. Speaker line: **Dr Mohammad Arifur Rahman, Analyst Programmer,
  Wimmera CMA, Victoria.**
- Goal: explain a real AI project (this induction chatbot) at a conceptual level —
  the ideas and the real problems, NOT the code.

## 2. Hard constraints (Arif's, for this lecture)
1. **No office IP, no real code.** Explain the gist/ideas only. Never paste actual
   source, prompts, clause text, server details, or client specifics.
2. **Keep language accessible.** Say "PDF / documents", NOT "knowledge base / KB" —
   students find plain terms easier. Retain this level throughout.
3. **Written materials that get circulated are NEUTRAL, third-person descriptions**
   of the session — the hosting authority circulates them, so do NOT write in
   "you're invited / join us" voice, and do NOT address the audience directly.
4. **No em dashes** in the circulated writeups.
5. Avoid phrasing that sounds less-academic (e.g. Arif rejected "no heavy coding").

## 3. Audience & teaching pitch (agreed)
- **IT students with some coding**, new to AI/LLMs. Curiosity-driven, plain language.
- Embeddings are taught with the vector-arithmetic analogy: **queen − female + male ≈ king.**
- The whole lecture is **problem-driven**: build a document chatbot in ~5 steps, and at
  each step the naive system fails in an instructive way; the failure motivates the
  next concept. This arc is the spine of BOTH the flyer and the (still-to-build) deck.

## 4. The 5-step narrative arc (the spine) + where each maps in the real project
Use the project's real bugs/issues as the "and then it broke…" example at each step.
Sources: `.cursor/project.md`, `.cursor/blueprint.md`, `.cursor/handover.md`.

1. **Upload a PDF** — the lazy way (drop it into ChatGPT/Claude). Problem: needs a paid
   seat; does not scale to thousands of documents.
2. **Teach it meaning (embeddings)** — words → numbers; semantic similarity.
3. **Find the right passage (RAG)** — retrieve by meaning. Real problem = **Bug1**
   (lexical-match-over-relevance): a normal lunch-break question was answered from the
   emergency-only appendix because keywords matched. Fix = scope-aware retrieval /
   contextual chunking.
   - NOTE (framing subtlety, still unresolved): on the flyer the "grabbed the wrong
     rule" hint currently sits ON the RAG card, which can read as if RAG caused the
     error. Really it's the **2→3 transition**: naive vector match caused it, scope-aware
     RAG fixes it. Arif was offered "move the hint to step 2"; he had not confirmed when
     this handover was written. Raise it again if refining the flyer or building the deck.
4. **Know what it knows** — real problem = **Bug2** (false abstention on coverage/"how
   many"): the bot refused to answer a question it clearly had, because the verifier
   graded enumerated items against retrieved passages only. Fix = treat the document/
   topic MAP as authoritative for existence/coverage.
5. **Never make it up (grounding / reliability)** — hallucination: models answer
   confidently but wrong. Fix = grounded generation + a verifier that checks the answer
   against the source before it is shown, and calibrated abstention. Real supporting
   material: Issue#1 (emergency meal-break, verifier over-reach) in `.cursor/project.md`.

Concepts the lecture surfaces, in order: embeddings → retrieval/RAG → hallucination →
reliability.

## 5. Deliverables so far (all in `lecture/`)
1. **`flyer.pptx`** — a 1-page 16:9 teaser flyer (deep-navy "clean tech", teal + amber
   accents). Editable text boxes, the 5-step path as the centrepiece, 4 concept chips,
   Wimmera CMA logo top-right, footer with the fixed logistics. Built by:
2. **`build_flyer.py`** — the python-pptx script that generates `flyer.pptx`. Edit +
   re-run to change the flyer. (`python-pptx` is installed in `.venv`.)
3. **`writeup.txt`** — ~200-word neutral description of the session for the authority to
   circulate (students + stakeholders on live stream). Matches constraints in §2.
4. **`design_brief.txt`** — plain INFORMATION list (no design direction) for an external
   human designer preparing a portrait event POSTER modelled on the Sydney Met reference.

## 6. Still TODO / next tasks
1. **The main slide deck (Arif's primary ask, not yet started).** A SMALL pptx, "few
   slides, less text more graphics", walking the 5-step arc above to explain the project
   in the lecture. Same constraints (§2). Build it the same way (python-pptx script in
   `lecture/`, preview to verify — see §7). Ask Arif for a plan sign-off before spending
   a lot of tokens (he prefers to review the design plan first).
2. **Poster** is being made by an external designer from `design_brief.txt`. Arif still
   needs to supply: host-institution (Sydney Met) logo, his headshot, venue name, the
   Teams/live-stream link + Meeting ID + passcode, a QR code, footer provider/CRICOS +
   website, and whether to co-brand with the Wimmera CMA logo.
3. Decide the flyer Bug1 framing (§4 note).

## 7. Useful mechanics (host = Windows)
- **Preview a .pptx as an image** (no LibreOffice on this host): export slide 1 via the
  installed PowerPoint COM automation from PowerShell:
  `$p=New-Object -ComObject PowerPoint.Application; $pres=$p.Presentations.Open("<abs.pptx>",$true,$false,$false); $pres.Slides.Item(1).Export("<abs.png>","PNG",1600,900); $pres.Close(); $p.Quit()`
  then Read the PNG. (LibreOffice / `soffice` is NOT on the bare Windows host.)
- Logo file: **`logo-wimmera-white.png`** at the repo root — white "Wimmera CMA" version,
  meant for dark backgrounds (invisible on white).
- Reference poster Arif wants the designer to mimic:
  `C:\Users\m.rahman\Sydney Met_Industry Talk_APR 2026.jpg` (a Sydney Met industry-talk
  flyer: header + logo, speaker photo + blurb, 2×2 icon grid — When/Where, Who, Why,
  How-to-Join+QR — provider footer).

## 8. Convention
- Lecture materials live in `lecture/`; this handover in `.cursor/`. Git remote
  `git@wcma:arifwcma/induction.git`, branch `main` (Arif commits lecture work straight to
  main like the rest of this repo). Never commit secrets.
