# ICT108 Guest Lecture — Slide-by-Slide Transcript

Format: 45 min talk + 15 min Q&A. Case study throughout: **MetMate**, a stand-in
chatbot answering Sydney Met student questions about university rules. The arc:
three build phases, each broken by a real failure and fixed by the next idea.
Minute marks are a rehearsal budget, not a script timer. The same text is
embedded as speaker notes in `deck.pptx`.

---

## Slide 1 — Title (~2 min)
Good afternoon everyone, thanks for having me. I'm Arif, Analyst Programmer at
Wimmera CMA in regional Victoria — my day job is building software and mapping
systems for a natural-resource agency. Over the past year I've built several
AI-powered tools for my organisation, but only a handful ended up genuinely
used to solve a real problem — the rest were experiments. One that's in real
daily use is a chatbot, and today I'll walk you through what it actually takes
to build one properly, using the real problems I ran into along the way. Since
I can't share my workplace's internal documents publicly, we'll use a stand-in
case study: MetMate, an imaginary chatbot for Sydney Met itself, answering
student questions about enrolment, library, and exam rules. Same ideas,
public-friendly example. One promise before we start: this lecture stays at
the level of concepts, so I'll use technical terminology sparingly and
carefully. New terms appear in this field literally every day; nobody
memorises them all. If a term flies past you today, don't worry — the
important ones keep coming back, you can always look them up later, and you'll
be able to follow the ideas either way.

## Slide 2 — Why not just upload it to ChatGPT? (~3 min)
So, a chatbot that answers student questions from the university's documents.
Let's start with the laziest possible version: take an existing product like
ChatGPT, upload the student handbook PDF, and start asking questions. And
honestly — it works. For one document, one person, one paid seat. But look at
what that means for an institution. To give this to every student, Sydney Met
would either have to build its own ChatGPT-like product from scratch, or buy a
paid subscription seat for every single student — and either way, the
documents keep changing and thousands of students ask questions at the same
time. Neither option scales. What we need is one shared bot, always current,
serving everyone at once. That's the real engineering problem, and it starts
here.

## Slide 3 — Why not any ready-made chatbot? (~4 min)
A fair question before we build: chatbots are everywhere now, so why not grab
a ready-made one, the way we grab Chrome for browsing? Nobody builds their own
browser. Four reasons this is different, at least today. First, expectations
are genuinely diversified — one organisation cares most about security and
where its data lives, another about raw speed, another about cost, another
about reliability under heavy use. A browser mostly just needs to render a
page; a chatbot's bar depends entirely on who's asking. Second, this field is
comparatively new, so common expectations aren't even well defined yet —
there's no agreed checklist like there is for browsers. Third, "no-code"
chatbot builders exist that promise exactly this, but in my own experience
they're more complicated to use well than they claim, and how far you can
customise the behaviour is limited. Fourth — and I say this half-joking — this
space moves so fast that a genuinely good ready-made bot might exist by the
time we finish this lecture; when I checked before preparing this, it wasn't
there yet. So for now, you still have to build, or at least understand the
build well enough to steer it. And beyond these four there's a deeper reason
you'll see by the end of the hour: every domain has specific needs that no
generic product anticipates. Hold that thought — we'll come back to it in the
very last slide.

## Slide 4 — MetMate at a glance (~4.5 min)
Here's the whole of MetMate at a glance — deliberately coarse, just a handful
of boxes. The top lane happens once, ahead of time, before any student asks
anything: the documents get broken up and organised into an index, a
searchable form. The bottom lane runs live, every single time a student asks:
the question searches that index, the best passages feed a draft answer, the
draft gets checked, and only then does the student see a reply. Keep this map
in your head — the rest of the lecture is a magnifying glass moving across it,
one box at a time. Three things worth saying while we look at it. First: a
chatbot is usually the very first exercise in any course on large language
models — LLMs, the AI models behind tools like ChatGPT — because the task is
well defined, and with decent hardware you can build a complete chatbot
running entirely on your own machine with free local models. Second: this is a
young, still-growing field, so there is no standard blueprint for this
diagram. What you're seeing is one way — the way we built it. Third — and this
is where real life differs from the course exercise: real users expect quality
answers, fast, at any scale, without the organisation running a data centre.
So this system quietly calls three commercial AI services over the internet —
three API providers. OpenAI turns text into its searchable meaning form and
handles the fast mechanical chores, Anthropic writes the final answers, and
Cohere re-orders search results by relevance. You pay per use, and in exchange
nobody has to own a single GPU.

## Slide 5 — Phase 1: just match the words (~3 min)
Let's build phase one, the bare minimum. Almost everything in the map is
standard software; the only genuinely new problem is the search box — given a
question and thousands of passages, find the few that matter. The simplest
possible answer: match words. Count how many words the question shares with
each passage, give rare words a bit more weight, and the passage with the most
overlap wins. This is decades-old search technology — it's fast, it's simple,
it needs no AI at all. The winning passages then go to the language model,
which phrases a reply out of them. And that's phase one complete: a working
chatbot. Now watch it fail.

## Slide 6 — Phase 1 breaks: right words, wrong rule (~4 min)
A student asks: "Can I access the library 24/7?" Somewhere in the documents
there's an appendix about exam periods, and it literally contains the words
"24/7 access". The general rule — the one that actually governs an ordinary
week — says open 8am to 10pm during term time, and it shares almost no words
with the question. Count the overlap: the appendix scores high, the real rule
scores low, and MetMate confidently tells the student the library never
closes. Every word of that answer came from a real document — and it's still
wrong, because word matching rewards the passage that echoes the question, not
the rule that applies. This is the single most important failure mode of naive
search, and the first version of my real bot did exactly this. A confident
wrong answer is worse than no answer, so phase one is dead. Notice that two
things broke at once: search matched words instead of meaning, and nothing
anywhere asked "does this rule even apply right now?" Phase two fixes both.

