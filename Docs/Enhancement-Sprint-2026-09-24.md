# Enhancement sprint: in progress, 24 September 2026

This sprint extends the working game; it does not replace its gameplay or VoiceOver focus implementation.

## Confirmed user requirements
- Exactly 150 new facts, ten per existing prize level; 750 final questions.
- Audit all 600 existing questions and all proposed additions for factual accuracy, ambiguity, distractors, natural complete UK English, spelling and semantic duplication.
- Explicit book/film context. Speak year ranges naturally, for example from 2001 until 2011.
- Deliberate increasing difficulty. Review EVERY question at levels 14 and 15 for genuinely obscure expert knowledge; record moves/replacements explicitly.
- Premium quiz-led magical presentation: prominent question, answer panels, clear lifelines, beautiful prize ladder. Scenery alone is insufficient.
- Ladder VoiceOver elements state N of 15, prize, current/completed and guarantee as appropriate; decoration hidden.
- Preserve existing VoiceOver/audio mixing exactly (user clarification). Improve the music and cues instead.
- Much stronger, longer loss haptic, respecting mute and app inactivity.
- Native iPhone/Watch regression tests, visual evidence, content checks and honest physical-device limits. Do not call a compiling build a completed sprint.

## Implemented, pending native validation
- Original celestial-library asset, quiz-led hero/answer surfaces, level-dependent static magical detail with brief transition respecting Reduce Motion/Dim Flashing Lights.
- Artefact lifeline seals, native accessible controls and distinct available/used/pressed states.
- Redesigned 15-rung prize ladder with one explicit accessibility label per rung.
- Device-local statistics stored in existing archive using an optional backward-compatible field; no invented historical statistics. Separate statistics tab; four Watch controls arranged in two rows for usable targets.
- Original 202.11-second, 64-bar soundtrack with eight developing harmonic scenes. Existing audio session, gain, independent settings and lifecycle logic retained.
- Three loss haptic beats at 650ms intervals; heavy iPhone impact; cancellation on inactive app, Haptics Off or a subsequent feedback event.
- Twenty existing shorthand year ranges rewritten and a regression check added.

## Content and final-round work completed
- 750 questions, 50 per level: exactly 150 additions, ten per level; all 600 original IDs retained.
- All question texts, four-choice sets and explanations reviewed. Fifty-three existing records polished, plus the earlier 20 year-range corrections. One inaccessible homophone/spelling question explicitly replaced.
- 422 existing questions regraded. The final two pools use specialist expert details; familiar plot, character and cast facts moved earlier. Grading is editorial, not invented player-performance data.
- Stable-ID migration preserves all seen-question history when facts move between levels. Highest prize and answer-position history remain intact.
- Distinct final-question cue, final-round visual headings and a restrained lifeline activation glow.
- Expanded iPhone and Watch tests cover statistics, all 15 ladder labels, large-text lifelines, saved-history migration and the final-question announcement. Screenshot evidence is retained by the native workflow.

## Still outstanding
- Complete native iPhone/Watch tests and archive validation, inspect the resulting screenshots, and resolve any failures.
- Publish the validated update with the prepared tester notes through the authorised free release workflow.
- Verify actual App Store Connect processing, review and distribution state. No new live beta is claimed until Apple confirms it.
- Physical VoiceOver speech, audio quality and haptic strength need real-device testing; simulator checks cannot establish those experiences.

## Validation record
- Local suite: 62 passing checks after the final source-reference and film-context corrections.
- Run 36044292652 stopped before compilation because one new separator used Windows-1252. Corrected in dbdd45f.
- Run 36045885427 passed 47 core tests but exposed Swift's type-checking limit in the redesigned ladder. The ladder was split into a small dedicated rung view.
- Run 36049038704 passed 49 of 50 core tests, including all statistics and history-migration checks. Its remaining failure was an old 40-question-pool assumption in the repeat-history test; updated to exercise all 50 questions and the 48-question history limit.
- Run 36049771831 is the current full native validation. Results will be recorded once complete.
- Build 16 remains the previously verified live beta; this sprint has not yet been released.
