import Foundation

public enum ExamSubject: String, Codable, CaseIterable, Identifiable, Sendable {
    case characters, spells, potions, transformations, creatures, education, history, objects, competitions, films
    public var id: String { rawValue }
    public var name: String {
        switch self {
        case .characters: return "Characters and Magical Families"
        case .spells: return "Charms, Spells and Defence"
        case .potions: return "Potions, Herbology and Magical Healing"
        case .transformations: return "Transfiguration and Magical Transformations"
        case .creatures: return "Magical Creatures and Beasts"
        case .education: return "Hogwarts and Wizarding Education"
        case .history: return "History of Magic and Wizarding Society"
        case .objects: return "Magical Objects, Wands and Places"
        case .competitions: return "Quidditch, Tournaments and Challenges"
        case .films: return "Harry Potter Films"
        }
    }
}

public enum ExamQualification: String, Codable, CaseIterable, Identifiable, Sendable {
    case owl, newt
    public var id: String { rawValue }
    public var name: String { self == .owl ? "O.W.L." : "N.E.W.T." }
    public var count: Int { self == .owl ? 20 : 50 }
    public var difficulty: ExamDifficulty { self == .owl ? .intermediate : .expert }
}

public enum ExamDifficulty: String, Codable, Sendable { case intermediate, expert }
public enum ExamTiming: String, Codable, CaseIterable, Identifiable, Sendable {
    case standard, extended, untimed
    public var id: String { rawValue }
    public var name: String {
        switch self {
        case .standard: return "Standard: 25 minutes"
        case .extended: return "Extended: 37 minutes 30 seconds"
        case .untimed: return "Untimed"
        }
    }
    public var duration: TimeInterval? {
        switch self { case .standard: return 1500; case .extended: return 2250; case .untimed: return nil }
    }
}

public enum ExamGrade: String, Codable, CaseIterable, Sendable {
    case outstanding = "Outstanding", exceeds = "Exceeds Expectations", acceptable = "Acceptable"
    case poor = "Poor", dreadful = "Dreadful", troll = "Troll"
    public var passed: Bool { [.outstanding, .exceeds, .acceptable].contains(self) }
    public static func grade(score: Int, qualification: ExamQualification) -> Self {
        let boundaries = qualification == .owl ? [18, 15, 12, 9, 6] : [45, 38, 30, 23, 15]
        for (index, boundary) in boundaries.enumerated() where score >= boundary { return allCases[index] }
        return .troll
    }
}

public struct QuestionClassification: Codable, Equatable, Sendable {
    public let questionID: String
    public let subject: ExamSubject
    public let difficulty: ExamDifficulty?
    public let eligible: Bool
    public let rationale: String
}

public struct ExamItem: Codable, Equatable, Identifiable, Sendable {
    public let question: Question
    public let subject: ExamSubject
    public let difficulty: ExamDifficulty
    public let conflictKeys: [String]
    public var id: String { question.id }
}

public struct ExamBank: Codable, Sendable {
    public let schemaVersion: Int
    public let classifications: [QuestionClassification]
    public let items: [ExamItem]
    public static func bundled() throws -> Self {
        guard let url = Bundle.module.url(forResource: "exam-bank", withExtension: "json") else {
            throw GameError.invalidBank("missing exam bank")
        }
        let bank = try JSONDecoder().decode(Self.self, from: Data(contentsOf: url))
        try bank.validate()
        return bank
    }
    public func pool(_ subject: ExamSubject, _ qualification: ExamQualification) -> [ExamItem] {
        items.filter { $0.subject == subject && $0.difficulty == qualification.difficulty }
    }
    public func validate() throws {
        guard schemaVersion == 1, Set(classifications.map(\.questionID)).count == classifications.count,
              Set(items.map(\.id)).count == items.count else { throw GameError.invalidBank("exam identifiers") }
        for item in items {
            let q = item.question
            guard q.answers.count == 4, Set(q.answers).count == 4, (0..<4).contains(q.correctIndex),
                  !q.text.isEmpty, !q.explanation.isEmpty, !q.source.isEmpty, !item.conflictKeys.isEmpty,
                  Set(item.conflictKeys).count == item.conflictKeys.count else { throw GameError.invalidBank(item.id) }
        }
        for subject in ExamSubject.allCases {
            for qualification in ExamQualification.allCases {
                let candidates = pool(subject, qualification)
                guard candidates.count >= qualification.count else { throw GameError.invalidBank("incomplete \(subject.name) \(qualification.name) paper") }
                // Editorial pools must be mutually compatible. This guarantees a full paper for every shuffle.
                let keys = candidates.flatMap(\.conflictKeys)
                guard Set(keys).count == keys.count else { throw GameError.invalidBank("conflicting \(subject.name) questions") }
            }
        }
    }
}

