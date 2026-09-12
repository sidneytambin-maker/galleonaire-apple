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
locking stage or answer confirmation overrides VoiceOver. A result replaces the
old question controls at the top. Its combined element includes correct/incorrect,
the correct answer and explanation. Focus moves there and the page scrolls to its
start. Next Question follows directly; that action focuses the new question.
The user is never advanced to another question automatically.

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

Shared logic tests cover immediate answers, rejected repeated activations,
all terminal return-to-menu paths, records-only persistence, cold-launch reset,
lifeline order, older saves,
and every integer volume from 0 through 100. Native UI tests cover both platforms;
iPhone also has a home accessibility audit and largest-text screenshots.
Audio files are checked for non-silence, clipping, duration and distinct content;
success/failure frequency ranges are additionally compared.

Actual VoiceOver focus announcements, speech/music balance, speaker output,
haptics, interruptions and paired-device preference delivery require physical
testing. Automated audits or compilation do not prove complete accessibility.
