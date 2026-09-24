# Native accessibility implementation and verification

Implementation follows Apple's native guidance:

- https://developer.apple.com/documentation/swiftui/accessibilityfocusstate
- https://developer.apple.com/documentation/accessibility/accessibilitynotification/announcement
- https://developer.apple.com/documentation/swiftui/tabview
- https://developer.apple.com/documentation/avfaudio/avaudioplayer/volume
- https://developer.apple.com/documentation/watchos-apps/setting-up-a-watchos-project

## September gameplay revision

Game, How to play and Settings are persistent bottom tabs, left to right. iPhone
uses the native tab bar. Watch uses three labelled icon buttons with selected
state and 44-point minimum targets, without an inactive adjustable/page control.
The Game page starts with one combined heading: "Galleonaire: a magical quiz game".
Artwork is decorative and hidden from VoiceOver; full text wraps with Dynamic Type.

An answer's standard activation scores immediately. No custom single-tap gesture,
locking stage or answer confirmation overrides VoiceOver. A correct answer now
advances atomically to the next question without a button, timer or speech wait.
The new question has its own accessible heading, with a focus identity containing
its question ID. Previous answer feedback is a separate element above it, reached
with a backward swipe. The answer subtree is replaced on every draw so a focused
old answer cannot acquire the next question's answer text. Focus is cleared before
scoring and requested on the new heading after the view update. A wrong answer
instead shows the terminal result, correct answer, explanation, question reached,
prize reached and winnings kept. Question 15 correctly ends in victory.

Finished games show Main Menu and Play Again. Main Menu clears only the finished
game, saves that transition, and preserves highest prize and question history.
Only records and preferences are saved to disk, never a live game. Every fresh
process launch starts at the main menu, including upgrades from older saved games.
Switching tabs or foregrounding a still-running process keeps the current game.
Leaving an unfinished game for another tab does not discard it. Walk Away,
Restart and high-score reset retain destructive-action cancellation.

Fifty-Fifty removes the two wrong buttons from both the visual and accessibility
trees. Each audience percentage is included in its answer button, before the
answer text; the small visual bar is not a separate VoiceOver element. After
Fifty-Fifty, votes are normalized to the remaining answers, including older saves.
Swap Question retains the legacy `freePass` storage identifier for compatibility.
The question's named actions also open Lifelines, Prize Ladder and Settings.

Both native sliders cover 0-100 percent with one-percent direct adjustments and
five-percent VoiceOver increments. Zero is silence and 100 is full app gain
relative to device volume. There is no hidden VoiceOver gain ceiling. Music
continues while changing tabs; active effects respond to volume/mute changes.
Every game sound has a separate, directly playable Settings preview button.
No app-owned question speech competes with VoiceOver.

## Verification boundary

Shared logic tests cover immediate answer-and-advance, stale-question rejection,
all terminal return-to-menu paths, records-only persistence, cold-launch reset,
lifeline order, older saves,
and every integer volume from 0 through 100. Native UI tests cover both platforms;
iPhone also has a home accessibility audit and largest-text screenshots. Both
platforms have full 15-question UI games through the million-galleon result.
The home art caption uses intrinsic text height rather than a fixed-height
overlay, allowing it to expand at the largest accessibility text sizes.
Audio files are checked for non-silence, clipping, duration and distinct content;
success/failure frequency ranges are additionally compared.

Native slider gestures are approximate; Apple's XCUIAutomation documentation
does not guarantee exact position fidelity. The UI test reads back each result,
checks increasing and decreasing values, and allows at most three real drags to
reach an endpoint. Zero and 100 must still match exactly, and survive relaunch.
Intermediate drag coordinates allow ten percentage points of positioning error;
the shared audio-gain tests check every integer exactly. Do not replace these
checks with a disabled test, a hard-coded test-only setting or a wider gain cap.
Reference: https://developer.apple.com/documentation/xcuiautomation/xcuielement/adjust(tonormalizedsliderposition:)

Actual VoiceOver focus announcements, speech/music balance, speaker output,
haptics, interruptions and paired-device preference delivery require physical
testing. Automated audits or compilation do not prove complete accessibility.

## Physical regression checklist

- Start a game, answer correctly and note the highest prize. Close the app from
  the app switcher, relaunch, and confirm Main Menu with the same highest prize
  and no resumed question. Repeat on Watch after terminating the app there.
- Lose a question and separately walk away. Check that Main Menu and Play Again
  are reachable, and that restarting never traps the user on an old result.
- Activate a correct answer with VoiceOver. Expect immediate advancement and a
  new-question announcement with no answer or prior explanation spoken first.
  Swipe left to hear the previous explanation as a separate item. There must be no Next Question control or waiting period.
  An incorrect answer must end the game and focus its complete summary instead.
- Switch between all four tabs during play. The in-memory question and used
  lifelines must remain unchanged until the process is closed.
- Use Fifty-Fifty and Ask the Audience in both orders. Only surviving answers
  should be reachable and each should include its own audience percentage.
- Adjust both volumes up and down with VoiceOver and direct touch. Check zero,
  intermediate levels and 100, then relaunch and check retained preferences.
- Play every individual sound preview. Check distinct correct/incorrect cues,
  audience applause, Fifty-Fifty and Swap Question, plus milestones and victory.

## 23 September visual and answer-order changes

Original enchanted-library artwork remains decorative. Native text stays on opaque,
high-contrast panels and wraps at accessibility sizes. A single green/red edge pulse
accompanies correct/incorrect answers; it never repeatedly strobes or covers the text.
Reduce Motion and Dim Flashing Lights each disable it, including if enabled mid-pulse.
Result wording and symbols remain available independently of colour or animation.

The shuffled answer permutation is part of each game state. Scoring, elimination and
polling use that same displayed question. The last correct position survives records-only
saves, so consecutive draws, swaps and restarts use a different position. Legacy saves
without a permutation keep their canonical order. Malformed permutations are rejected.

## 24 September: text sizing and enhancement checks

Use balanced standard text sizes by default. Do not force an accessibility Dynamic Type category or use oversized text as the default presentation. Text follows the user's Apple text-size preferences through semantic fonts and scaled metrics; Zoom is managed by the operating system. The XXXL accessibility launch argument exists only in the explicit iPhone stress tests. Watch headings use compact semantic headline sizing, with 44-point navigation controls.

Statistics expose concise combined labels; decorative bars and magical artwork are hidden from VoiceOver. Test all four tabs, final-question announcements, each of the 15 prize-ladder positions, available and used lifelines, and the separate previous-answer summary. Physical VoiceOver speech, audio quality, pairing and haptic strength still require real-device checks; retain the existing audio mixing behaviour.