public struct ExamPaperQuestion: Codable, Equatable, Identifiable, Sendable {
    public let item: ExamItem
    public let answerOrder: [Int]
    public var answer: Int?
    public var id: String { item.id }
    public var correct: Bool { answer.map { answerOrder[$0] == item.question.correctIndex } ?? false }
}

public struct ExamAttempt: Codable, Equatable, Identifiable, Sendable {
    public let id: UUID
    public let subject: ExamSubject
    public let qualification: ExamQualification
    public let timing: ExamTiming
    public let startedAt: Date
    public let deadline: Date?
    public var questions: [ExamPaperQuestion]
    public var currentIndex: Int
    public var warnedMinutes: Set<Int>
    public var submittedAt: Date?
    public var expired: Bool
    public var unanswered: Int { questions.filter { $0.answer == nil }.count }
    public var score: Int { questions.filter(\.correct).count }
    public var percentage: Int { score * 100 / qualification.count }
    public var grade: ExamGrade { .grade(score: score, qualification: qualification) }
    public var summary: String {
        "\(subject.name). \(qualification.name). \(score) out of \(qualification.count), \(percentage) percent. \(grade.rawValue). \(grade.passed ? "Pass" : "Fail")."
    }
    public func remaining(at now: Date) -> TimeInterval? { deadline.map { max(0, $0.timeIntervalSince(now)) } }
    public var isValid: Bool {
        questions.count == qualification.count && Set(questions.map(\.id)).count == questions.count &&
        questions.indices.contains(currentIndex) && warnedMinutes.isSubset(of: [5, 1]) &&
        (qualification != .owl || timing == .untimed) &&
        deadline == timing.duration.map { startedAt.addingTimeInterval($0) } &&
        questions.allSatisfy { q in
            q.item.subject == subject && q.item.difficulty == qualification.difficulty &&
            q.item.question.answers.count == 4 && (0..<4).contains(q.item.question.correctIndex) &&
            q.answerOrder.count == 4 && Set(q.answerOrder) == Set(0..<4) &&
            (q.answer.map { (0..<4).contains($0) } ?? true)
        }
    }
}

public struct ExamArchive: Codable, Equatable, Sendable {
    public var schemaVersion = 1
    public var active: ExamAttempt?
    public var results: [ExamAttempt] = []
    public init() {}
    public func validate() throws {
        guard schemaVersion == 1, active.map({ $0.isValid && $0.submittedAt == nil }) ?? true,
              results.allSatisfy({ $0.isValid && $0.submittedAt != nil }),
              Set(results.map(\.id)).count == results.count,
              !results.contains(where: { $0.id == active?.id }) else { throw GameError.invalidSave }
    }
    public func best(subject: ExamSubject, qualification: ExamQualification) -> ExamAttempt? {
        results.filter { $0.subject == subject && $0.qualification == qualification }.max { $0.score < $1.score }
    }
}

