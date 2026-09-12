import SwiftUI
import Combine
import GalleonaireCore

@MainActor final class GameStore: ObservableObject {
    @Published private(set) var engine: GameEngine?
    @Published private(set) var settings = GameSettings()
    @Published private(set) var lastAnswer: AnswerOutcome?
    @Published var errorMessage: String?
    @Published private(set) var recoveryRequired = false
    let feedback = GameFeedback()
    private let persistence: GamePersistence
    private let preferences: UserDefaults
    private let deviceID: String
    private var sync: SettingsSync?

    init() {
        var directory = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0].appendingPathComponent("Galleonaire", isDirectory: true)
        #if DEBUG
        let testing = ProcessInfo.processInfo.arguments.contains("--ui-testing")
        if testing {
            directory = directory.appendingPathComponent("UITesting", isDirectory: true)
            if ProcessInfo.processInfo.arguments.contains("--reset-test-game") { try? FileManager.default.removeItem(at: directory) }
        }
        preferences = testing ? UserDefaults(suiteName: "com.sidneytambin.galleonaire.uitesting")! : .standard
        if testing && ProcessInfo.processInfo.arguments.contains("--reset-test-game") {
            preferences.removePersistentDomain(forName: "com.sidneytambin.galleonaire.uitesting")
        }
        #else
        preferences = .standard
        #endif
        persistence = GamePersistence(directory: directory)
        deviceID = preferences.string(forKey: "deviceID") ?? UUID().uuidString
        preferences.set(deviceID, forKey: "deviceID")
        if let data = preferences.data(forKey: "settings"), let saved = try? JSONDecoder().decode(GameSettings.self, from: data), saved.isValid { settings = saved }
        do {
            let bank = try QuestionBank.bundled()
            do {
                let saved = try persistence.load()
                engine = try GameEngine(bank: bank, archive: saved.recordsOnly)
                if saved.game != nil {
                    do { try persistence.save(saved.recordsOnly) }
                    catch { errorMessage = "Your previous game was cleared for this launch, but the saved file could not be updated. Your highest prize has been kept." }
                }
            }
            catch {
                recoveryRequired = true
                engine = try GameEngine(bank: bank)
                errorMessage = "Your saved records could not be read. They will be preserved before a new game starts."
            }
        } catch { errorMessage = error.localizedDescription }
        feedback.settings = settings
        sync = SettingsSync { [weak self] incoming in self?.receive(incoming) }
        sync?.start(settings)
    }

    var game: GameState? { engine?.game }
    var question: Question? { engine?.question }
    var highScore: Int { engine?.archive.highScore ?? 0 }
    var guarantee: Int { engine?.guarantee ?? 0 }

    @discardableResult private func transact(_ change: (inout GameEngine) throws -> Bool) -> Bool {
        guard var updated = engine else { return false }
        do {
            if recoveryRequired { try persistence.preserveUnreadableSave() }
            guard try change(&updated) else { return false }
            try updated.validateArchive()
            try persistence.save(updated.archive.recordsOnly)
            engine = updated
            recoveryRequired = false
            return true
        } catch {
            errorMessage = "The change was not saved. \(error.localizedDescription) Your previous game has been kept."
            return false
        }
    }

    func newGame() {
        if transact({ try $0.newGame(); return true }) { lastAnswer = nil; feedback.play(.nextQuestion) }
    }
    @discardableResult func answer(_ index: Int, questionID: String) -> Bool {
        var outcome: AnswerOutcome?
        guard transact({ engine in
            outcome = try engine.answerAndAdvance(index, questionID: questionID)
            return outcome != nil
        }), let outcome else { return false }
        lastAnswer = outcome
        resultFeedback(outcome)
        return true
    }
    @discardableResult func returnToMenu() -> Bool {
        guard transact({ $0.returnToMenu() }) else { return false }
        lastAnswer = nil
        return true
    }
    private func resultFeedback(_ outcome: AnswerOutcome) {
        if outcome.phase == .won { feedback.play(.victory) }
        else if outcome.phase == .lost { feedback.play(.incorrect) }
        else if outcome.prize == 32000 { feedback.play(.majorMilestone) }
        else if outcome.prize == 1000 { feedback.play(.milestone) }
        else if outcome.phase == .correct { feedback.play(.correct) }
    }
    @discardableResult func use(_ lifeline: Lifeline) -> Bool {
        guard transact({ try $0.use(lifeline) }) else { return false }
        lastAnswer = nil
        switch lifeline {
        case .fiftyFifty: feedback.play(.fiftyFifty)
        case .audience: feedback.play(.audience)
        case .freePass: feedback.play(.swapQuestion)
        }
        return true
    }
    func walkAway() { if transact({ $0.walkAway() }) { feedback.play(.milestone) } }
    func resetHighScore() {
        if transact({ $0.resetHighScore(); return true }) {
            AccessibilityNotification.Announcement("Highest prize reset. Your current game is kept.").post()
        }
    }
    func set(_ key: SettingKey, value: Int) {
        settings.set(key, value: value, author: deviceID)
        persistSettings()
        sync?.publish(settings)
    }
    private func receive(_ incoming: GameSettings) {
        if settings.merge(incoming) { persistSettings(); sync?.publish(settings) }
    }
    private func persistSettings() {
        guard let encoded = try? JSONEncoder().encode(settings) else { return }
        preferences.set(encoded, forKey: "settings")
        feedback.settings = settings
        feedback.refreshVolumes()
    }
}
