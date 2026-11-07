import Foundation

public enum TopicPerformance {
    // Read once; Classic's stored question content, difficulty and prize level remain unchanged.
    private static let reviewed: [String: ExamSubject] = {
        guard let url = Bundle.module.url(forResource: "exam-bank", withExtension: "json"),
              let data = try? Data(contentsOf: url), let bank = try? JSONDecoder().decode(ExamBank.self, from: data) else { return [:] }
        return Dictionary(bank.classifications.map { ($0.questionID, $0.subject) } + bank.items.map { ($0.id, $0.subject) }, uniquingKeysWith: { first, _ in first })
    }()
    public static func subject(questionID: String) -> ExamSubject? { reviewed[questionID] }
    private static let legacy: [String: ExamSubject] = {
        guard let url = Bundle.module.url(forResource: "questions", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let original = try? JSONDecoder().decode(QuestionBank.self, from: data) else { return [:] }
        var candidates: [String: Set<ExamSubject>] = [:]
        for question in original.questions {
            if let subject = reviewed[question.id] { candidates[question.category, default: []].insert(subject) }
        }
        // A historical category is safe only when every reviewed question in it agrees.
        return candidates.reduce(into: [:]) { result, entry in
            if entry.value.count == 1 { result[entry.key] = entry.value.first }
        }
    }()
    public static func legacySubject(_ label: String) -> ExamSubject? {
        if let exact = ExamSubject.allCases.first(where: { $0.name == label }) { return exact }
        return legacy[label]
    }
    public static func grouped(_ categories: [String: AnswerRecord]) -> (subjects: [ExamSubject: AnswerRecord], earlier: [String: AnswerRecord]) {
        var subjects: [ExamSubject: AnswerRecord] = [:]
        var earlier: [String: AnswerRecord] = [:]
        for (label, record) in categories {
            if let subject = legacySubject(label) {
                var total = subjects[subject, default: AnswerRecord()]
                total.answered += record.answered; total.correct += record.correct
                subjects[subject] = total
            } else { earlier[label] = record }
        }
        return (subjects, earlier)
    }
}
