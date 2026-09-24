import XCTest
@testable import GalleonaireCore

final class StatisticsTests: XCTestCase {
    func testCountersRejectStaleAnswersAndCountLifelinesOnce() throws {
        var engine = try GameEngine(bank: .bundled())
        try engine.newGame(seed: 123)
        let q = engine.question!
        XCTAssertTrue(try engine.use(.fiftyFifty))
        XCTAssertFalse(try engine.use(.fiftyFifty))
        _ = try engine.answerAndAdvance(engine.question!.correctIndex, questionID: q.id)
        XCTAssertNil(try engine.answerAndAdvance(0, questionID: q.id))
        let s = try XCTUnwrap(engine.archive.statistics)
        XCTAssertEqual(s.gamesStarted, 1)
        XCTAssertEqual(s.gamesFinished, 0)
        XCTAssertEqual(s.answers.answered, 1)
        XCTAssertEqual(s.answers.correct, 1)
        XCTAssertEqual(s.answers.accuracy, 100)
        XCTAssertEqual(s.currentStreak, 1)
        XCTAssertEqual(s.highestLevel, 2)
        XCTAssertEqual(s.lifelinesUsed, 1)
        XCTAssertEqual(s.levels[1]?.answered, 1)
        XCTAssertEqual(s.categories[q.category]?.correct, 1)
        XCTAssertTrue(s.isValid)
    }
    func testWinLossWalkAwayRestartAndIndependentHighScoreReset() throws {
        var e = try GameEngine(bank: .bundled())
        try e.newGame(seed: 1)
        for _ in 1...15 { _ = try e.answerAndAdvance(e.question!.correctIndex, questionID: e.question!.id) }
        XCTAssertEqual(e.archive.statistics?.gamesWon, 1)
        XCTAssertEqual(e.archive.statistics?.bestBanked, 1_000_000)
        XCTAssertEqual(e.archive.statistics?.bestStreak, 15)
        e.resetHighScore()
        XCTAssertEqual(e.archive.statistics?.gamesWon, 1)
        try e.newGame(seed: 2)
        _ = try e.answerAndAdvance((e.question!.correctIndex + 1) % 4, questionID: e.question!.id)
        XCTAssertEqual(e.archive.statistics?.currentStreak, 0)
        XCTAssertEqual(e.archive.statistics?.answers.answered, 16)
        XCTAssertEqual(e.archive.statistics?.answers.accuracy, 94)
        try e.newGame(seed: 3)
        XCTAssertTrue(e.walkAway()); XCTAssertFalse(e.walkAway())
        try e.newGame(seed: 4); try e.newGame(seed: 5)
        XCTAssertEqual(e.archive.statistics?.gamesStarted, 5)
        XCTAssertEqual(e.archive.statistics?.gamesFinished, 3)
        try e.validateArchive()
    }
    func testLegacySaveDecodesWithoutInventingHistory() throws {
        let data = Data(#"{"schemaVersion":1,"highScore":32000,"recent":{}}"#.utf8)
        let old = try JSONDecoder().decode(GameArchive.self, from: data)
        XCTAssertNil(old.statistics)
        var e = try GameEngine(bank: .bundled(), archive: old)
        try e.newGame(seed: 1)
        XCTAssertEqual(e.archive.highScore, 32000)
        XCTAssertEqual(e.archive.statistics?.gamesStarted, 1)
        XCTAssertEqual(e.archive.statistics?.answers.answered, 0)
    }
    func testStatisticsPersistInRecordsOnlyArchive() throws {
        var e = try GameEngine(bank: .bundled())
        try e.newGame(seed: 12)
        _ = try e.answerAndAdvance(e.question!.correctIndex, questionID: e.question!.id)
        let folder = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: folder) }
        let persistence = GamePersistence(directory: folder)
        try persistence.save(e.archive.recordsOnly)
        let saved = try persistence.load()
        XCTAssertNil(saved.game)
        XCTAssertEqual(saved.statistics, e.archive.statistics)
        try GameEngine(bank: .bundled(), archive: saved).validateArchive()
    }
    func testCorruptStatisticsAreRejected() throws {
        var archive = GameArchive()
        var s = GameStatistics(); s.answers.answered = 4; s.answers.correct = 5
        archive.statistics = s
        XCTAssertThrowsError(try GameEngine(bank: .bundled(), archive: archive))
    }
}