/// All mutations take an explicit clock. The app commits a copy atomically before publishing it.
public struct ExamEngine: Sendable {
    public private(set) var archive: ExamArchive
    public init(archive: ExamArchive = ExamArchive()) throws { try archive.validate(); self.archive = archive }
    public mutating func begin(bank: ExamBank, subject: ExamSubject, qualification: ExamQualification,
                               timing: ExamTiming, now: Date, seed: UInt64) throws {
        guard archive.active == nil else { throw GameError.invalidSave }
        try bank.validate()
        var random = RandomState(seed: seed)
        let pool = bank.pool(subject, qualification)
        let previous = archive.results.last { $0.subject == subject && $0.qualification == qualification }?.questions.map(\.id)
        var selection = Array(pool.shuffled(using: &random).prefix(qualification.count))
        // Rejection sampling retains random selection while excluding the previous exact order.
        while selection.map(\.id) == previous {
            selection = Array(pool.shuffled(using: &random).prefix(qualification.count))
        }
        let questions = selection.map {
            ExamPaperQuestion(item: $0, answerOrder: Array(0..<4).shuffled(using: &random), answer: nil)
        }
        let actualTiming = qualification == .owl ? ExamTiming.untimed : timing
        archive.active = ExamAttempt(id: UUID(), subject: subject, qualification: qualification, timing: actualTiming,
                                     startedAt: now, deadline: actualTiming.duration.map { now.addingTimeInterval($0) },
                                     questions: questions, currentIndex: 0, warnedMinutes: [], submittedAt: nil, expired: false)
    }
    @discardableResult public mutating func expire(now: Date) -> UUID? {
        guard let a = archive.active, let deadline = a.deadline, now >= deadline else { return nil }
        return submit(id: a.id, now: now)
    }
    @discardableResult public mutating func answer(_ answer: Int?, questionID: String, attemptID: UUID, now: Date) -> Bool {
        if expire(now: now) != nil { return false }
        guard var a = archive.active, a.id == attemptID, a.questions[a.currentIndex].id == questionID,
              answer.map({ (0..<4).contains($0) }) ?? true else { return false }
        a.questions[a.currentIndex].answer = answer
        archive.active = a
        return true
    }
    public mutating func navigate(to index: Int, now: Date) {
        guard expire(now: now) == nil, var a = archive.active, a.questions.indices.contains(index) else { return }
        a.currentIndex = index; archive.active = a
    }
    @discardableResult public mutating func submit(id: UUID, now: Date) -> UUID? {
        if archive.results.contains(where: { $0.id == id }) { return id }
        guard var a = archive.active, a.id == id else { return nil }
        a.expired = a.deadline.map { now >= $0 } ?? false
        a.submittedAt = a.expired ? a.deadline : now
        archive.results.append(a)
        archive.active = nil
        return id
    }
    public mutating func warning(now: Date) -> String? {
        guard expire(now: now) == nil, var a = archive.active, let remaining = a.remaining(at: now) else { return nil }
        let minutes = remaining <= 60 ? 1 : remaining <= 300 ? 5 : 0
        guard minutes > 0, !a.warnedMinutes.contains(minutes) else { return nil }
        a.warnedMinutes.insert(minutes)
        if minutes == 1 { a.warnedMinutes.insert(5) }
        archive.active = a
        return minutes == 1 ? "One minute remaining in this exam." : "Five minutes remaining in this exam."
    }
}

public struct ExamPersistence {
    public let directory: URL
    public init(directory: URL) { self.directory = directory }
    public func load() throws -> ExamArchive {
        let url = directory.appendingPathComponent("exams.json")
        guard FileManager.default.fileExists(atPath: url.path) else { return ExamArchive() }
        let archive = try JSONDecoder().decode(ExamArchive.self, from: Data(contentsOf: url))
        try archive.validate()
        return archive
    }
    public func save(_ archive: ExamArchive) throws {
        try archive.validate()
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        try JSONEncoder().encode(archive).write(to: directory.appendingPathComponent("exams.json"), options: .atomic)
    }
}
