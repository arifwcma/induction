# MetMate lecture — speaker transcript

ICT108 guest lecture · Tue 14 July 2026, 2:00–3:00 pm · 45 min talk + 15 min Q&A.
One section per slide. The minute mark is a budget, not a stopwatch — if a slide runs
over, steal from slide 16, never from slides 11–14 (the embedding block).

Running total is shown at each slide so you can check the clock mid-talk.

---

## Slide 1 — Title: Talk to Your Documents  (~1 min, total 1)

Good afternoon everyone, thank you for having me. I'm Arif — Analyst Programmer at
Wimmera CMA in regional Victoria. My day job is building software and mapping systems,
and over the last year I have built several AI tools for my organisation. One of them is
a chatbot that answers questions from official documents, and it is in real daily use.

Today I will show you how such a chatbot really works — by building one from zero, in
five phases. Each phase will hit a real problem, and the problem will force the next
idea.

I can't show my workplace's internal system, so we will use a stand-in: MetMate, an
invented chatbot for Sydney Met itself, answering student questions about enrolment, the
library, and exams. Same ideas, public-friendly example.

One promise before we start: concepts over terminology. Every technical term will arrive
only when the story needs it, and I will define it in plain English when it does.
Nothing to memorise up front — and everything can be looked up later.

---

## Slide 2 — Phase 1: Upload a PDF, ask a question  (~2 min, total 3)

Phase one. The simplest possible way to talk to your documents — and it needs no code at
all. Open ChatGPT, attach the student handbook PDF, type your question. Done.

What happens under the hood? For text, you can imagine it very simply: the full text of
the document and your question are glued together into ONE long piece of text, and the
model reads all of it and writes an answer. That's the picture — one big string of text.
Keep it in your head, because the whole lecture is about improving this one picture.

Two small notes. First, today we care about text only — what happens with images or
complex files is a story for another day. Second, and honestly: this works. If you are
one person with one document, this is genuinely the right solution, and my honest advice
is: just do this. The rest of this lecture exists because a university is not one
person.

---

## Slide 3 — Phase 1: Why this doesn't scale  (~2.5 min, total 5.5)

So why can't Sydney Met just tell 30,000 students "go upload the handbook to ChatGPT"?
Three problems.

One — ChatGPT is somebody else's product. We can't put ChatGPT itself on the university
website; to offer that experience ourselves we would have to build our own ChatGPT-like
product, which is a huge job.

Two — the alternative is that every student needs their own paid subscription. Thousands
of seats, just to ask about the handbook.

Three — and this is the quiet killer — a real answer often needs several documents at
once: the handbook, the library rules, the exam procedures. And these documents evolve;
they change through the year. Expecting every student to re-upload the right, current
pile of PDFs into every private chat, every time — that will simply never happen.

Now our first technical term of the day. That pile of official documents the bot must
answer from has a name: the Knowledge Base — the KB. And notice the teal box on the
slide — every time you see a box like that today, it means a new term just entered our
story, defined in plain English, ready to be looked up later.

So here is what we actually want: ONE bot, OUR OWN, sitting on the university website,
always reading the CURRENT documents. That means we build. Phase two.

---

## Slide 4 — Phase 2: Our own bot — same trick, our pipes  (~2.5 min, total 8)

Phase two: our own bot, the smallest one possible. Three pieces. A web page with a chat
box — ordinary web development, many of you can build this already. A server behind it —
ordinary backend code. And the model?

We don't have our own model — but the maker of ChatGPT sells access to the machine
behind it. That is the OpenAI API. A quick word on names, because it confuses everyone:
ChatGPT is the product, the website you chat with. OpenAI is the company, and the API is
how our program talks to their model directly. API — a doorway for programs: our server
sends text over the internet, the model's reply comes back as text. No chat window
involved.

I should also say: you don't have to use a paid API at all. You can run a free model on
your own machine — a popular tool for that is called Ollama — and everything in this
lecture would work the same way. For a concrete picture, for the rest of the talk, let's
say we use the OpenAI API.

And what does our server actually send? Exactly the phase-one trick, just through pipes:
one big string — every document in the KB, plus the student's question.

---

## Slide 5 — Phase 2: What the model actually receives  (~2.5 min, total 10.5)

