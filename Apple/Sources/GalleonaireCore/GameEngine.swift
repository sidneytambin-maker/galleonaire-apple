import Foundation

public enum Lifeline: String, Codable, CaseIterable, Identifiable, Sendable {
    case fiftyFifty, audience, freePass
    public var id: String { rawValue }
    public var name: String {
        switch self { case .fiftyFifty: return "Fifty-Fifty"; case .audience: return "Ask the Audience"; case .freePass: return "Swap Question" }
    }
    public var detail: String {
        switch self {
        case .fiftyFifty: return "Removes two incorrect answers. Available once per game."
        case .audience: return "Shows a simulated audience vote. The audience can be wrong. Available once per game."
        case .freePass: return "Replaces this question at the same prize level. Available once per game."
        }
    }
}

public enum GamePhase: String, Codable, Sendable { case question, correct, lost, won, walkedAway }

public struct AnswerOutcome: Equatable, Sendable {
    public let question: Question
    public let phase: GamePhase
    public let level: Int
    public let prize: Int
    public let banked: Int
}

public struct RandomState: Codable, Equatable, RandomNumberGenerator, Sendable {
    public var state: UInt64
    public init(seed: UInt64) { state = seed }
    public mutating func next() -> UInt64 {
        state &+= 0x9e3779b97f4a7c15
        var z = state
        z = (z ^ (z >> 30)) &* 0xbf58476d1ce4e5b9
        z = (z ^ (z >> 27)) &* 0x94d049bb133111eb
        return z ^ (z >> 31)
    }
    mutating func pick(_ bound: Int) -> Int { Int.random(in: 0..<bound, using: &self) }
}

public struct GameState: Codable, Equatable, Sendable {
    public var id = UUID()
    public var level = 1
    public var questionID = ""
    // Optional so saves made before answer shuffling still decode in their original order.
    public var answerOrder: [Int]?
    public var phase = GamePhase.question
    public var selectedAnswer: Int?
    public var eliminated = Set<Int>()
    public var usedLifelines = Set<Lifeline>()
    public var visited = [String]()
    public var audience: [Int]?
    public var prize = 0
    public var banked = 0
    public var random: RandomState
    public var isFinished: Bool { [.lost, .won, .walkedAway].contains(phase) }
    public var visibleAnswers: [Int] { (0..<4).filter { !eliminated.contains($0) } }
    public var audiencePercentages: [Int]? {
        guard let audience else { return nil }
        // Redistribute the existing poll among surviving answers, including older saves.
        let indices = visibleAnswers
        let total = indices.reduce(0) { $0 + audience[$1] }
        var result = Array(repeating: 0, count: 4)
        guard !indices.isEmpty else { return result }
        for index in indices { result[index] = total > 0 ? audience[index] * 100 / total : 100 / indices.count }
        let remainderOrder = indices.sorted {
            let a = total > 0 ? audience[$0] * 100 % total : 0
            let b = total > 0 ? audience[$1] * 100 % total : 0
            return a == b ? $0 < $1 : a > b
        }
        for index in remainderOrder.prefix(100 - result.reduce(0, +)) { result[index] += 1 }
        return result
    }
}

public struct GameArchive: Codable, Equatable, Sendable {
    public var schemaVersion = 1
    public var game: GameState?
    public var highScore = 0
    public var recent = [Int: [String]]()
    public var lastCorrectPosition: Int?
    // Optional for lossless decoding of every pre-statistics archive.
    public var statistics: GameStatistics?
    public init() {}
    public var recordsOnly: GameArchive {
        var saved = self
        saved.game = nil
        return saved
    }
}

public struct GameEngine: Sendable {
    public let bank: QuestionBank
    public private(set) var archive: GameArchive
    public var game: GameState? { archive.game }
    public var question: Question? {
        guard let game, let original = bank.question(game.questionID) else { return nil }
        guard let order = game.answerOrder else { return original }
        guard order.count == 4, Set(order) == Set(0..<4),
              let correct = order.firstIndex(of: original.correctIndex) else { return nil }
        return Question(id: original.id, level: original.level, difficulty: original.difficulty,
                        category: original.category, text: original.text,
                        answers: order.map { original.answers[$0] }, correctIndex: correct,
                        explanation: original.explanation, source: original.source)
    }
    public var guarantee: Int {
        guard let game else { return 0 }
        if game.phase == .won { return 1_000_000 }
        let completed = game.phase == .correct ? game.level : game.level - 1
        return completed >= 10 ? 32000 : completed >= 5 ? 1000 : 0
    }

    public init(bank: QuestionBank, archive: GameArchive = GameArchive()) throws {
        try bank.validate()
        self.bank = bank
        self.archive = archive
        try validateArchive()
    }

