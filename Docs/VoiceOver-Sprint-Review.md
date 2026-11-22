# 22 November 2026 review: exam navigation and content

The reported Next announcement came from a focused button whose label changed to Skip Question when the next unanswered question arrived. The shared iPhone/Watch paper now uses a stable Next Question label, recreates the question list for each question identity, reveals the heading and requests accessibility focus after layout. Previous and navigator actions clear stale focus. Cancellation prevents a delayed task focusing an obsolete question. There is no extra announcement duplicating the heading.

The nearby audit covered exam entry, answers, navigation, review, results, timer updates, Classic, statistics grouping, semantic text sizes, decorative elements and native controls. Answer choices retain native Button semantics with one explicit label/value. The audit removed an accessibility wrapper that discarded the native button role; targeted UI assertions check that answers remain buttons. Timer checks publish only changed archives. Result references open through a native detail link. Existing green/gold styling, wrapping and Reduce Motion treatment remain. No new animation or correctness cue occurs during an exam.

40 original questions were added: 20 intermediate and 20 expert. All 1,264 existing questions were included in fact/wording comparisons. Editorial checking covered each fact, all choices, answer, explanation, attribution, difficulty and answer disclosure. Drafts repeating the Book of Admittance binding, two Boggarts, Quirinus, film prop bones and shopfront period were rejected, not merely reworded. The school boarding-age draft was replaced because of its proximity to an existing attendance-age question. Two remaining automatic flags concern a substring collision and unrelated buildings with the same floor number; individual reasons are in exam-similarity-review.json.

The bank validator checks unique IDs, normalized stems, fact keys, choices, source metadata, eligibility, counts and compatible generation for all 20 papers. These checks complement editorial review; they cannot mathematically prove the absence of every possible semantic overlap. Source material was opened and checked on 22 November 2026; questions and explanations are newly written. No passages, quizzes or song lyrics are reproduced.

1,304 total unique questions in Classic; 1,036 of these eligible for exams, comprising 507 intermediate and 529 expert. Existing records and saved attempt snapshots remain unchanged. Classic stays at 15 questions per game; papers remain 20/50. Difficulty is an editorial assessment, not calibrated player data.

Final candidate verification passed 62 Swift core tests, 95 Python checks and three UI tests per platform using Xcode 27.2 (27B52). Native UI checks ran on iPhone 18 Pro Max with iOS 27.2 and Apple Watch Ultra 4 (49mm) with watchOS 27.2: O.W.L. navigation/submission/review; N.E.W.T. skip/answer/back/save/resume; Classic entry plus completed exam and legacy statistics. Answer controls were explicitly required to retain their native button role. The iPhone smoke used the largest accessibility text size and passed description, contrast and clipping audits in portrait and landscape. Portrait screenshots and both platforms' accessibility trees were inspected. The landscape screenshot capture was cropped/misaligned and is not accepted as visual verification. No full supported-model matrix was repeated. Physical-device VoiceOver speech timing was unavailable. Signed-package and Apple submission outcomes are recorded separately in Release-Status.md.

## New question source register

- [J. K. Rowling: Boggart](https://www.harrypotter.com/writing-by-jk-rowling/boggart): ex_n22_010.
- [J. K. Rowling: Castelobruxo](https://www.harrypotter.com/writing-by-jk-rowling/castelobruxo): ex_n22_015.
- [J. K. Rowling: Celestina Warbeck](https://www.harrypotter.com/writing-by-jk-rowling/celestina-warbeck): ex_n22_001, ex_n22_002, ex_n22_023, ex_n22_024.
- [J. K. Rowling: Dolores Umbridge](https://www.harrypotter.com/writing-by-jk-rowling/dolores-umbridge): ex_n22_036.
- [J. K. Rowling: Extension Charms](https://www.harrypotter.com/writing-by-jk-rowling/extension-charms): ex_n22_005, ex_n22_006.
- [J. K. Rowling: Floo Powder](https://www.harrypotter.com/writing-by-jk-rowling/floo-powder): ex_n22_031.
- [J. K. Rowling: Gilderoy Lockhart](https://www.harrypotter.com/writing-by-jk-rowling/gilderoy-lockhart): ex_n22_011, ex_n22_012.
- [J. K. Rowling: Hufflepuff Common Room](https://www.harrypotter.com/writing-by-jk-rowling/hufflepuff-common-room): ex_n22_017, ex_n22_029, ex_n22_030.
- [J. K. Rowling: Ilvermorny](https://www.harrypotter.com/writing-by-jk-rowling/ilvermorny): ex_n22_016, ex_n22_021, ex_n22_022.
- [J. K. Rowling: Mahoutokoro](https://www.harrypotter.com/writing-by-jk-rowling/mahoutokoro): ex_n22_014.
- [J. K. Rowling: Owls](https://www.harrypotter.com/writing-by-jk-rowling/owls): ex_n22_008, ex_n22_009, ex_n22_037.
- [J. K. Rowling: Pensieve](https://www.harrypotter.com/writing-by-jk-rowling/pensieve): ex_n22_004, ex_n22_027, ex_n22_028.
- [J. K. Rowling: Professor Mcgonagall](https://www.harrypotter.com/writing-by-jk-rowling/professor-mcgonagall): ex_n22_035, ex_n22_039, ex_n22_040.
- [J. K. Rowling: Professor Quirrell](https://www.harrypotter.com/writing-by-jk-rowling/professor-quirrell): ex_n22_020.
- [J. K. Rowling: Sir Cadogan](https://www.harrypotter.com/writing-by-jk-rowling/sir-cadogan): ex_n22_033, ex_n22_034.
- [J. K. Rowling: The Knight Bus](https://www.harrypotter.com/writing-by-jk-rowling/the-knight-bus): ex_n22_038.
- [J. K. Rowling: The Leaky Cauldron](https://www.harrypotter.com/writing-by-jk-rowling/the-leaky-cauldron): ex_n22_019.
- [J. K. Rowling: The Potter Family](https://www.harrypotter.com/writing-by-jk-rowling/the-potter-family): ex_n22_003, ex_n22_025, ex_n22_026.
- [J. K. Rowling: The Quill Of Acceptance And The Book Of Admittance](https://www.harrypotter.com/writing-by-jk-rowling/the-quill-of-acceptance-and-the-book-of-admittance): ex_n22_007.
- [J. K. Rowling: Uagadou](https://www.harrypotter.com/writing-by-jk-rowling/uagadou): ex_n22_013.
- [Warner Bros. Studio Tour London: Costumes](https://www.wbstudiotour.co.uk/the-experience/explore-the-tour/costumes/): ex_n22_018, ex_n22_032.

Classic levels of this update: 7: 2, 8: 6, 9: 9, 10: 3, 14: 9, 15: 11.

Native accessibility guidance consulted: [Apple: accessibility child behaviour, ignore](https://developer.apple.com/documentation/swiftui/accessibilitychildbehavior/ignore). A new ignored-child element starts without inherited properties; retaining the native answer Button avoids hiding its action and role.