Let's make that string concrete, because this exact shape carries the rest of the
lecture. You can imagine the model receives a text like this: the word "Context", then
the documents pasted in; the word "Question", then the student's question; then one
instruction — "answer using only the context above".

Two terms arrive here. This whole message, everything we send, is called the PROMPT. And
the reference material we paste in for the model to answer from is called the CONTEXT.

Now the important realisation: this is ALL the model sees. It has no memory of Sydney
Met, no hidden database, no idea our university exists. If the right fact is not
somewhere in that prompt, the model can only guess.

So the whole craft of a document chatbot comes down to one question: WHAT goes into this
text? Hold that — it is the rest of the lecture.

---

## Slide 6 — Phase 2: How much of this is actually AI?  (~3 min, total 13.5)

Before we go further, pause and look at what we have — because there is an important
observation here. Any "AI system" you meet is not fully AI. The web page — ordinary
code. The server — ordinary code. Gluing strings together — ordinary code. Exactly ONE
box in this picture is AI: the model.

There is a clean way to tell the two worlds apart — not by definition, but by behaviour.
Ordinary code is DETERMINISTIC: same input, same output, every single time. You can test
it, trust it, debug it — the skills you already have from software engineering apply
directly. The model is NON-DETERMINISTIC: ask the exact same question twice and the
wording of the answer may differ.

So when you hear "AI system", picture this slide: one non-deterministic box, surrounded
by ordinary, deterministic software. And here is the part I want you to remember as
future developers: most of the work — and most of the value you add — lives in the
deterministic part. That is where we spend the rest of today.

---

## Slide 7 — Phase 2 breaks: One question, two million words  (~2.5 min, total 16)

Now phase two breaks. A university KB is not one handbook — it's hundreds of PDFs. Say
300 PDFs, roughly two million words. And our design sends ALL of it, for EVERY question
— even for "what are the library hours?".

I can tell you from experience what happens, because my first real bot was built exactly
this way: it took about a MINUTE to answer. Nobody sits in a chat window waiting a
minute. And think about what we are doing — almost everything we send is completely
irrelevant to the question being asked.

One honest disclaimer before we fix it: we will NOT open up how the model itself works
today. That is a deep field of its own, and for this lecture the model stays a very
capable magic box. Our job — the chatbot developer's job — is to feed that box well:
fast, and accurate.

So the direction is obvious: send LESS. But which part? That question is phase three.

---

## Slide 8 — Phase 3: Send less — pick the right pieces  (~3 min, total 19)

Here's the idea. For any single question, only a few paragraphs out of the whole KB
actually matter. So — ahead of time — we cut every document into small pieces. New term:
a CHUNK. A chunk is a small passage cut from a document, a few paragraphs, ideally about
one topic.

Then, when a question arrives, we pick the top five or ten chunks that look most
relevant, and we build exactly the same prompt as before — same Context-Question shape —
just with those few chunks as the context instead of everything. Two hundred pages
become two pages, per question.

And one framing I really want you to keep. How the model answers from the text we give
it — that is not our department; we take it as given. But choosing WHAT it reads — that
is precisely where you, the chatbot developer, show your skill. Answering like ChatGPT
does is a giant AI problem; picking the right text is an engineering problem, and it is
YOUR problem. Almost everything that made my real bot better over time happened in this
choosing step.

---

## Slide 9 — Phase 3: Finding the pieces — no AI needed  (~3.5 min, total 22.5)

So how do we pick the right chunks? First question to ask: do we need AI for this? And
the honest answer is NO — and I want you to see that concretely.

Here is the KB as it is actually stored: a plain table of chunks. Nothing exotic. The
question comes in: "What are the library opening hours?" Now just count shared words.
Chunk A — the library hours rule — shares three: library, opening, hours. Chunk B, about
enrolment — zero. Chunk C, the exam appendix — one: library. Chunk A wins, and chunk A
is genuinely the right passage.

Add one refinement — rare words count extra, because "library" says more than "the" —
and you have essentially rebuilt BM25, the scoring recipe search engines ran on for
decades. This is how search worked before AI — and notice, it is still ordinary
deterministic code: a word table and counting.

