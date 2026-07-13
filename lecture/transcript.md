# ICT108 Guest Lecture — Slide-by-Slide Transcript Plan

Case study used throughout: **MetMate**, a stand-in chatbot answering Sydney Met
student questions about university rules. Full text is also embedded as speaker
notes in `deck.pptx`.

---

## Slide 1 — Title
Good afternoon everyone, thanks for having me. I'm Arif, Analyst Programmer at
Wimmera CMA in regional Victoria. Over the past year I've built several
AI-powered tools for my organisation, but only a handful of them ended up
genuinely used to solve a real problem — the rest were experiments. One that's
in real daily use is a chatbot. Today I want to walk you through what it
actually takes to build one properly, using the real problems I ran into along
the way. Since I can't share my workplace's internal documents publicly, we'll
use a stand-in case study: imagine a chatbot for Sydney Met itself, answering
student questions about enrolment, library, and exam rules. Let's call it
MetMate. Same ideas, public-friendly example.

## Slide 2 — Why not just use an existing chatbot?
Before we build anything, a fair question: chatbots are common now, so why
doesn't everyone just grab one off the shelf, the way we grab Chrome for
browsing? Nobody builds their own browser. Four reasons this is different, at
least today.

1. Expectations are actually diversified — one organisation cares most about
   security and data residency, another about raw speed, another about cost,
   another about reliability under heavy use. A browser mostly just needs to
   render a page; a chatbot's bar depends entirely on who's asking.
2. This field is comparatively new, so common expectations aren't even well
   defined yet — there's no agreed checklist like there is for browsers.
3. "No-code" chatbot builders exist that promise exactly this, but in my own
   experience they're more complicated to use well than they claim, and how far
   you can customise the behaviour is limited.
4. This space moves so fast that a genuinely good ready-made bot might exist by
   the time we finish this lecture — but when I checked before preparing this,
   it wasn't there yet.

So for now, if you want a chatbot that fits your exact constraints, you still
have to build one, or at least understand how it's built well enough to steer
it.

## Slide 3 — Step 1: Upload it to ChatGPT
So let's build MetMate from scratch, and at every step we'll do the lazy
obvious thing first, watch it break, and let that break motivate the next idea.
Step one: the laziest possible chatbot. Take an existing product like ChatGPT,
upload the student handbook PDF, and start asking it questions. It genuinely
works, for one document, one person, one paid seat. But look at what "just use
ChatGPT" actually means for an institution: to give this to every student,
Sydney Met would either have to build its own ChatGPT-like product from
scratch, or buy a paid subscription seat for every single student — and either
way, the documents keep changing and thousands of students need answers at the
same time. Neither option scales. We need something that serves everyone at
once, from one shared, always-current source of truth. That's the real
engineering problem starting here.

## Slide 4 — The big picture (architecture overview)
Before we zoom into each concept one at a time, here's the full picture of
what we're actually going to build, so you have a map to place each piece on
as we go. Two halves. The top half happens once, ahead of time, before any
student asks anything: every document gets broken up and organised into an
index built around meaning, not exact words — that's what step two is about.
The bottom half happens every single time a student asks a question, live: the
question searches that index, pulls out a draft answer, and — this is the part
that took the most work — checks that draft against the real source before
it's ever shown to the student. Steps three, four, and five are really just
zooming into different parts of that second row: how search finds the right
passage, and how the system checks and knows what it does and doesn't actually
know before it speaks. Keep this picture in your head; everything from here is
detail on one box of it.

## Slide 5 — Step 2: Teach it meaning (embeddings)
To search across many documents automatically, the computer needs to
understand what a question and a passage MEAN, not just whether the words
match exactly. That's what an embedding does: it converts a piece of text into
a list of numbers — think of it as plotting the text as a point in space, where
meaning determines position. Texts about similar things land near each other,
even without sharing any words. The classic illustration: take the point for
"queen", subtract the direction for "female", add the direction for "male", and
you land close to "king". The model captured a real relationship purely from
patterns in language, as geometry. Once every chunk of every document is turned
into one of these points, and the student's question is turned into a point
too, finding a relevant passage becomes: find the nearby points. That's the
foundation everything else sits on.

## Slide 6 — Step 3: Find the right passage (RAG) — and it breaks
Now search actually works: a student asks "can I access the library 24/7?" and
the system finds the passage that mentions "24/7" access most closely. But
here's the trap: that passage only exists in a rule for exam period, buried in
an appendix — the general everyday rule says the library is open 8am to 10pm,
term time. Because the exam-period rule contains the exact phrase the question
echoes, it gets pulled up and answered as if it always applies — a confident,
wrong answer, sourced from a real document, based purely on words matching
rather than whether that rule actually governs right now. This is the single
most important failure mode of naive AI search: matching on keywords instead of
relevance or scope. The fix is to make sure every retrieved passage carries the
context of WHEN it applies — attach that condition directly to the passage when
it's stored, so retrieval and the model both see it, not just the raw sentence.
Get this wrong and your chatbot confidently tells students the wrong thing,
which is almost worse than not answering at all.

## Slide 7 — Step 4: Know what it knows — and it breaks
Good, MetMate now avoids the wrong-rule trap. But a new failure shows up: a
student asks "how many kinds of special consideration are there for exams?"
MetMate correctly lists them all — say six categories — because it has a
master index, a table of contents of every rule section, and that index
genuinely lists six. But then a safety check kicks in: a second pass verifies
every claim against the actual passages retrieved for search. That check only
had snippets for two of the six categories in hand, so it marks the other four
"unsupported" and throws the whole answer away — the bot tells the student "I
couldn't confidently find this", on a question it clearly could answer. The fix
is to give that safety check two different sources of truth: use the master
index as the authority for what EXISTS or how many there are, since it's built
directly from the real documents, but still require an actual retrieved passage
before trusting any DETAIL about one specific category. Existence and detail
need different evidence. Miss that distinction and your bot becomes needlessly
shy on exactly the questions it's best equipped to answer.

## Slide 8 — Step 5: Never make it up
Put steps three and four together and you get the real design principle behind
a trustworthy chatbot: never let it show an answer it hasn't checked against
the source first. Every draft answer goes through a verifier before the
student ever sees it — did every claim actually come from a real, applicable
rule? If yes, show it. If a claim doesn't check out, don't show it anyway — try
again, maybe search once more with a refined question, and only if it genuinely
still can't find solid grounding, tell the student honestly that it doesn't
know, rather than guessing. That's the difference between a chatbot that
sounds confident and one you can actually rely on. Confidence and correctness
are not the same thing for a language model — it will happily generate a
fluent, wrong answer unless you build a mechanism that catches it before
publishing. This calibrated honesty — answer only when genuinely grounded,
admit it when not — is really the whole reliability story in one sentence.

## Slide 9 — Closing recap + Q&A
So, five steps, five instructive failures: uploading one PDF doesn't scale; raw
keyword-ish search grabs confident wrong rules; a verifier without the right
authority becomes needlessly shy; and the fix running through both is the same
idea — give every piece of information the CONTEXT it needs, whether that's
when a rule applies, or what actually counts as evidence. That's what took this
project from a demo to something people actually rely on daily. Happy to take
questions, on any of these five steps, or anything else about how AI systems
like this get built in practice.
