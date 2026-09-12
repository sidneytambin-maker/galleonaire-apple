import Foundation

public enum SettingKey: String, Codable, CaseIterable, Sendable { case musicEnabled, musicVolume, effectsEnabled, effectsVolume, hapticsEnabled }

public struct SettingValue: Codable, Equatable, Sendable {
    public var value: Int
    public var revision: UInt64
    public var author: String
}

public struct GameSettings: Codable, Equatable, Sendable {
    public var schemaVersion = 1
    public private(set) var values: [SettingKey: SettingValue] = [:]
    public init() {}
    public func value(_ key: SettingKey) -> Int {
        values[key]?.value ?? (key == .musicVolume ? 15 : key == .effectsVolume ? 35 : 1)
    }
    public func enabled(_ key: SettingKey) -> Bool { value(key) == 1 }
    public var musicGain: Float { enabled(.musicEnabled) ? Float(value(.musicVolume)) / 100 : 0 }
    public var effectsGain: Float { enabled(.effectsEnabled) ? Float(value(.effectsVolume)) / 100 : 0 }
    public mutating func set(_ key: SettingKey, value: Int, author: String) {
        let maximum = key == .musicVolume || key == .effectsVolume ? 100 : 1
        let latest = values.values.map(\.revision).max() ?? 0
        guard latest < UInt64.max else { return }
        values[key] = SettingValue(value: min(maximum, max(0, value)), revision: latest + 1, author: author)
    }
    @discardableResult public mutating func merge(_ incoming: GameSettings) -> Bool {
        guard incoming.isValid else { return false }
        var changed = false
        for (key, candidate) in incoming.values {
            if let local = values[key], local.revision > candidate.revision || (local.revision == candidate.revision && local.author >= candidate.author) { continue }
            if values[key] != candidate { values[key] = candidate; changed = true }
        }
        return changed
    }
    public var isValid: Bool {
        schemaVersion == 1 && values.allSatisfy { key, entry in
            let maximum = key == .musicVolume || key == .effectsVolume ? 100 : 1
            return (0...maximum).contains(entry.value) && entry.revision < UInt64.max && !entry.author.isEmpty && entry.author.count <= 100
        }
    }
}