Build this, wire it into our pipeline, and something surprising happens: the bot
suddenly feels GOOD. Fast, cheap, and usually right. My real bot at this stage was
already impressing people. Usually right. Remember that word — usually.

---

## Slide 10 — Phase 3 breaks: Right words, wrong rule  (~3.5 min, total 26)

Here is the failure that ends phase three — and it is a real one; my bot did exactly
this, and this example is its public stand-in.

Week three of term. A student asks: "Can I access the library 24/7?" Count the words.
The Exam Period Appendix contains "library", "access", AND "24/7" — score three, top
result. The general rule — the one that actually governs an ordinary week — says
"library opening hours 8am to 10pm on term days". It shares one word. Score one. Left
behind.

So MetMate answers, fluently and confidently: "Yes — the library is open 24/7." Wrong.
And notice the scary part: every single word of that answer came from a real official
document. Word counting rewards the chunk that ECHOES the question — not the rule that
APPLIES.

There's a quieter failure hiding underneath too: a question about "enrolment" scores
ZERO against a chunk that says "registration". Synonyms are invisible to word counting.

Both failures point the same way. Matching exact words — the technical name is LEXICAL
matching — is not enough. We need to match MEANING — SEMANTIC matching. How on earth
does a computer compute with meaning? That is phase four, and it is the heart of this
lecture.

---

## Slide 11 — Phase 4: Math with words  (~3 min, total 29)

To match meaning, we need to be able to do MATH with words. Take three words from our
university world: enrolment, registration, withdrawal. You and I know enrolment and
registration are nearly the same thing, and withdrawal is roughly the opposite. The
question is: how can a computer measure that?

Here is the simple, almost silly idea: give every word a NUMBER. Enrolment: 5.
Registration: 6. Withdrawal: minus 5. Now "how similar?" becomes "how close?" — plain
subtraction. Five and six are one apart: close, similar. Five and minus five are ten
apart: far, opposite.

This idea — writing words as numbers so that close numbers mean similar meaning — is
called an EMBEDDING. And I will say this directly: if you take only ONE thing home from
this lecture, I would be very glad if it is this concept. Understand embeddings and half
of the modern LLM world becomes accessible to you.

But there's a problem with one number per word. Along comes the word "pass". Where does
it go on this line? It's not similar to enrolment. It's not the opposite either. It's
just… about something else. One number is not enough.

---

## Slide 12 — Phase 4: One number isn't enough — vectors  (~4 min, total 33)

The fix: give each word SEVERAL numbers instead of one — a list. New term: a VECTOR. In
our context, a vector is just a list of numbers. Let the first number measure the
enrolment-versus-withdrawal direction, and the second measure the pass-versus-fail
direction.

Now watch. Enrolment: [5, 0] — strongly about enrolling, nothing to do with passing or
failing. Registration: [6, 0]. Withdrawal: [minus 5, 0]. Pass: [0, 5] — nothing to do
with enrolment. And fail: [0, minus 5], a bonus word.

Each slot in the list is called a DIMENSION — a 3-number vector is 3-dimensional, and so
on.

Now think about the word "course". It's related to enrolment — you enrol in a course.
It's related to passing — you pass a course. But it is not quite either. Do we need a
third slot for it? We could add one — or we can reuse what we already have: course =
[2.5, 2.5]. A bit of both.

And that is the deep trick of embeddings: we do NOT need a new dimension for every word.
A few hundred well-chosen dimensions can place hundreds of thousands of words, each word
a point, similar words nearby. Real production embeddings use roughly three hundred to
three thousand dimensions — not two — but it is exactly this idea, just with more room.

Meaning has become geometry: distance IS similarity.

---

## Slide 13 — Phase 4: Who assigns the numbers?  (~2.5 min, total 35.5)

One question should be bothering you: who assigns all these numbers? If we typed them by
hand it would literally take forever — and we'd argue for a week about "course". The
answer: nobody assigns them. They are LEARNED.

Here is one classic recipe. Take millions of real sentences. Hide a word: "Students must
______ before the census date." Make the computer guess the missing word. Notice the
beautiful part — this needs no human answer sheet, because the hidden word IS the
answer.

