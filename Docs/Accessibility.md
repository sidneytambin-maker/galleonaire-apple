# Native accessibility implementation and verification

Implementation follows Apple's native guidance:

- https://developer.apple.com/videos/play/wwdc2021/10223/
- https://developer.apple.com/documentation/swiftui/accessibilityfocusstate
- https://developer.apple.com/documentation/accessibility/accessibilitynotification/announcement
- https://developer.apple.com/documentation/watchos-apps/setting-up-a-watchos-project

Both native targets use semantic SwiftUI buttons, toggles, sliders and headings.
Full question and answer text wraps without a line limit. Reading order is
question heading, question, answers, confirmation/result, lifelines, prizes and
remaining controls. Decorative artwork and progress graphics are hidden from
VoiceOver; progress has a textual equivalent. Selected/eliminated/locked/correct/
incorrect answer states have text and accessibility values, not colour alone.

Question focus moves only on new questions, explicit navigation or a result.
Lifelines and settings are also available through named question actions. Native
modal dismissal supplies cancellation. New-game/restart and walking away use
confirmation; answer selection does not commit the answer. Volume is a native
slider in five-percent increments with a percentage value. No custom gestures
replace VoiceOver, and no app-owned question speech is present.

Animations are short and disabled by Reduce Motion. Music is capped at six
percent, effects at eighteen percent while VoiceOver is enabled, while retaining
the user's selected preference. Effective sound balance still needs real-device
listening, including speech and interruptions.

## Evidence status

Native unit tests, iPhone UI tests and Watch UI tests are being run through the
separate cloud workflow. Test results and screenshots must be reviewed before
marking any platform verified. Source inspection and an automated audit do not
prove hardware VoiceOver usability or formal WCAG AAA conformance.

Physical checks remain required: complete new game, all lifelines, cancellation,
answer lock/result, settings, interruption/resume, loss/win/restart; the same
journeys on Watch; sound balance and settings convergence while disconnected.
