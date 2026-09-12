import XCTest
@testable import GalleonaireCore

final class GameEngineTests: XCTestCase {
    private func engine(_ seed: UInt64 = 42) throws -> GameEngine {
        var engine = try GameEngine(bank: .bundled())
        try engine.newGame(seed: seed)
        return engine
    }
    private func reach(_ level: Int, _ engine: inout GameEngine) throws {
        while engine.game!.level < level {
            XCTAssertTrue(engine.select(engine.question!.correctIndex))
            XCTAssertTrue(engine.lockAnswer())
            XCTAssertTrue(try engine.nextQuestion())
        }
    }
    func testOriginalBankHas300ValidQuestionsAnd20PerLevel() throws {
        let bank = try QuestionBank.bundled()
        XCTAssertEqual(bank.questions.count, 300)
        for level in 1...15 { XCTAssertEqual(bank.questions.filter { $0.level == level }.count, 20) }
        XCTAssertEqual(bank.ladder, QuestionBank.prizeLadder)
    }
    func testNewGameHasOriginalLifelinesAndNoPreselectedAnswer() throws {
        let e = try engine()
        XCTAssertEqual(e.game?.level, 1)
        XCTAssertEqual(e.game?.prize, 0)
        XCTAssertNil(e.game?.selectedAnswer)
        XCTAssertEqual(e.game?.usedLifelines, [])
    }
    func testCannotLockWithoutSelectionOrSelectOutOfBounds() throws {
        var e = try engine()
        let before = e.archive
        XCTAssertFalse(e.lockAnswer())
        XCTAssertFalse(e.select(-1))
        XCTAssertFalse(e.select(4))
        XCTAssertEqual(e.archive, before)
    }
    func testSelectionDoesNotLockOrAdvance() throws {
        var e = try engine()
        XCTAssertTrue(e.select(0))
        XCTAssertEqual(e.game?.phase, .question)
        XCTAssertEqual(e.game?.level, 1)
        XCTAssertTrue(e.select(1))
        XCTAssertEqual(e.game?.selectedAnswer, 1)
    }
    func testSingleActivationAnswersImmediatelyAndCannotAnswerTwice() throws {
        for correct in [true, false] {
            var e = try engine()
            let index = correct ? e.question!.correctIndex : (e.question!.correctIndex + 1) % 4
            XCTAssertTrue(e.answer(index))
            XCTAssertEqual(e.game?.phase, correct ? .correct : .lost)
            XCTAssertEqual(e.game?.selectedAnswer, index)
            let after = e.archive
            for second in -1...4 { XCTAssertFalse(e.answer(second)); XCTAssertEqual(e.archive, after) }
            try e.validateArchive()
        }
    }
    func testImmediateAnswerRejectsEliminatedAndInvalidOptionsWithoutChangingSave() throws {
        var e = try engine()
        try e.use(.fiftyFifty)
        let before = e.archive
        for index in Array(e.game!.eliminated) + [-1, 4] {
            XCTAssertFalse(e.answer(index))
            XCTAssertEqual(e.archive, before)
        }
        XCTAssertTrue(e.answer(e.question!.correctIndex))
    }
    func testEveryFinishedPhaseCanReturnToPersistedMenuWithoutLosingRecords() throws {
        for phase in [GamePhase.lost, .walkedAway, .won] {
            var e = try engine()
            try reach(phase == .won ? 15 : 6, &e)
            if phase == .walkedAway { e.walkAway() }
            else { e.answer(phase == .won ? e.question!.correctIndex : (e.question!.correctIndex + 1) % 4) }
            XCTAssertEqual(e.game?.phase, phase)
            let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
            defer { try? FileManager.default.removeItem(at: directory) }
            let persistence = GamePersistence(directory: directory)
            try persistence.save(e.archive)
            var restored = try GameEngine(bank: .bundled(), archive: persistence.load())
            let score = restored.archive.highScore, history = restored.archive.recent
            XCTAssertTrue(restored.returnToMenu())
            XCTAssertFalse(restored.returnToMenu())
            try persistence.save(restored.archive)
            let menu = try GameEngine(bank: .bundled(), archive: persistence.load())
            XCTAssertNil(menu.game)
            XCTAssertEqual(menu.archive.highScore, score)
            XCTAssertEqual(menu.archive.recent, history)
        }
    }
    func testMenuCannotDiscardAnUnfinishedGame() throws {
        var e = try engine()
        XCTAssertFalse(e.returnToMenu())
        e.answer(e.question!.correctIndex)
        XCTAssertFalse(e.returnToMenu())
        XCTAssertEqual(e.game?.phase, .correct)
    }
    func testOnDiskRecordsNeverContainAnUnfinishedOrFinishedGame() throws {
        var e = try engine()
        try reach(7, &e)
        try e.use(.audience)
        let live = e.game
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let persistence = GamePersistence(directory: directory)
        for finished in [false, true] {
            if finished { e.walkAway() }
            try persistence.save(e.archive.recordsOnly)
            let loaded = try persistence.load()
            XCTAssertNil(loaded.game)
            XCTAssertEqual(loaded.highScore, 2000)
            XCTAssertEqual(loaded.recent, e.archive.recent)
            let fresh = try GameEngine(bank: .bundled(), archive: loaded)
            XCTAssertNil(fresh.game)
            if !finished { XCTAssertEqual(e.game, live, "Saving records must not reset the running game") }
        }
    }
    func testOldSavedQuestionIsDiscardedOnFreshLaunchWithoutLosingHighestPrize() throws {
        var old = try engine()
        try reach(11, &old)
        try old.use(.fiftyFifty)
        let data = try JSONEncoder().encode(old.archive)
        let saved = try JSONDecoder().decode(GameArchive.self, from: data)
        let fresh = try GameEngine(bank: .bundled(), archive: saved.recordsOnly)
        XCTAssertNil(fresh.game)
        XCTAssertEqual(fresh.archive.highScore, 32000)
        XCTAssertEqual(fresh.archive.recent, old.archive.recent)
    }
    func testAudienceSharesOnlyVisibleAnswersInEitherLifelineOrderAndAfterRestore() throws {
        for seed in 0..<40 {
            for order in [[Lifeline.audience, .fiftyFifty], [.fiftyFifty, .audience]] {
                var e = try engine(UInt64(seed))
                for line in order { try e.use(line) }
                let restored = try GameEngine(bank: .bundled(), archive: JSONDecoder().decode(GameArchive.self, from: JSONEncoder().encode(e.archive)))
                let game = restored.game!, votes = try XCTUnwrap(game.audiencePercentages)
                XCTAssertEqual(game.visibleAnswers.count, 2)
                XCTAssertTrue(game.visibleAnswers.contains(e.question!.correctIndex))
                XCTAssertEqual(votes.reduce(0, +), 100)
                for i in game.eliminated { XCTAssertEqual(votes[i], 0) }
                XCTAssertEqual(game.audiencePercentages, e.game?.audiencePercentages)
            }
        }
    }
    func testSwapQuestionKeepsLegacySaveIdentifierAndClearsVisiblePoll() throws {
        XCTAssertEqual(Lifeline.freePass.name, "Swap Question")
        XCTAssertEqual(try JSONDecoder().decode(Lifeline.self, from: Data("\"freePass\"".utf8)), .freePass)
        var e = try engine()
        try e.use(.audience)
        try e.use(.fiftyFifty)
        try e.use(.freePass)
        XCTAssertEqual(e.game?.visibleAnswers, [0, 1, 2, 3])
        XCTAssertNil(e.game?.audiencePercentages)
    }
    func testLegacyScoringPrimitiveKeepsIntermediatePhaseForCompatibility() throws {
        var e = try engine()
        e.select(e.question!.correctIndex)
        e.lockAnswer()
        XCTAssertEqual(e.game?.phase, .correct)
        XCTAssertEqual(e.game?.level, 1)
        XCTAssertEqual(e.game?.prize, 100)
        XCTAssertEqual(e.archive.highScore, 100)
        XCTAssertFalse(e.lockAnswer())
        XCTAssertFalse(e.select(0))
        XCTAssertFalse(try e.use(.freePass))
        XCTAssertTrue(try e.nextQuestion())
        XCTAssertEqual(e.game?.level, 2)
    }

