# Original game discovery

Source inspected 11 September 2026, without modification:

`C:\Users\User\dodge Dropbox\sidney tambin\Public\hand held backup\SAFE_EXPERIMENTS`

- `speech/src/tambin_pre_menu.c`, Galleon Air implementation at lines 5133-5816.
- `galleon_air/galleon_air_questions.json`, structured master question bank.
- `speech/src/galleon_air_questions.inc`, compiled question-bank representation.

## Faithful rules

Fifteen questions, one drawn from each prize level. The ladder is 100, 200, 300,
500, 1,000, 2,000, 4,000, 8,000, 16,000, 32,000, 64,000, 125,000, 250,000,
500,000 and 1,000,000 galleons. These are fictional points, not real-money prizes.

Answer order is fixed, despite the old function being called shuffle_answers.
Exactly four choices and one correct answer. Questions have stable IDs, level,
difficulty, category, book/film source, explanation and source note. The 300-item
master bank has twenty questions per level. It is primarily Harry Potter trivia;
it must not be silently replaced by generic magical trivia.

Correct answers increase the current prize and highest-ever level reached. Wrong
answers end the game: zero before completing question 5, 1,000 after completing
question 5, and 32,000 after completing question 10. Completing question 15 wins.
Voluntary walking away banks the current prize. Original high score tracks the
highest level reached, not only final winnings.

Each lifeline is available once per game:

- Fifty-Fifty: keep the correct answer and one random incorrect answer.
- Ask the Audience: simulated four-way percentages adding to 100; increasingly
  uncertain later in the game, including a 20 percent misleading bias from level
  11. Base support is 62/48/38/30 across levels 1-4/5-8/9-12/13-15, plus 0-8.
- Free Pass: replace the question with a different question at the SAME level.
  It is not a free correct answer. Clears this question's elimination and poll
  state; previously spent lifelines remain spent.

No repeated question in a game. Across games, per-level recent history excludes
the most recent pool-size-minus-two questions (pool-size-minus-one for tiny
pools); fall back to the least recently used eligible question when necessary.

Original menus: new game, how to play, highest score, back. Reset high score and
walk away require confirmation. Original files persist high score and question
history, but not an interrupted active game. Apple adds atomic active-game
persistence, explicit answer confirmation and player-controlled next question.
These interaction improvements do not change scoring or lifeline outcomes.

## Original media and release rights

Original question recordings are self-voicing assets and are NOT shipped in the
Apple edition. Native VoiceOver owns speech. New nonverbal audio and original
artwork require a documented source or generation process. No film soundtrack,
franchise logo, actor likeness or copied book illustration will be imported.

The inherited trivia references third-party books and films. Migration does not
establish ownership of those underlying works or confer a franchise licence.
Metadata must not imply official endorsement. Do not submit an ownership or
licensing declaration without factual support.
