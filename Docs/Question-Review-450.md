# 450-question editorial review

Reviewed 12 September 2026. The shared iPhone and Watch bank contains 450 questions: 30 at each of 15 prize levels. Exactly 150 new IDs (21-30 at every level) supplement the original 300 stable IDs. The immutable original reference and its recorded SHA-256 are unchanged.

## Evidence and scope

All 150 additions and 23 replacement questions have a source key, an independently written question and explanation, and a URL from the official Harry Potter site, J. K. Rowling's writing archive or Warner Bros. Studio Tour. The registry is `Reference/question-sources.json`; the two pipe-delimited CSV files are the editable content. They use 65 distinct source entries. Film, book and expanded wizarding-world contexts are named where a distinction matters. Edition-dependent page counts were not used.

The original bank was also read for factual ambiguity and repeated underlying facts. Twenty-three questions were replaced and fifteen further questions had wording or choices clarified. The other 262 original questions retain their original book/film source notes. Those notes are not a claim that every retained fact has been independently reverified against an online page in this sprint.

Examples of corrections:

- The Pensieve question now asks about revisiting memories, not removing them from a person's mind. [Rowling: Pensieve](https://www.harrypotter.com/writing-by-jk-rowling/pensieve).
- The Thestral question includes understanding death, not merely witnessing it. [Rowling: Thestrals](https://www.harrypotter.com/writing-by-jk-rowling/thestrals).
- The second-task question no longer offers both Scottish selkies and merpeople as competing answers. It asks who guards the hostages, not who kidnapped them. [Official second-task account](https://www.harrypotter.com/features/twelve-of-our-favourite-moments-from-the-triwizard-tournament-tasks), [Rowling: The Great Lake](https://www.harrypotter.com/writing-by-jk-rowling/the-great-lake).
- Regulus's question asks who orders Kreacher to take the locket home, rather than confusing the person issuing the order with the house-elf carrying it out. [Official Regulus account](https://www.harrypotter.com/features/unsung-heroes-of-harry-potter-stories-regulus-black).
- The old question attributing Hermione's traitor jinx to the Protean Charm, the Defence exam question with multiple valid creature answers, and the question with two valid young Tom Riddle actors have been replaced.
- The Book of Admittance, wizarding schools, wand cores and travel history additions use Rowling's archived essays. [Admission](https://www.harrypotter.com/writing-by-jk-rowling/the-quill-of-acceptance-and-the-book-of-admittance), [Wand cores](https://www.harrypotter.com/writing-by-jk-rowling/wand-cores).
- Film construction statistics are explicitly about the production, not fictional canon. [Studio sets](https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/sets/), [Studio props](https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/props/).

## Duplicate review

Each question has an editorial `factKey` describing the underlying fact. Repeated Pensieve, Peverell brother, mirror, bezoar, portrait-passage and actor questions were replaced. All 450 fact keys and normalized question texts are now unique. A pairwise text-similarity review was also performed: similarly worded questions about different actors, different Patronuses or different historical officeholders ask distinct facts and were retained.

Fact keys are editorial annotations, not an automatic truth or semantic-understanding oracle. New content must still be read alongside the existing questions, including its distractors, rather than assigning a fresh key to a rephrased fact. Difficulty is editorial and should be refined from tester feedback without duplicating or changing stable IDs unnecessarily.

## Reproducible checks

Run `python3 Scripts/question_pack.py --write` after editing the source data, then run `python3 -m unittest discover -s Scripts -p 'test_*.py' -v`. The normal `question_pack.py` check rejects a stale bundled bank. Tests check exact per-level additions, stable IDs, original-file hash, distinct answer choices, reproducibility, source traceability, balanced correct-answer positions and annotated duplicate facts.

The release inspector compares the actual questions.json bytes in both apps inside the signed IPA with the reviewed source. A package containing an old bank or different iPhone/Watch banks is rejected before upload. Automated checks do not replace factual review or physical VoiceOver testing.

Git attributes preserve the immutable original's Windows CRLF line endings on macOS checkouts, while the generated bank uses LF. This retains the original SHA-256 check rather than ignoring platform differences or weakening the content check.
