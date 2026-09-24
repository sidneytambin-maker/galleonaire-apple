import Foundation

public struct AnswerRecord: Codable, Equatable, Sendable {
    public var answered = 0
    public var correct = 0
    public var accuracy: Int { answered == 0 ? 0 : Int((Double(correct) / Double(answered) * 100).rounded()) }
    public var isValid: Bool { answered >= 0 && correct >= 0 && correct <= answered }
    mutating func record(_ success: Bool) { answered += 1; if success { correct += 1 } }
}

/// Device-local counters from the first statistics-enabled release. Historical play is not guessed.
public struct GameStatistics: Codable, Equatable, Sendable {
    public var gamesStarted = 0
    public var gamesFinished = 0
    public var gamesWon = 0
    public var answers = AnswerRecord()
    public var highestLevel = 0
    public var bestBanked = 0
    public var currentStreak = 0
    public var bestStreak = 0
    public var lifelines: [String: Int] = [:]
    public var levels: [Int: AnswerRecord] = [:]
    public var categories: [String: AnswerRecord] = [:]
    public init() {}
    public var lifelinesUsed: Int { lifelines.values.reduce(0, +) }
    public var isValid: Bool {
        gamesStarted >= 0 && gamesFinished >= 0 && gamesWon >= 0 && gamesWon <= gamesFinished &&
        answers.isValid && (0...15).contains(highestLevel) &&
        ([0] + QuestionBank.prizeLadder).contains(bestBanked) &&
        currentStreak >= 0 && currentStreak <= bestStreak && bestStreak <= answers.correct &&
        lifelines.allSatisfy { Lifeline(rawValue: $0.key) != nil && $0.value >= 0 } &&
        levels.allSatisfy { (1...15).contains($0.key) && $0.value.isValid } &&
        categories.allSatisfy { !$0.key.isEmpty && $0.value.isValid } &&
        levels.values.reduce(0) { $0 + $1.answered } == answers.answered &&
        levels.values.reduce(0) { $0 + $1.correct } == answers.correct &&
        categories.values.reduce(0) { $0 + $1.answered } == answers.answered &&
        categories.values.reduce(0) { $0 + $1.correct } == answers.correct
    }
    mutating func record(question: Question, correct: Bool) {
        answers.record(correct)
        levels[question.level, default: AnswerRecord()].record(correct)
        categories[question.category, default: AnswerRecord()].record(correct)
        currentStreak = correct ? currentStreak + 1 : 0
        bestStreak = max(bestStreak, currentStreak)
    }
    mutating func finish(won: Bool, banked: Int) {
        gamesFinished += 1
        if won { gamesWon += 1 }
        bestBanked = max(bestBanked, banked)
    }
}
