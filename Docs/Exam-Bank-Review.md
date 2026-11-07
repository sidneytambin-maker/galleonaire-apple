# Exam bank review

The original 1,000 records, IDs, Classic levels and source notes remain unchanged. Each has one reviewed primary subject in `Reference/exam-classifications.json`. Exam difficulty and eligibility are separate from Classic levels. Introductory questions and unresolved version/source issues are excluded from exams.

264 original additions are stored separately in the exam resource and joined into Classic's upper-level pool at runtime. There are 509 expert and 485 intermediate eligible questions. Every subject supports a 20-question O.W.L. and a 50-question N.E.W.T.

| Subject | Original classified | Added | Intermediate | Expert |
| --- | ---: | ---: | ---: | ---: |
| Characters and Magical Families | 174 | 4 | 68 | 56 |
| Charms, Spells and Defence | 65 | 38 | 38 | 51 |
| Potions, Herbology and Magical Healing | 64 | 37 | 40 | 50 |
| Transfiguration and Magical Transformations | 44 | 46 | 30 | 51 |
| Magical Creatures and Beasts | 104 | 23 | 44 | 50 |
| Hogwarts and Wizarding Education | 144 | 8 | 55 | 51 |
| History of Magic and Wizarding Society | 74 | 20 | 37 | 50 |
| Magical Objects, Wands and Places | 185 | 10 | 104 | 50 |
| Quidditch, Tournaments and Challenges | 82 | 37 | 35 | 50 |
| Harry Potter Films | 64 | 41 | 34 | 50 |

Sources include the seven novels, Rowling's companion books and screenplay, her Pottermore essays now hosted on HarryPotter.com, official encyclopedia and editorial material, and Warner Bros. Studio Tour production accounts and press pack. The Harry Potter Lexicon provides explicit book/chapter and original-publication reference checks for specialist details. Source labels distinguish books, films, screenplay, Famous Wizard cards and Book of Potions. No fan speculation is treated as an established fact. Questions, distractors and explanations use original wording.

Difficulty review distinguishes ordinary narrative knowledge from precise book incidents, specialist magical lore and production details. Very difficult items include obscure names, exact quantities, rules, dates and incidental details. An expert designation is an editorial assessment, not a measured population difficulty score; no psychometric calibration is claimed.

Editorial checks covered the tested fact, all four choices, correct answer, explanation, source and version. Rejected draft additions included Lyall Lupin's specialism, Hope Howell's workplace, Castelobruxo robes, Uagadou wandless casting, dragon-core accidents and Durmstrang visitor Memory Charms, because their facts were already present. The bridge introduction question was replaced with a more specialist structural-material question. Stems that disclosed the owner of the examined wand, Rita's animal form, or the bird used in early Quidditch were rewritten to remove those disclosures without changing the new fact being tested.

`Scripts/exam_bank.py --check` verifies all 1,000 classifications, unique IDs/text/fact keys, four distinct answers, source metadata, all twenty minimum pool sizes, compatible conflict keys and deterministic full-paper generation. The similarity scan compares every addition with the entire existing bank and previous additions. Its 24 remaining candidate pairs have individual editorial resolutions in `Reference/exam-similarity-review.json`; repeated numbers or book titles are not treated as repeated facts. Semantic review remains necessary: a lexical scanner alone cannot prove the absence of paraphrases.

Each attempt draws without replacement, shuffles answer positions, and snapshots its complete question content. Consecutive retakes cannot repeat the exact preceding question order. Pools larger than a paper can also change selection; a pool of exactly fifty necessarily reuses its questions in a fresh order. Future bank updates affect new attempts, never a saved paper.

Validation and release evidence is recorded separately; this document does not assert a successful Apple build or TestFlight availability.
