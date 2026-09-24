import Foundation

public struct GamePersistence {
    public let directory: URL
    public init(directory: URL) { self.directory = directory }
    public func load() throws -> GameArchive {
        let url = directory.appendingPathComponent("game.json")
        guard FileManager.default.fileExists(atPath: url.path) else { return GameArchive() }
        return try JSONDecoder().decode(GameArchive.self, from: Data(contentsOf: url))
    }
    public func save(_ archive: GameArchive) throws {
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let encoded = try JSONEncoder().encode(archive)
        try encoded.write(to: directory.appendingPathComponent("game.json"), options: .atomic)
    }
    public func preserveUnreadableSave() throws {
        let original = directory.appendingPathComponent("game.json")
        if FileManager.default.fileExists(atPath: original.path) {
            try FileManager.default.copyItem(at: original, to: directory.appendingPathComponent("recovery-\(UUID().uuidString).json"))
        }
    }
}


extension GameArchive {
    /// Reclassify the seen-question history without replacing facts or losing records.
    /// The app already clears unfinished games on launch; this only accepts records.
    public func migratingQuestionHistory(to bank: QuestionBank) throws -> GameArchive {
        guard game == nil else { throw GameError.invalidSave }
        if questionContentRevision == bank.contentRevision { return self }
        guard questionContentRevision == nil, bank.contentRevision == 2,
              let previousLevels = bank.previousLevels else { throw GameError.invalidSave }
        var migrated = self
        migrated.recent = [:]
        var seen = Set<String>()
        for oldLevel in recent.keys.sorted() {
            guard (1...15).contains(oldLevel) else { throw GameError.invalidSave }
            for id in recent[oldLevel, default: []] {
                guard previousLevels[id] == oldLevel, let question = bank.question(id),
                      seen.insert(id).inserted else { throw GameError.invalidSave }
                migrated.recent[question.level, default: []].append(id)
            }
        }
        migrated.questionContentRevision = bank.contentRevision
        return migrated
    }
}
