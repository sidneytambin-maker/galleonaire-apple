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
