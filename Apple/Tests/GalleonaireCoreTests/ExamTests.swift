import XCTest
@testable import GalleonaireCore

final class ExamTests: XCTestCase {
    private let start = Date(timeIntervalSince1970: 1_800_000_000)
    private func engine(_ qualification: ExamQualification = .newt, timing: ExamTiming = .standard) throws -> ExamEngine {
        var engine = try ExamEngine()
        try engine.begin(bank: .bundled(), subject: .transformations, qualification: qualification,
                         timing: timing, now: start, seed: 453)
        return engine
    }
    func testEveryGradeBoundaryForBothPapers() {
        for qualification in ExamQualification.allCases {
            let expected: [(ClosedRange<Int>, ExamGrade)] = qualification == .owl ?
                [(0...5, .troll), (6...8, .dreadful), (9...11, .poor), (12...14, .acceptable), (15...17, .exceeds), (18...20, .outstanding)] :
                [(0...14, .troll), (15...22, .dreadful), (23...29, .poor), (30...37, .acceptable), (38...44, .exceeds), (45...50, .outstanding)]
            for (range, grade) in expected {
                for score in range {
                    let result = ExamGrade.grade(score: score, qualification: qualification)
                    XCTAssertEqual(result, grade)
                    XCTAssertEqual(result.passed, score * 100 >= qualification.count * 60)
                }
            }
        }
    }
    func testAllTwentyPapersHaveDistinctCompatibleQuestionsAndFixedAnswerOrder() throws {
        let bank = try ExamBank.bundled()
        XCTAssertEqual(bank.classifications.count, 1000)
        XCTAssertGreaterThanOrEqual(bank.items.filter { $0.difficulty == .expert }.count, 500)
        for subject in ExamSubject.allCases {
            for qualification in ExamQualification.allCases {
                var first = try ExamEngine(), second = try ExamEngine()
                for engine in [0, 1] {
                    if engine == 0 { try first.begin(bank: bank, subject: subject, qualification: qualification, timing: .untimed, now: start, seed: 57) }
                    else { try second.begin(bank: bank, subject: subject, qualification: qualification, timing: .untimed, now: start, seed: 57) }
                }
                let paper = try XCTUnwrap(first.archive.active)
                XCTAssertEqual(paper.questions.count, qualification.count)
                XCTAssertEqual(Set(paper.questions.map(\.id)).count, qualification.count)
                XCTAssertEqual(paper.questions, second.archive.active?.questions)
                let keys = paper.questions.flatMap { $0.item.conflictKeys }
                XCTAssertEqual(keys.count, Set(keys).count)
                XCTAssertTrue(paper.questions.allSatisfy { Set($0.answerOrder) == Set(0..<4) })
                XCTAssertTrue(paper.isValid)
            }
        }
    }
    func testAnswerChangeSkipReturnAndSnapshotResume() throws {
        var e = try engine(.owl)
        let original = try XCTUnwrap(e.archive.active)
        let q = original.questions[0]
        XCTAssertTrue(e.answer(0, questionID: q.id, attemptID: original.id, now: start))
        e.navigate(to: 7, now: start.addingTimeInterval(10))
        XCTAssertFalse(e.answer(1, questionID: q.id, attemptID: original.id, now: start))
        e.navigate(to: 0, now: start)
        XCTAssertTrue(e.answer(2, questionID: q.id, attemptID: original.id, now: start))
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        let disk = ExamPersistence(directory: folder)
        try disk.save(e.archive)
        // Restoring a paper requires no current bank: it includes every original question and answer order.
        var restored = try ExamEngine(archive: disk.load())
        XCTAssertEqual(restored.archive, e.archive)
        XCTAssertEqual(restored.archive.active?.questions[0].item, q.item)
        XCTAssertEqual(restored.archive.active?.questions[0].answerOrder, q.answerOrder)
        XCTAssertEqual(restored.archive.active?.questions[0].answer, 2)
        XCTAssertTrue(restored.answer(nil, questionID: q.id, attemptID: original.id, now: start))
        XCTAssertEqual(restored.archive.active?.unanswered, 20)
        XCTAssertThrowsError(try restored.begin(bank: .bundled(), subject: .films, qualification: .owl, timing: .untimed, now: start, seed: 3))
    }
    func testRetakeCannotRepeatThePreviousOrderEvenWithTheSameSeed() throws {
        let bank = try ExamBank.bundled()
        for qualification in ExamQualification.allCases {
            var e = try ExamEngine()
            try e.begin(bank: bank, subject: .films, qualification: qualification, timing: .untimed, now: start, seed: 6706)
            let first = try XCTUnwrap(e.archive.active)
            e.submit(id: first.id, now: start)
            try e.begin(bank: bank, subject: .films, qualification: qualification, timing: .untimed, now: start, seed: 6706)
            let second = try XCTUnwrap(e.archive.active)
            XCTAssertNotEqual(first.id, second.id)
            XCTAssertNotEqual(first.questions.map(\.id), second.questions.map(\.id))
            XCTAssertEqual(Set(second.questions.map(\.id)).count, qualification.count)
            XCTAssertEqual(e.archive.results.count, 1)
        }
    }
    func testDeadlineRejectsLateInputAndSubmitsExactlyOnceAcrossResume() throws {
        var e = try engine()
        let a = try XCTUnwrap(e.archive.active), q = a.questions[0]
        let correct = try XCTUnwrap(q.answerOrder.firstIndex(of: q.item.question.correctIndex))
        var clock = start.addingTimeInterval(1499)
        XCTAssertTrue(e.answer(correct, questionID: q.id, attemptID: a.id, now: clock))
        e = try ExamEngine(archive: JSONDecoder().decode(ExamArchive.self, from: JSONEncoder().encode(e.archive)))
        clock = start.addingTimeInterval(1500)
        XCTAssertFalse(e.answer((correct + 1) % 4, questionID: q.id, attemptID: a.id, now: clock))
        XCTAssertNil(e.archive.active)
        XCTAssertEqual(e.archive.results.count, 1)
        XCTAssertEqual(e.archive.results[0].score, 1)
        XCTAssertEqual(e.archive.results[0].unanswered, 49)
        XCTAssertTrue(e.archive.results[0].expired)
        XCTAssertEqual(e.archive.results[0].submittedAt, a.deadline)
        XCTAssertEqual(e.submit(id: a.id, now: clock), a.id)
        XCTAssertNil(e.expire(now: clock.addingTimeInterval(600)))
        XCTAssertEqual(e.archive.results.count, 1)
    }
    func testExtendedAndUntimedRulesAndOverdueNavigation() throws {
        var extended = try engine(timing: .extended)
        XCTAssertNil(extended.expire(now: start.addingTimeInterval(2249)))
        extended.navigate(to: 1, now: start.addingTimeInterval(2250))
        XCTAssertEqual(extended.archive.results.count, 1)
        for qualification in ExamQualification.allCases {
            var untimed = try engine(qualification, timing: .untimed)
            XCTAssertNil(untimed.expire(now: start.addingTimeInterval(1_000_000)))
            XCTAssertNotNil(untimed.archive.active)
        }
        XCTAssertNil(try engine(.owl, timing: .extended).archive.active?.deadline)
    }
    func testManualSubmissionAndWarningsAreIdempotent() throws {
        var e = try engine()
        let id = try XCTUnwrap(e.archive.active?.id)
        XCTAssertNil(e.warning(now: start.addingTimeInterval(1199)))
        XCTAssertNotNil(e.warning(now: start.addingTimeInterval(1200)))
        XCTAssertNil(e.warning(now: start.addingTimeInterval(1250)))
        XCTAssertNotNil(e.warning(now: start.addingTimeInterval(1440)))
        XCTAssertNil(e.warning(now: start.addingTimeInterval(1450)))
        XCTAssertEqual(e.submit(id: id, now: start.addingTimeInterval(1451)), id)
        XCTAssertEqual(e.submit(id: id, now: start.addingTimeInterval(1501)), id)
        XCTAssertEqual(e.archive.results.count, 1)
        XCTAssertFalse(e.archive.results[0].expired)
        XCTAssertEqual(e.archive.results[0].grade, .troll)
        XCTAssertEqual(e.archive.results[0].score, 0)
    }
    func testInvalidSaveCannotReplaceGoodExamRecords() throws {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        let disk = ExamPersistence(directory: folder), good = try engine().archive
        try disk.save(good)
        var invalid = good
        invalid.active?.questions[0].answer = 4
        XCTAssertThrowsError(try disk.save(invalid))
        XCTAssertEqual(try disk.load(), good)
        invalid = good
        invalid.active?.questions[0] = ExamPaperQuestion(item: good.active!.questions[0].item, answerOrder: [0, 0, 1, 2], answer: nil)
        XCTAssertThrowsError(try ExamEngine(archive: invalid))
    }
    func testExamAndClassicFilesAndStatisticsRemainIndependent() throws {
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        var classic = try GameEngine(bank: .bundled())
        try classic.newGame(seed: 4)
        _ = try classic.answerAndAdvance(classic.question!.correctIndex, questionID: classic.question!.id)
        let gameDisk = GamePersistence(directory: folder)
        try gameDisk.save(classic.archive.recordsOnly)
        let before = try gameDisk.load()
        var exam = try engine(.owl)
        _ = exam.submit(id: exam.archive.active!.id, now: start)
        try ExamPersistence(directory: folder).save(exam.archive)
        XCTAssertEqual(try gameDisk.load(), before)
        XCTAssertEqual(try ExamPersistence(directory: folder).load().results.count, 1)
    }
    func testLegacyTopicAggregationUsesCountsAndKeepsAmbiguousHistory() {
        let records = [ExamSubject.films.name: AnswerRecord(answered: 2, correct: 1),
                       "Film cast": AnswerRecord(answered: 8, correct: 7),
                       "Story Details": AnswerRecord(answered: 10, correct: 3)]
        let grouped = TopicPerformance.grouped(records)
        XCTAssertEqual(grouped.subjects[.films]?.answered, 10)
        XCTAssertEqual(grouped.subjects[.films]?.correct, 8)
        XCTAssertEqual(grouped.subjects[.films]?.accuracy, 80)
        XCTAssertEqual(grouped.earlier["Story Details"]?.answered, 10)
        XCTAssertEqual(grouped.subjects.values.reduce(0) { $0 + $1.answered } + grouped.earlier.values.reduce(0) { $0 + $1.answered }, 20)
    }
}