    public mutating func newGame(seed: UInt64 = UInt64.random(in: 0...UInt64.max)) throws {
        var state = GameState(random: RandomState(seed: seed))
        try drawQuestion(into: &state)
        archive.game = state
        var statistics = archive.statistics ?? GameStatistics()
        statistics.gamesStarted += 1
        statistics.highestLevel = max(statistics.highestLevel, 1)
        archive.statistics = statistics
    }

    @discardableResult public mutating func select(_ answer: Int) -> Bool {
        guard var state = game, state.phase == .question, (0...3).contains(answer), !state.eliminated.contains(answer) else { return false }
        state.selectedAnswer = answer
        archive.game = state
        return true
    }

    @discardableResult public mutating func answer(_ index: Int) -> Bool {
        guard select(index) else { return false }
        return lockAnswer()
    }

    @discardableResult public mutating func answerAndAdvance(_ index: Int, questionID: String) throws -> AnswerOutcome? {
        guard let question, question.id == questionID, game?.phase == .question else { return nil }
        // Commit scoring and the next draw together; stale answer controls cannot score a different question.
        var updated = self
        guard updated.answer(index), let scored = updated.game else { return nil }
        let outcome = AnswerOutcome(question: question, phase: scored.phase, level: scored.level, prize: scored.prize, banked: scored.banked)
        if scored.phase == .correct { guard try updated.nextQuestion() else { throw GameError.noQuestion } }
        try updated.validateArchive()
        self = updated
        return outcome
    }

    @discardableResult public mutating func returnToMenu() -> Bool {
        guard game?.isFinished == true else { return false }
        archive.game = nil
        return true
    }

    @discardableResult public mutating func lockAnswer() -> Bool {
        guard var state = game, state.phase == .question, let selected = state.selectedAnswer, let q = question else { return false }
        var statistics = archive.statistics ?? GameStatistics()
        statistics.record(question: q, correct: selected == q.correctIndex)
        if selected == q.correctIndex {
            state.prize = bank.ladder[state.level - 1]
            archive.highScore = max(archive.highScore, state.prize)
            state.phase = state.level == 15 ? .won : .correct
            if state.phase == .won { state.banked = state.prize }
        } else {
            state.banked = guarantee
            state.phase = .lost
        }
        archive.game = state
        if state.isFinished { statistics.finish(won: state.phase == .won, banked: state.banked) }
        archive.statistics = statistics
        return true
    }

    @discardableResult public mutating func nextQuestion() throws -> Bool {
        guard var state = game, state.phase == .correct, state.level < 15 else { return false }
        state.level += 1
        try drawQuestion(into: &state)
        archive.game = state
        var statistics = archive.statistics ?? GameStatistics()
        statistics.highestLevel = max(statistics.highestLevel, state.level)
        archive.statistics = statistics
        return true
    }

    @discardableResult public mutating func walkAway() -> Bool {
        guard var state = game, !state.isFinished else { return false }
        state.banked = state.prize
        state.phase = .walkedAway
        archive.game = state
        var statistics = archive.statistics ?? GameStatistics()
        statistics.finish(won: false, banked: state.banked)
        archive.statistics = statistics
        return true
    }

    @discardableResult public mutating func use(_ lifeline: Lifeline) throws -> Bool {
        guard var state = game, state.phase == .question, !state.usedLifelines.contains(lifeline), let q = question else { return false }
        switch lifeline {
        case .fiftyFifty:
            let wrong = (0...3).filter { $0 != q.correctIndex }
            let kept = wrong[state.random.pick(wrong.count)]
            state.eliminated = Set(wrong.filter { $0 != kept })
            if let selected = state.selectedAnswer, state.eliminated.contains(selected) { state.selectedAnswer = nil }
        case .audience:
            state.audience = audiencePoll(level: state.level, correct: q.correctIndex, random: &state.random)
        case .freePass:
            try drawQuestion(into: &state)
        }
        state.usedLifelines.insert(lifeline)
        archive.game = state
        var statistics = archive.statistics ?? GameStatistics()
        statistics.lifelines[lifeline.rawValue, default: 0] += 1
        archive.statistics = statistics
        return true
    }

    public mutating func resetHighScore() { archive.highScore = 0 }

