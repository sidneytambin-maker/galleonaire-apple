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

## Implemented and natively validated
- Original celestial-library asset, quiz-led hero/answer surfaces, level-dependent static magical detail with brief transition respecting Reduce Motion/Dim Flashing Lights.
- Artefact lifeline seals, native accessible controls and distinct available/used/pressed states.
- Redesigned 15-rung prize ladder with one explicit accessibility label per rung.
- Device-local statistics stored in existing archive using an optional backward-compatible field; no invented historical statistics. Separate statistics tab; four Watch controls in one compact row, with a horizontal fallback on narrow displays and minimum 44-point targets.
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

## Release outcome
- Version 0.1.0 (19) is approved, processed and available to internal and external TestFlight testers, independently confirmed at 21:30 UTC on 24 September.
- Both tester groups, final tester notes and automatic notifications are verified. The public invitation remains open with the optional group limit disabled.
- Native tests, archive/signing validation, upload and visual review are complete. No Apple or account action remains pending.
- Physical VoiceOver speech, audio quality, haptic strength and paired-device preference delivery remain real-device testing requests; simulator checks cannot establish those experiences.

## Validation record
- Local suite: 62 passing checks after the final source-reference and film-context corrections.
- Run 36044292652 stopped before compilation because one new separator used Windows-1252. Corrected in dbdd45f.
- Run 36045885427 passed 47 core tests but exposed Swift's type-checking limit in the redesigned ladder. The ladder was split into a small dedicated rung view.
- Run 36049038704 passed 49 of 50 core tests, including all statistics and history-migration checks. Its remaining failure was an old 40-question-pool assumption in the repeat-history test; updated to exercise all 50 questions and the 48-question history limit.
- Run 36049771831: all 50 core tests passed; 13 of 16 iPhone tests and 5 of 7 Watch tests passed; the unsigned archive passed. Five lifeline-related UI failures identified a real accessibility regression: ignoring the custom button's children produced a container instead of the native button. Changed to the same combined native-button structure already passing on answer controls.
- Reviewed actual iPhone/Watch screenshots from that run. The Watch's two-row tabs consumed too much content space; replaced by a compact row retaining 44-point targets. Added regression assertions for a visible New Game button and native lifeline identity/value. A decorative, noninteractive top backdrop prevents scrolled text competing with the system clock.
- Build 17's validation was cancelled before signing/upload because it contained the same known lifeline regression.
- The release workflow now runs core, iPhone, Watch and archive checks as separate standard free Mac jobs. Signing still requires every validation job to pass. This retains all checks and makes each platform's evidence available sooner.
- Build 16 remained live while the enhancement candidates were validated; build 19 now delivers this sprint.

- Run 36056442756 (build 18): all 50 core tests and all 16 iPhone tests passed; archive validation passed. Six of seven Watch tests passed, including the corrected native lifelines. The new home-layout check caught a two-point overlap at the bottom of New Game. Reduced Watch page spacing from 12 to 8 points; use semantic headline sizing for Watch section/result headings. Default content sizes are not overridden; larger text follows system preferences. Build 18 was not signed or uploaded because its Watch gate failed.

- Run 36058891945, native commit 60851af: 50 core tests, 16 iPhone tests, seven Watch tests and the unsigned archive all passed. Reviewed the final normal-size iPhone home/gameplay and Watch home/statistics/result screenshots. The Watch home button now fits above the navigation; compact headings retain semantic text scaling. Earlier iPhone largest-accessibility-text screenshots and native control checks passed. Main text/background colour pairs range from 9.36:1 to 18.73:1 contrast. Public source history and exported native-test artifacts passed redacted secret scans. Signing/upload is gated on all four completed validation jobs.

- Final workflow 36058891945 succeeded, including signing and upload. Apple processed build 19 as VALID, approved it and returned IN_BETA_TESTING for both audiences. The final notes thank testers and explain system-controlled text sizing, independent audio controls, new content, statistics and requested physical checks. See Release-Status.md.
