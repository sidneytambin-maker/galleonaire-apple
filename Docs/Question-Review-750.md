# 750-question editorial review — 24 September 2026

The collection has 750 questions: 50 at each of the existing 15 prize levels. `question-additions-750.csv` contributes exactly 150 new IDs, ten per level (41–50). Every addition has a specific novel, chapter, independent wording, four choices and a factual explanation. No new general-fantasy questions were added.

All 600 existing question/choice/explanation records were read during this review. Fifty-three records receive explicit editorial changes in `question-polish-750.json`: clearer UK English, full titles, accurate source context, corrected accents, plausible distractors and removal of accidental answer clues. Earlier year-range corrections write “from 2001 until 2011” rather than slash or dash shorthand. The original source snapshot and its hash remain untouched.

One existing fact is replaced explicitly: ga_15_38 formerly distinguished four spellings pronounced alike. It now asks about the Cornish song mentioned in the same author note. Its new fact is separate from the 150 additions. This fixes an inaccessible question without quietly replacing the whole bank.

## Difficulty

`question-difficulty-review.json` records all 600 existing assignments and reasons. 422 existing questions change levels; their IDs continue to identify their original facts, apart from the one explicitly documented replacement. Forty existing questions form each level, followed by ten additions. Familiar plot outcomes, common cast questions and basic magical abilities no longer occupy the two expert rounds. Those rounds instead use obscure names, numbers, background lore, production details and precise novel details. Distractors were reviewed and selected numeric ranges tightened.

This is editorial difficulty grading. No player success percentages are invented; beta testing should establish whether any individual question still needs promotion or demotion. Four-choice guessing always remains possible.

## Duplication and accuracy review

`question-semantic-audit-750.json` records the reviewed bank hash and 61 high-overlap pairs. The entire collection was compared at the fact level, including inverse formulations. The candidate list supplements that review; text matching and unique fact keys alone do not prove uniqueness. No duplicated underlying fact was identified in the final additions. Different wand properties, different characters' disguises and distinct book/film events are kept as separate facts.

Several drafts were rejected before integration, including a Mirror of Erised item with two valid choices, an incorrect house attribution, unsupported exam trivia and candidates duplicating previous coverage. The new final-round questions were reviewed separately for obscure expert recall.

Sources for the new questions name the original novel and chapter. HP Lexicon pages are independent secondary references, not official canon publishers; official Harry Potter material corroborates selected details. Existing archive and film questions retain their established sources. The Elder Wand core explanation now correctly cites the official fact file instead of claiming that the novel states the core material.

## Saved records

The content revision includes the previous levels of all 600 IDs. On launch, the app reclassifies seen-question history by stable ID, preserving every seen fact, the highest prize and the last answer position. Invalid or unknown records are rejected rather than silently discarded. Unfinished games already return to the menu on a fresh launch; that behaviour is unchanged. New statistics record the levels actually played and are not rewritten as historical estimates.

## Validation

Rebuilding the bank reproduces the bundled bytes exactly. Automated checks enforce total and per-level counts, exact new IDs, distinct fact keys, four unique nonempty answers, a valid correct index, explicit book context for additions, readable year ranges, source metadata and removal of familiar facts from the expert pools. Native migration tests cover all 600 old IDs, persistence, idempotence, invalid records and repeat avoidance. Final native UI/release results are recorded in the sprint and release reports.