## Slide 7 — Phase 2: search by meaning (~5 min)
First half of the fix: teach the computer meaning. That's what an embedding
does — it converts a piece of text into a list of numbers. Think of it as
plotting the text as a point in space, where meaning determines position:
texts about similar things land near each other, even if they share no words
at all. The classic illustration: take the point for "queen", subtract the
direction for "female", add the direction for "male", and you land close to
"king". The model captured a real relationship purely from patterns in
language, as geometry. So during the build-once lane, every passage of every
document becomes a point; live, the student's question becomes a point too,
and search stops being "count the shared words" and becomes "find the nearby
points". A passage about opening hours now lands right next to a question
about opening hours, even when the wording is completely different. That's
half the fix.

## Slide 8 — Phase 2: say when each rule applies (~4 min)
Here's the second half, and it's the subtler one. Even searching by meaning,
the exam-period passage still comes up — it genuinely is about library access.
The missing ingredient is context: when each passage is stored, attach the
conditions under which it applies — "exam period only", "term time", whatever
the surrounding document says. Now the pieces the bot retrieves aren't bare
sentences; they're sentences that carry their own scope, and a simple check
can set aside the ones whose conditions don't hold for this question. Ask
about ordinary library hours and the appendix steps back: 8am to 10pm in term
time, 24/7 only during exams. Phase two, MetMate answers the library question
correctly. This idea — every piece of information carrying the context of when
it's true — is probably the most transferable lesson in this whole lecture.

## Slide 9 — Phase 3: it refuses what it knows (~4 min)
Phase two works, so we got ambitious. A chatbot speaking to students on behalf
of a university must not invent things — language models will happily produce
fluent, confident, wrong sentences. So we added a safety check: before any
answer is shown, a second pass verifies every claim against the passages that
search retrieved, and unsupported claims kill the answer. Sensible, right?
Here's what happened. A student asks: "How many kinds of special consideration
are there?" MetMate drafts the correct answer — six categories — because
alongside the index it keeps a master list, a table of contents of every rule
section, built directly from the documents. But search, tuned to fetch a
handful of relevant passages, only pulled the full text for two of the six.
The checker finds four claims with no passage in hand, stamps them
"unsupported", and throws the whole answer away. The bot tells the student "I
couldn't confidently find this" — on a question it demonstrably could answer.
Too shy is a real failure too.

## Slide 10 — Phase 3: the right evidence per claim (~4 min)
The fix is not to loosen the check — it's to give it the right evidence for
each kind of claim. Claims about what exists, or how many there are: the
master list is the authority. It was built directly from the documents
themselves, so it's exactly as trustworthy as they are. Claims about the
detail of one specific rule: those still require the actual passage, no
exceptions. Existence and detail need different evidence — miss that
distinction and your bot goes shy on precisely the questions it's best
equipped to answer. And when a claim genuinely has neither kind of evidence?
The bot doesn't guess. It quietly searches once more with a sharper query, and
if the support still isn't there, it tells the student honestly that it
doesn't know. That's the whole honesty policy in one breath: never show an
unchecked answer, never refuse what you can prove, and when you truly can't —
say so. Phase three complete, and this is the version people can rely on.

## Slide 11 — The whole system, built by its failures (~3 min)
Now zoom back out — same map as the start, but grown. The grey boxes are phase
one, the bare skeleton: split the documents, match, draft, reply. The teal
boxes are phase two: the meaning index, the applicability labels, the filter
that keeps only rules that apply right now. The amber boxes are phase three:
the master list, the claim checker, the retry, and the honest "I don't know".
Here's the point of this slide: nothing in this picture was designed up front.
Every coloured box exists because a real failure forced it. Which means you
don't need the perfect architecture on day one — you need a working skeleton,
and the discipline to treat every failure as a design instruction.

## Slide 12 — What we skipped (~1.5 min)
Remember the promise from slide one — that terms keep coming back? Here are
six I deliberately skipped today, all quietly at work in the real system.
Hybrid retrieval: run word search and meaning search together and merge the
results — old and new search are better combined than either alone. Reranking:
a second, smarter pass re-orders the passages search found. Query rewriting:
clean the student's question into a sharp search query before searching.
Question splitting: one compound question becomes several simple ones,
answered together. Conversation memory: condense the chat so far into one
standalone question, so "what about postgrads?" makes sense on its own. And
the two-model design: a cheap, fast model does all this mechanical plumbing,
while the strong, expensive model only writes the final answer — that's how
the system stays both smart and affordable. None of these changes the story
you just saw; they squeeze out the last twenty percent of quality. When you
need them, look them up — you now have the map they attach to.

## Slide 13 — Make it fit the domain (~3 min)
Last thing — back to the thought I asked you to hold at the start: why
ready-made bots don't quite fit. Everything we built today is the generic
recipe, and the recipe is public — anyone can follow it. The value, and
honestly the fun, is fitting it to a domain. Three quick examples from the
kinds of tools I get to build. A GIS assistant — mapping is my own field —
shouldn't just answer questions about map data; it should know what the user
is looking at right now: which layers are on, where they've zoomed, what they
just clicked. A weather assistant can't only quote documents, because
documents describe the past — its whole job is the future, so forecasting has
to live inside it. A finance assistant sits on data that moves all day, so in
its idle time it should be analysing what just changed and preparing the
answers people are about to ask. Same skeleton, three completely different
bots. Somewhere in whatever field you end up working in, there's a version of
this waiting to be fitted — and that part isn't in any tutorial. That part is
yours. Thank you — happy to take questions.