    func testAutomaticAnswersAdvanceEveryLevelAndStopAtMillion() throws {
        for seed in 0..<10 {
            var e = try engine(UInt64(seed))
            var ids = Set<String>()
            for level in 1...15 {
                let q = try XCTUnwrap(e.question)
                XCTAssertTrue(ids.insert(q.id).inserted)
                let outcome = try XCTUnwrap(e.answerAndAdvance(q.correctIndex, questionID: q.id))
                XCTAssertEqual(outcome.question, q)
                XCTAssertEqual(outcome.level, level)
                XCTAssertEqual(outcome.prize, QuestionBank.prizeLadder[level - 1])
                XCTAssertEqual(e.game?.level, min(level + 1, 15))
                XCTAssertEqual(e.game?.phase, level == 15 ? .won : .question)
                XCTAssertEqual(e.archive.highScore, outcome.prize)
                try e.validateArchive()
            }
            XCTAssertEqual(e.game?.banked, 1_000_000)
            XCTAssertTrue(e.returnToMenu())
            XCTAssertEqual(e.archive.highScore, 1_000_000)
        }
    }
    func testStaleAnswerCannotAnswerTheAutomaticallyLoadedQuestion() throws {
        var e = try engine()
        let old = try XCTUnwrap(e.question)
        XCTAssertNotNil(try e.answerAndAdvance(old.correctIndex, questionID: old.id))
        let after = e.archive
        for index in -1...4 {
            XCTAssertNil(try e.answerAndAdvance(index, questionID: old.id))
            XCTAssertEqual(e.archive, after)
        }
    }
    func testAutomaticFlowRejectsInvalidAndEliminatedAnswers() throws {
        var e = try engine()
        try e.use(.fiftyFifty)
        let q = try XCTUnwrap(e.question), before = e.archive
        for index in [-1, 4] + Array(e.game!.eliminated) {
            XCTAssertNil(try e.answerAndAdvance(index, questionID: q.id))
            XCTAssertEqual(e.archive, before)
        }
        XCTAssertNotNil(try e.answerAndAdvance(q.correctIndex, questionID: q.id))
        XCTAssertEqual(e.game?.visibleAnswers, [0, 1, 2, 3])
        XCTAssertEqual(e.game?.usedLifelines, [.fiftyFifty])
    }
    func testAutomaticLossKeepsReachedPrizeAndGuaranteeWithoutAdvancing() throws {
        for level in 1...15 {
            var e = try engine(UInt64(level))
            while e.game!.level < level {
                let q = e.question!
                try e.answerAndAdvance(q.correctIndex, questionID: q.id)
            }
            let q = e.question!, prize = e.game!.prize
            let result = try XCTUnwrap(e.answerAndAdvance((q.correctIndex + 1) % 4, questionID: q.id))
            XCTAssertEqual(result.phase, .lost)
            XCTAssertEqual(result.prize, prize)
            XCTAssertEqual(result.banked, level > 10 ? 32000 : level > 5 ? 1000 : 0)
            XCTAssertEqual(e.game?.level, level)
            XCTAssertNil(try e.answerAndAdvance(q.correctIndex, questionID: q.id))
        }
    }
    func testLossGuaranteesAtEveryBoundary() throws {
        for level in 1...15 {
            var e = try engine(UInt64(level))
            try reach(level, &e)
            e.select((e.question!.correctIndex + 1) % 4)
            e.lockAnswer()
            XCTAssertEqual(e.game?.phase, .lost)
            XCTAssertEqual(e.game?.banked, level > 10 ? 32000 : level > 5 ? 1000 : 0, "Level \(level)")
            XCTAssertFalse(try e.nextQuestion())
            XCTAssertFalse(e.walkAway())
            try e.validateArchive()
        }
    }
    func testWinningAndNoRepeatsOverManyCompleteGames() throws {
        for seed in 0..<60 {
            var e = try engine(UInt64(seed))
            try reach(15, &e)
            e.select(e.question!.correctIndex)
            e.lockAnswer()
            XCTAssertEqual(e.game?.phase, .won)
            XCTAssertEqual(e.game?.banked, 1_000_000)
            XCTAssertEqual(e.archive.highScore, 1_000_000)
            XCTAssertEqual(Set(e.game!.visited).count, 15)
            XCTAssertFalse(try e.nextQuestion())
            XCTAssertFalse(try e.use(.audience))
            try e.validateArchive()
        }
    }
    func testMilestonesGuaranteedImmediatelyAfterCorrectAnswer() throws {
        for (level, prize) in [(5, 1000), (10, 32000)] {
            var e = try engine()
            try reach(level, &e)
            e.select(e.question!.correctIndex)
            e.lockAnswer()
            XCTAssertEqual(e.guarantee, prize)
        }
    }
    func testWalkingAwayKeepsCurrentWinnings() throws {
        for afterCorrect in [false, true] {
            var e = try engine()
            try reach(9, &e)
            if afterCorrect { e.select(e.question!.correctIndex); e.lockAnswer() }
            let prize = e.game!.prize
            XCTAssertTrue(e.walkAway())
            XCTAssertEqual(e.game?.phase, .walkedAway)
            XCTAssertEqual(e.game?.banked, prize)
            try e.validateArchive()
        }
    }
    func testFiftyFiftyKeepsExactlyOneWrongAndCorrectAnswer() throws {
        for seed in 0..<100 {
            var e = try engine(UInt64(seed))
            let correct = e.question!.correctIndex
            XCTAssertTrue(try e.use(.fiftyFifty))
            XCTAssertEqual(e.game?.eliminated.count, 2)
            XCTAssertFalse(e.game!.eliminated.contains(correct))
            for i in e.game!.eliminated { XCTAssertFalse(e.select(i)) }
            XCTAssertFalse(try e.use(.fiftyFifty))
            try e.validateArchive()
        }
    }
    func testEliminatingSelectedAnswerClearsSelectionWithoutRevealingCorrectAnswer() throws {
        for seed in 0..<30 {
            var e = try engine(UInt64(seed))
            let wrong = (e.question!.correctIndex + 1) % 4
            e.select(wrong)
            try e.use(.fiftyFifty)
            if e.game!.eliminated.contains(wrong) { XCTAssertNil(e.game?.selectedAnswer) }
            else { XCTAssertEqual(e.game?.selectedAnswer, wrong) }
        }
    }
    func testFreePassReplacesSameLevelWithoutPrizeAndDoesNotRestoreLifelines() throws {
        var e = try engine()
        try reach(7, &e)
        let old = e.game!
        try e.use(.fiftyFifty)
        try e.use(.audience)
        XCTAssertTrue(try e.use(.freePass))
        XCTAssertNotEqual(e.game?.questionID, old.questionID)
        XCTAssertEqual(e.game?.level, 7)
        XCTAssertEqual(e.game?.prize, old.prize)
        XCTAssertEqual(e.game?.usedLifelines.count, 3)
        XCTAssertEqual(e.game?.eliminated, [])
        XCTAssertNil(e.game?.audience)
        XCTAssertNil(e.game?.selectedAnswer)
        XCTAssertEqual(e.game?.visited.count, 8)
        XCTAssertFalse(try e.use(.freePass))
        try e.validateArchive()
    }
    func testAudienceTotalsAndLateGameCanMislead() throws {
        var misleading = 0
        for seed in 0..<120 {
            var e = try engine(UInt64(seed))
            try reach(11, &e)
            XCTAssertTrue(try e.use(.audience))
            let poll = e.game!.audience!
            XCTAssertEqual(poll.count, 4)
            XCTAssertEqual(poll.reduce(0, +), 100)
            XCTAssertTrue(poll.allSatisfy { (0...100).contains($0) })
            if poll[e.question!.correctIndex] < poll.max()! { misleading += 1 }
            XCTAssertFalse(try e.use(.audience))
        }
        XCTAssertGreaterThan(misleading, 0)
        XCTAssertLessThan(misleading, 120)
    }
    func testRecentHistoryAvoidsEarlyRepeatsAcrossGames() throws {
        var e = try engine()
        var ids = [e.game!.questionID]
        for seed in 1..<19 { try e.newGame(seed: UInt64(seed)); ids.append(e.game!.questionID) }
        XCTAssertEqual(Set(ids).count, 19)
        XCTAssertEqual(e.archive.recent[1]?.count, 18)
    }
    func testRestartPreservesHighScoreAndClearsActiveState() throws {
        var e = try engine()
        try reach(6, &e)
        try e.use(.fiftyFifty)
        let id = e.game!.id
        try e.newGame()
        XCTAssertNotEqual(e.game?.id, id)
        XCTAssertEqual(e.archive.highScore, 1000)
        XCTAssertEqual(e.game?.usedLifelines, [])
        XCTAssertEqual(e.game?.visited.count, 1)
        XCTAssertEqual(e.game?.level, 1)
    }
    func testPersistenceRestoresQuestionSelectionLifelinesAndRandomState() throws {
        var e = try engine()
        try reach(6, &e)
        try e.use(.audience)
        e.select(e.question!.correctIndex)
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        let store = GamePersistence(directory: directory)
        try store.save(e.archive)
        var restored = try GameEngine(bank: .bundled(), archive: store.load())
        XCTAssertEqual(e.archive, restored.archive)
        try e.use(.freePass)
        try restored.use(.freePass)
        XCTAssertEqual(e.archive, restored.archive)
    }
    func testCorruptSaveIsPreservedBeforeReplacement() throws {
        let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        defer { try? FileManager.default.removeItem(at: directory) }
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let bad = Data("not valid JSON".utf8)
        try bad.write(to: directory.appendingPathComponent("game.json"))
        let store = GamePersistence(directory: directory)
        XCTAssertThrowsError(try store.load())
        try store.preserveUnreadableSave()
        try store.save(try engine().archive)
        let recovery = try FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: nil).first { $0.lastPathComponent.hasPrefix("recovery-") }!
        XCTAssertEqual(try Data(contentsOf: recovery), bad)
    }
    func testMalformedArchivesRejectedBeforeIndexing() throws {
        let e = try engine()
        for invalidLevel in [-1, 0, 16, Int.max] {
            var archive = e.archive
            archive.game!.level = invalidLevel
            XCTAssertThrowsError(try GameEngine(bank: .bundled(), archive: archive))
        }
        var archive = e.archive
        archive.game!.selectedAnswer = 6
        XCTAssertThrowsError(try GameEngine(bank: .bundled(), archive: archive))
        archive = e.archive
        archive.game!.phase = .won
        XCTAssertThrowsError(try GameEngine(bank: .bundled(), archive: archive))
    }
    func testHighestPrizeResetDoesNotDeleteActiveGame() throws {
        var e = try engine()
        try reach(6, &e)
        let game = e.game
        e.resetHighScore()
        XCTAssertEqual(e.archive.highScore, 0)
        XCTAssertEqual(e.game, game)
        try e.validateArchive()
    }
    func testSeedProducesSameQuestionChoices() throws {
        var first = try engine(99), second = try engine(99)
        try reach(15, &first)
        try reach(15, &second)
        XCTAssertEqual(first.game?.visited, second.game?.visited)
        XCTAssertEqual(first.game?.random, second.game?.random)
    }
}