    private mutating func drawQuestion(into state: inout GameState) throws {
        let pool = bank.questions.filter { $0.level == state.level }
        let eligible = pool.filter { !state.visited.contains($0.id) }
        guard !eligible.isEmpty else { throw GameError.noQuestion }
        var history = archive.recent[state.level, default: []]
        let fresh = eligible.filter { !history.contains($0.id) }
        let chosen: Question
        if !fresh.isEmpty { chosen = fresh[state.random.pick(fresh.count)] }
        else { chosen = eligible.min { (history.firstIndex(of: $0.id) ?? Int.max) < (history.firstIndex(of: $1.id) ?? Int.max) }! }
        state.questionID = chosen.id
        let positions = (0..<4).filter { $0 != archive.lastCorrectPosition }
        let position = positions[state.random.pick(positions.count)]
        var order = (0..<4).filter { $0 != chosen.correctIndex }.shuffled(using: &state.random)
        order.insert(chosen.correctIndex, at: position)
        state.answerOrder = order
        archive.lastCorrectPosition = position
        state.visited.append(chosen.id)
        state.phase = .question
        state.selectedAnswer = nil
        state.eliminated = []
        state.audience = nil
        history.removeAll { $0 == chosen.id }
        history.append(chosen.id)
        let capacity = pool.count <= 3 ? pool.count - 1 : pool.count - 2
        archive.recent[state.level] = Array(history.suffix(max(0, capacity)))
    }

    private func audiencePoll(level: Int, correct: Int, random: inout RandomState) -> [Int] {
        let index = level - 1
        let base = index < 4 ? 62 : index < 8 ? 48 : index < 12 ? 38 : 30
        var leader = correct
        if index >= 10 && random.pick(5) == 0 {
            let wrong = (0...3).filter { $0 != correct }
            leader = wrong[random.pick(3)]
        }
        var votes = Array(repeating: 0, count: 4)
        votes[leader] = min(78, base + random.pick(9))
        var remaining = 100 - votes[leader]
        for i in 0...3 where i != leader {
            let slots = ((i + 1)..<4).filter { $0 != leader }.count
            if slots == 0 { votes[i] = remaining }
            else {
                votes[i] = max(1, min(remaining - slots, remaining / (slots + 1) + random.pick(9) - 4))
                remaining -= votes[i]
            }
        }
        return votes
    }

    public func validateArchive() throws {
        guard archive.schemaVersion == 1, ([0] + bank.ladder).contains(archive.highScore) else { throw GameError.invalidSave }
        if let statistics = archive.statistics, !statistics.isValid { throw GameError.invalidSave }
        if let position = archive.lastCorrectPosition, !(0..<4).contains(position) { throw GameError.invalidSave }
        for (level, ids) in archive.recent {
            guard (1...15).contains(level), Set(ids).count == ids.count,
                  ids.allSatisfy({ bank.question($0)?.level == level }) else { throw GameError.invalidSave }
        }
        guard let g = game else { return }
        guard (1...15).contains(g.level), let q = question, q.level == g.level,
              g.visited.last == g.questionID, Set(g.visited).count == g.visited.count,
              g.visited.allSatisfy({ bank.question($0) != nil }),
              g.visited.count == g.level + (g.usedLifelines.contains(.freePass) ? 1 : 0),
              g.eliminated.allSatisfy({ (0...3).contains($0) && $0 != q.correctIndex }),
              g.eliminated.isEmpty || (g.eliminated.count == 2 && g.usedLifelines.contains(.fiftyFifty)),
              g.selectedAnswer.map({ (0...3).contains($0) && !g.eliminated.contains($0) }) ?? true,
              ([0] + bank.ladder).contains(g.prize), ([0] + bank.ladder).contains(g.banked)
        else { throw GameError.invalidSave }
        if let poll = g.audience {
            guard g.usedLifelines.contains(.audience), poll.count == 4, poll.allSatisfy({ (0...100).contains($0) }), poll.reduce(0, +) == 100 else { throw GameError.invalidSave }
        }
        let previous = g.level == 1 ? 0 : bank.ladder[g.level - 2]
        switch g.phase {
        case .question: guard g.prize == previous, g.banked == 0 else { throw GameError.invalidSave }
        case .correct: guard g.level < 15, g.selectedAnswer == q.correctIndex, g.prize == bank.ladder[g.level - 1], g.banked == 0 else { throw GameError.invalidSave }
        case .won: guard g.level == 15, g.selectedAnswer == q.correctIndex, g.prize == 1_000_000, g.banked == g.prize else { throw GameError.invalidSave }
        case .lost: guard let answer = g.selectedAnswer, answer != q.correctIndex, g.prize == previous, g.banked == (g.level > 10 ? 32000 : g.level > 5 ? 1000 : 0) else { throw GameError.invalidSave }
        case .walkedAway: guard g.banked == g.prize, g.prize == previous || g.prize == bank.ladder[g.level - 1] else { throw GameError.invalidSave }
        }
    }
}
