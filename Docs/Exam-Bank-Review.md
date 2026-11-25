# Exam bank review

The original 1,000-record resource, IDs and Classic levels remain unchanged. Each has one reviewed primary subject in `Reference/exam-classifications.json`. Three source/version corrections are applied separately at runtime: Hagrid's name links to his official profile; the Howler's congratulations are attributed to the film; and the Gringotts dragon's breed is attributed to the official encyclopedia rather than the novel. The original source record remains available for provenance. Exam difficulty and eligibility are separate from Classic levels; introductory questions are excluded from exams.

500 additions are stored separately and joined into Classic at their reviewed difficulty levels. The game now contains 1,500 questions, including 602 intermediate and 630 expert exam-eligible questions (1,232 in total, a subset of the same database). This public update adds 196 questions: 95 intermediate and 101 expert. Every subject has more questions than a full paper requires, allowing both selection and order to vary on retakes.

| Subject | Original classified | All additions | This update | Intermediate | Expert |
| --- | ---: | ---: | ---: | ---: | ---: |
| Characters and Magical Families | 173 | 31 | 20 | 80 | 71 |
| Charms, Spells and Defence | 65 | 65 | 24 | 56 | 60 |
| Potions, Herbology and Magical Healing | 64 | 63 | 24 | 53 | 63 |
| Transfiguration and Magical Transformations | 44 | 61 | 14 | 39 | 57 |
| Magical Creatures and Beasts | 104 | 53 | 24 | 59 | 66 |
| Hogwarts and Wizarding Education | 144 | 34 | 20 | 68 | 64 |
| History of Magic and Wizarding Society | 74 | 45 | 20 | 48 | 64 |
| Magical Objects, Wands and Places | 185 | 36 | 18 | 115 | 65 |
| Quidditch, Tournaments and Challenges | 82 | 53 | 16 | 42 | 59 |
| Harry Potter Films | 65 | 59 | 16 | 42 | 61 |

Sources include the seven novels, Rowling's companion books and screenplay, her Pottermore essays now hosted on HarryPotter.com, official encyclopedia and editorial material, Warner Bros. Studio Tour production accounts and press pack, and Rotten Tomatoes film-credit listings. The Harry Potter Lexicon provides explicit book/chapter and original-publication reference checks for specialist details. Source labels distinguish books, films, screenplay, Famous Wizard cards and Book of Potions. No fan speculation is treated as an established fact. Questions, distractors and explanations use original wording.

Difficulty review distinguishes ordinary narrative knowledge from precise book incidents, specialist magical lore and production details. Very difficult items include obscure names, exact quantities, rules, dates and incidental details. An expert designation is an editorial assessment, not a measured population difficulty score; no psychometric calibration is claimed.

Editorial checks covered the tested fact, all four choices, correct answer, explanation, source and version. Rejected draft additions included Lyall Lupin's specialism, Hope Howell's workplace, Castelobruxo robes, Uagadou wandless casting, dragon-core accidents and Durmstrang visitor Memory Charms, because their facts were already present. The bridge introduction question was replaced with a more specialist structural-material question. Stems that disclosed the owner of the examined wand, Rita's animal form, or the bird used in early Quidditch were rewritten to remove those disclosures without changing the new fact being tested.

`Scripts/exam_bank.py --check` verifies all 1,000 classifications, unique IDs/text/fact keys, four distinct answers, source metadata, all twenty minimum pool sizes, compatible conflict keys and deterministic full-paper generation. The similarity scan compares every addition with the entire existing bank and previous additions. Its remaining candidate pairs have individual editorial resolutions in `Reference/exam-similarity-review.json`; repeated numbers or book titles are not treated as repeated facts. Semantic review remains necessary: a lexical scanner alone cannot prove the absence of paraphrases.

Each attempt draws without replacement, shuffles answer positions, and snapshots its complete question content. Consecutive retakes cannot repeat the exact preceding question order. Pools larger than a paper can also change selection; a pool of exactly fifty necessarily reuses its questions in a fresh order. Future bank updates affect new attempts, never a saved paper.

Validation and release evidence is recorded separately; this document does not assert a successful Apple build or TestFlight availability.
