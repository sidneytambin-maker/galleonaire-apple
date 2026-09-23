# 600-question review: 23 September 2026

The bank contains 600 questions, exactly 40 per each of the 15 prize levels.
`Reference/question-additions-600.csv` adds precisely IDs 31-40 at each level.
All 450 preceding IDs remain; the immutable original 300-question reference is untouched.

All 150 additions have independently written questions, four distinct answers, a
single correct answer, an explanation, a fact identifier and a traceable official
source. The sources were checked against the official Harry Potter fact files and
Rowling archive. New topics include character histories, wand materials, magical
creatures, Hogwarts locations and spells. Later levels include more specialist
archive facts. No passages from novels, artwork or film material were imported.

The additions were compared with the existing question list for duplicate facts.
Automated checks reject repeated normalized questions, answer options, IDs or fact
identifiers and enforce ten additions per level. Separate questions about different
characters' houses or different wand components ask distinct facts. Semantic review
is still necessary: unique identifiers alone cannot prove factual uniqueness.

`Reference/question-context-clarifications.json` updates 263 older entries with
specific book/film wording, full titles and/or clearer source notes. Plot questions
identify the relevant book; adaptation differences identify the film. The Gillyweed
answer explicitly distinguishes Dobby in the fourth book, Harry Potter and the
Goblet of Fire, from Neville in its 2005 film. Room of Requirement discovery,
Dumbledore's Army betrayal, Fiendfyre and the Burrow attack receive the same treatment.

Recent-question history now keeps 38 entries per level, avoiding the previous 38
questions at that level where possible. Each draw additionally shuffles all four
answers and chooses a correct position different from the last draw. The displayed
order, scoring and lifelines use the same permutation.

Run `python Scripts/question_pack.py` and the Python test suite to verify the
reproducible resource. Native unit tests cover repeat history, all answer positions,
swaps, scoring, lifelines, persistence and legacy archives. Native UI tests select
answers by their text and check separate question/previous-answer elements.
