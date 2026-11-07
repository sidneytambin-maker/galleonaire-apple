import SwiftUI
import GalleonaireCore

@MainActor final class ExamStore: ObservableObject {
    @Published private(set) var engine: ExamEngine?
    @Published private(set) var bank: ExamBank?
    @Published var errorMessage: String?
    @Published var resultID: UUID?
    private let persistence: ExamPersistence
    var now: () -> Date = Date.init
    var active: ExamAttempt? { engine?.archive.active }
    var results: [ExamAttempt] { engine?.archive.results ?? [] }

    init() {
        var directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("Galleonaire", isDirectory: true)
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing") {
            directory = directory.appendingPathComponent("UITesting", isDirectory: true)
        }
        #endif
        persistence = ExamPersistence(directory: directory)
        do {
            engine = try ExamEngine(archive: persistence.load())
            checkDeadline()
        } catch {
            errorMessage = "Exam records could not be loaded. The existing file has been kept. \(error.localizedDescription)"
        }
        do { bank = try ExamBank.bundled() }
        catch { errorMessage = "New exams are unavailable. Saved papers remain available. \(error.localizedDescription)" }
        #if DEBUG
        installTestFixture()
        #endif
    }
    #if DEBUG
    private func installTestFixture() {
        let args = ProcessInfo.processInfo.arguments
        guard args.contains("--ui-testing"), args.contains("--reset-test-game"), let bank,
              args.contains("--exam-fixture-ready") || args.contains("--exam-fixture-expired") else { return }
        do {
            let expired = args.contains("--exam-fixture-expired")
            var fixture = try ExamEngine()
            let start = Date().addingTimeInterval(expired ? -1600 : 0)
            try fixture.begin(bank: bank, subject: .transformations, qualification: expired ? .newt : .owl,
                              timing: expired ? .standard : .untimed, now: start, seed: 6706)
            let paper = fixture.archive.active!
            for index in 0..<19 {
                fixture.navigate(to: index, now: start)
                let question = paper.questions[index]
                _ = fixture.answer(question.answerOrder.firstIndex(of: question.item.question.correctIndex),
                                   questionID: question.id, attemptID: paper.id, now: start)
            }
            fixture.navigate(to: 19, now: start)
            try persistence.save(fixture.archive)
            engine = fixture; resultID = nil
        } catch { errorMessage = "Exam fixture failed: \(error.localizedDescription)" }
    }
    #endif
    @discardableResult private func transact(_ change: (inout ExamEngine) throws -> Void) -> Bool {
        guard var updated = engine else { return false }
        let previousAttempt = updated.archive.active?.id
        do {
            try change(&updated)
            if updated.archive != engine?.archive { try persistence.save(updated.archive) }
            engine = updated
            if let previousAttempt, updated.archive.results.contains(where: { $0.id == previousAttempt }) {
                resultID = previousAttempt
            }
            return true
        } catch {
            errorMessage = "The exam change could not be saved. Your previously saved answers have been kept. \(error.localizedDescription)"
            return false
        }
    }
    func begin(subject: ExamSubject, qualification: ExamQualification, timing: ExamTiming) -> Bool {
        guard let bank else { return false }
        resultID = nil
        return transact { try $0.begin(bank: bank, subject: subject, qualification: qualification, timing: timing,
                                       now: now(), seed: UInt64.random(in: 0...UInt64.max)) }
    }
    func checkDeadline(announce: Bool = false) {
        let time = now()
        var completed: UUID?
        var warning: String?
        if transact({ e in
            completed = e.expire(now: time)
            if announce { warning = e.warning(now: time) }
        }) {
            if let completed { resultID = completed }
            if let warning { AccessibilityNotification.Announcement(warning).post() }
        }
    }
    func answer(_ index: Int?, questionID: String, attemptID: UUID) {
        var accepted = false
        let time = now()
        if transact({ e in accepted = e.answer(index, questionID: questionID, attemptID: attemptID, now: time) }) {
            if accepted { AccessibilityNotification.Announcement(index == nil ? "Answer cleared" : "Answer recorded").post() }
            else if results.contains(where: { $0.id == attemptID }) { resultID = attemptID }
        }
    }
    func navigate(_ index: Int) {
        checkDeadline()
        _ = transact { $0.navigate(to: index, now: now()) }
    }
    func submit(_ id: UUID) {
        var completed: UUID?
        if transact({ completed = $0.submit(id: id, now: now()) }), let completed { resultID = completed }
    }
}