Words that fit the same gaps — enrol, register — get pushed toward nearby numbers. Words
that never fit that gap — "party" — drift away. Repeat over millions of sentences, and
the numbers assign themselves.

The general name for this — learning the number-form of things from data instead of
designing it by hand — is REPRESENTATION LEARNING. And there is a famous party trick you
can look up later: with vectors learned this way, king minus man plus woman lands almost
exactly on queen. The arithmetic works because meaning became geometry.

---

## Slide 14 — Phase 4: MetMate searches by meaning  (~3.5 min, total 39)

Now plug embeddings into MetMate. In the build-once lane, when we cut the KB into
chunks, we now also compute each chunk's vector and store both — you can see the stored
KB is still just a table: chunk text, plus its vector. In the live lane, the question
becomes a vector too, and "search" now means: find the chunks whose vectors sit CLOSEST
to the question's vector.

The closeness score between two vectors has an official name — cosine similarity — one
more look-up-able term; it is nothing more than "how close are these two lists of
numbers".

Watch it work. "How do I fix a mistake in my registration?" The right chunk says
"enrolment corrections" — ZERO shared words with the question; keyword search scores it
zero and never finds it. But its vector sits right next to the question's vector — found
by meaning. Search with "registration", and texts about "enrolment" now come to you.

And our library trap? Ask about 24/7 access and the bot now retrieves BOTH library
chunks — the general rule and the appendix — because both are ABOUT library access
times. The model sees the full picture and answers with the condition: 8 to 10 normally,
24/7 only during exams.

Same skeleton, one box upgraded — the bot just learned meaning.

---

## Slide 15 — All together: The whole picture — you built RAG  (~3 min, total 42)

Zoom out and look at the whole machine — colour-coded by the phase that forced each box
into existence. Grey: the phase-two skeleton — page, server, prompt, model, answer.
Teal: phase three — cut into chunks, pick the best ones. Amber: phase four — vectors on
both lanes. Nothing in this picture was designed up front; every box exists because a
failure demanded it.

Now the payoff. This exact recipe — SEARCH a knowledge base, PASTE the winners into the
prompt, let the model WRITE — has a name in the industry: RAG. Retrieval-Augmented
Generation. Retrieval — find it. Augmented — add it to the prompt. Generation — the
model writes. You did not memorise RAG today; you BUILT it, and now you own it.

Two honest footnotes. This diagram is ONE way to build a document chatbot — the field is
young, there is no standard blueprint; this is the shape my real bot uses. And notice
again: exactly one box in this whole picture is generative AI. Even the embedding step,
once trained, is deterministic — same text in, same numbers out, every time. Mostly
ordinary software, remember, around one remarkable box.

---

## Slide 16 — Phase 5: What real chatbots add  (~1.5 min, total 43.5)

Phase five, and I'll keep it to one line per idea — these are the refinements that
separate today's teaching bot from a production bot, and every one of them is
look-up-able.

Hierarchical chunking: store small chunks AND whole sections, so detail questions and
overview questions both work. Context-aware chunking: cut at natural boundaries —
headings, clauses — not blindly every five hundred words. Hybrid search: run keyword
search and meaning search together; each catches what the other misses. Reranking: a
second, more careful pass re-orders the top chunks before they enter the prompt.
Conversation memory: "what about postgrads?" only makes sense given the chat so far —
rewrite it into a full standalone question first. And verification: before showing an
answer, check every claim against the source documents — and if the support is not
there, say honestly, "I don't know".

Each of these earned its place in my real bot the same way everything today did: a real
failure demanded it.

---

## Slide 17 — Three things to take home  (~1.5 min, total 45)

Three things to take home.

One: an AI product is mostly ordinary software. One AI box — and your code, your
engineering, decides what it reads. The skills you are already building apply directly.

Two: embeddings. Words as numbers, meaning as distance. That is the one concept I asked
you to keep — it unlocks half of what you will read about LLMs from here.

Three: RAG — retrieve, augment, generate. You built it today, phase by phase, failure by
failure — so it is yours now.

The recipe is public; anyone can follow it. Making it work for a real domain — your
future workplace's documents, rules, quirks — that part is not in any tutorial. That
part is yours.

Thank you — I'm happy to take questions.
