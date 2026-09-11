import XCTest
@testable import GalleonaireCore

final class SettingsTests: XCTestCase {
    func testRestrainedDefaults() {
        let s = GameSettings()
        XCTAssertEqual(s.value(.musicVolume), 15)
        XCTAssertEqual(s.value(.effectsVolume), 35)
        XCTAssertTrue(s.enabled(.hapticsEnabled))
    }
    func testConcurrentDifferentFieldsAreBothKept() {
        var phone = GameSettings(), watch = GameSettings()
        phone.set(.musicVolume, value: 20, author: "phone")
        watch.set(.effectsEnabled, value: 0, author: "watch")
        let phoneBefore = phone
        XCTAssertTrue(phone.merge(watch))
        XCTAssertTrue(watch.merge(phoneBefore))
        XCTAssertEqual(phone, watch)
        XCTAssertEqual(phone.value(.musicVolume), 20)
        XCTAssertFalse(phone.enabled(.effectsEnabled))
    }
    func testConflictResolutionConvergesAndIsIdempotent() {
        var a = GameSettings(), b = GameSettings()
        a.set(.musicVolume, value: 10, author: "A")
        b.set(.musicVolume, value: 80, author: "B")
        let oldA = a
        a.merge(b)
        b.merge(oldA)
        XCTAssertEqual(a, b)
        XCTAssertFalse(a.merge(b))
        a.set(.musicVolume, value: 15, author: "A")
        XCTAssertTrue(b.merge(a))
        XCTAssertEqual(a, b)
        XCTAssertEqual(b.value(.musicVolume), 15)
    }
    func testSettingsPersistThroughJSONAndClampVolumes() throws {
        var s = GameSettings()
        s.set(.musicVolume, value: 900, author: "A")
        s.set(.effectsVolume, value: -50, author: "A")
        XCTAssertEqual(s.value(.musicVolume), 100)
        XCTAssertEqual(s.value(.effectsVolume), 0)
        XCTAssertEqual(try JSONDecoder().decode(GameSettings.self, from: JSONEncoder().encode(s)), s)
    }
    func testUnknownSchemaCannotOverrideLocalSettings() {
        var local = GameSettings(), remote = GameSettings()
        remote.set(.musicEnabled, value: 0, author: "B")
        remote.schemaVersion = 99
        XCTAssertFalse(local.merge(remote))
        XCTAssertTrue(local.enabled(.musicEnabled))
    }
}
