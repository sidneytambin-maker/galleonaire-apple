import XCTest

final class GalleonaireWatchUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset-test-game"]
        app.launch()
    }
    private func tap(_ element: XCUIElement) {
        guard element.waitForExistence(timeout: 5) else {
            XCTFail("Missing Watch control: \(element)\n\(app.debugDescription)")
            return
        }
        for _ in 0..<18 {
            if element.exists && element.isHittable { element.tap(); return }
            app.scrollViews.firstMatch.swipeUp()
        }
        for _ in 0..<18 {
            app.scrollViews.firstMatch.swipeDown()
            if element.isHittable { element.tap(); return }
        }
        XCTFail("Watch control is not reachable: \(element)\n\(app.debugDescription)")
    }
    override func tearDownWithError() throws {
        capture("watch-final-state")
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = "watch-accessibility-tree"
        tree.lifetime = .keepAlways
        add(tree)
    }
    private func capture(_ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
    func testIndependentWatchGameStartsAndSelectsAnswer() {
        capture("watch-home")
        tap(app.buttons["New Game"])
        XCTAssertTrue(app.staticTexts["questionText"].waitForExistence(timeout: 5))
        capture("watch-question")
        tap(app.buttons["answer0"])
        tap(app.buttons["lockAnswer"])
        tap(app.buttons["Lock Answer"])
        XCTAssertTrue(app.staticTexts["gameResult"].waitForExistence(timeout: 5))
        capture("watch-answer-result")
    }
    func testWatchLifelinesAndSettingsExist() {
        tap(app.buttons["New Game"])
        tap(app.buttons["Lifelines"])
        XCTAssertTrue(app.buttons["Fifty-Fifty"].exists)
        tap(app.buttons["Free Pass"])
        tap(app.buttons["Use Free Pass"])
        XCTAssertTrue(app.staticTexts["questionText"].waitForExistence(timeout: 5))
        app.terminate()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        tap(app.buttons["Settings"])
        XCTAssertTrue(app.switches["musicEnabled"].waitForExistence(timeout: 5), app.debugDescription)
        capture("watch-settings")
    }
}
