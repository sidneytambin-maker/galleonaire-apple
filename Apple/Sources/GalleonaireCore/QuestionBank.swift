import Foundation

public struct Question: Codable, Equatable, Identifiable, Sendable {
    public let id: String
    public let level: Int
    public let difficulty: Int
    public let category: String
    public let text: String
    public let answers: [String]
    public let correctIndex: Int
    public let explanation: String
    public let source: String
}

public enum GameError: Error, LocalizedError, Equatable {
    case invalidBank(String), invalidSave, noQuestion
    public var errorDescription: String? {
        switch self {
        case .invalidBank(let reason): return "The question pack could not be loaded: \(reason)."
        case .invalidSave: return "The saved game could not be restored. It has been kept for recovery."
        case .noQuestion: return "No unused question is available at this level."
        }
    }
}

public struct QuestionBank: Codable, Sendable {
    public let schemaVersion: Int
    public let ladder: [Int]
    public let questions: [Question]
    public static let prizeLadder = [100, 200, 300, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 125000, 250000, 500000, 1000000]

    public static func bundled() throws -> Self {
        guard let url = Bundle.module.url(forResource: "questions", withExtension: "json") else {
            throw GameError.invalidBank("missing resource")
        }
        let bank = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        try bank.validate()
        return bank
    }

    public func question(_ id: String) -> Question? { questions.first { $0.id == id } }

    public func validate() throws {
        guard schemaVersion == 1, ladder == Self.prizeLadder else { throw GameError.invalidBank("unsupported rules") }
        var ids = Set<String>(), texts = Set<String>()
        func normalize(_ value: String) -> String {
            value.lowercased().split(whereSeparator: { $0.isWhitespace }).joined(separator: " ")
        }
        for q in questions {
            let answers = q.answers.map(normalize)
            guard !q.id.isEmpty, ids.insert(q.id).inserted,
                  !normalize(q.text).isEmpty, texts.insert(normalize(q.text)).inserted,
                  (1...15).contains(q.level), (1...15).contains(q.difficulty),
                  answers.count == 4, Set(answers).count == 4, answers.allSatisfy({ !$0.isEmpty }),
                  (0...3).contains(q.correctIndex), !q.explanation.isEmpty, !q.source.isEmpty
            else { throw GameError.invalidBank(q.id) }
        }
        for level in 1...15 where questions.filter({ $0.level == level }).count < 2 {
            throw GameError.invalidBank("level \(level) needs at least two questions")
        }
    }
}
