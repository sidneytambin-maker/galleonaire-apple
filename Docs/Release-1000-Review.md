# 1,000-question release review

The expansion adds 250 independently worded book questions: 17 at each of levels 1–10 and 16 at each of levels 11–15. The resulting pools have 67 and 66 questions respectively. All 750 previous question objects and the existing 600-entry migration mapping were compared against main commit 5e8f37e4168cc06cd5fafb5ab12fd8e876244d8c and are unchanged.

Each addition records a fact key, explicit novel context, chapter, explanation and source URL. Editorial review removed repeated facts, an overlapping Hepzibah/Hufflepuff question, book-versus-film substitutions and incorrect chapter references. Specialist details were checked against chapter notes and corroborating references, including official Harry Potter material and publisher resources. The committed CSV is the reproducible source for the additions. Unique keys alone are not a guarantee against semantic duplicates; tester reports remain valuable.

The shared iPhone/Watch views add finite decorative particle effects for correct answers, losses, all three lifelines and victory, plus a static gold victory seal. Effects cannot intercept input or own accessibility focus. They stop when Reduce Motion, Dim Flashing Lights or backgrounding applies. Lifeline sounds remain handled by the existing game transaction.

Local validation: question-pack reproducibility and all 66 Python tests pass. New tests cover exact expansion distribution, source/context retention and refusing to retry invalid Apple build identities or unknown encryption declarations. Native unit, iPhone UI, Watch UI and embedded archive validation are mandatory CI gates before signing and uploading. Simulator checks cannot verify real-device VoiceOver audio, tactile effects or Watch battery consumption.

The upload runs only after all four native gates. A separate protected-environment workflow verifies the completed release run, waits for its exact Apple build, saves testing notes, verifies both beta-group assignments, submits beta review and records internal/external availability. Apple review pending is reported as pending rather than release success.

Release outcome: build 23 passed all four native gates, uploaded successfully, and Apple returned APPROVED with IN_BETA_TESTING internally and externally. See Release-Status.md and Release-23-Verification.json.
