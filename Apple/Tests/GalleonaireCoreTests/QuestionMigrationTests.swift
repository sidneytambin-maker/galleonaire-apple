import XCTest
@testable import GalleonaireCore

final class QuestionMigrationTests: XCTestCase {
    func testEveryLegacySeenFactSurvivesRegradingExactlyOnce() throws {
        let bank = try QuestionBank.bundled()
        var legacy = GameArchive()
        legacy.highScore = 125000
        legacy.lastCorrectPosition = 2
        for (id, level) in try XCTUnwrap(bank.previousLevels) {
            legacy.recent[level, default: []].append(id)
        }
        let migrated = try legacy.migratingQuestionHistory(to: bank)
        XCTAssertEqual(Set(migrated.recent.values.flatMap { $0 }), Set(legacy.recent.values.flatMap { $0 }))
        XCTAssertEqual(migrated.recent.values.reduce(0) { $0 + $1.count }, 600)
        XCTAssertEqual(migrated.highScore, 125000)
        XCTAssertEqual(migrated.lastCorrectPosition, 2)
        XCTAssertEqual(migrated.questionContentRevision, 2)
        for (level, ids) in migrated.recent {
            XCTAssertTrue(ids.allSatisfy { bank.question($0)?.level == level })
        }
        XCTAssertEqual(try migrated.migratingQuestionHistory(to: bank), migrated)
        try GameEngine(bank: bank, archive: migrated).validateArchive()
    }

    func testMigrationRejectsUnknownOrMisfiledLegacyHistory() throws {
        let bank = try QuestionBank.bundled()
        var legacy = GameArchive()
        legacy.recent = [1: ["missing-question"]]
        XCTAssertThrowsError(try legacy.migratingQuestionHistory(to: bank))
        legacy.recent = [2: ["ga_01_01"]]
        XCTAssertThrowsError(try legacy.migratingQuestionHistory(to: bank))
        legacy.recent = [1: ["ga_01_01", "ga_01_01"]]
        XCTAssertThrowsError(try legacy.migratingQuestionHistory(to: bank))
        legacy.recent = [:]
        legacy.questionContentRevision = 99
        XCTAssertThrowsError(try legacy.migratingQuestionHistory(to: bank))
    }

    func testMigratedRecordsPersistAndAvoidRepeatingSeenFacts() throws {
        let bank = try QuestionBank.bundled()
        var legacy = GameArchive()
        legacy.recent = [1: ["ga_01_01"]]
        let migrated = try legacy.migratingQuestionHistory(to: bank)
        let data = try JSONEncoder().encode(migrated)
        let restored = try JSONDecoder().decode(GameArchive.self, from: data)
        XCTAssertEqual(restored, migrated)
        for seed in 0..<40 {
            var engine = try GameEngine(bank: bank, archive: restored)
            try engine.newGame(seed: UInt64(seed))
            XCTAssertNotEqual(engine.question?.id, "ga_01_01")
            XCTAssertEqual(engine.archive.questionContentRevision, 2)
        }
    }
}
