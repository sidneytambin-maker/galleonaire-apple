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
        _ = element.waitForExistence(timeout: 2)
        // The key window can be only the scroll indicator on watchOS. Use the
        // full content window and hold at the end of each drag to stop momentum.
        let window = app.windows.allElementsBoundByIndex.max {
            $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height
        }!
        for attempt in 0..<25 {
            let top = window.frame.minY + 66
            let bottom = window.frame.maxY - 12
            if element.exists, element.isHittable,
               element.frame.midY >= top, element.frame.midY <= bottom {
                element.tap()
                return
            }
            let upward = element.exists && element.frame.midY < top
            print("Watch scroll \(attempt): viewport \(window.frame), target \(element.exists ? element.frame.debugDescription : "not yet materialized")")
            let start = window.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: upward ? 0.45 : 0.75))
            let end = window.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: upward ? 0.75 : 0.45))
            start.press(forDuration: 0.05, thenDragTo: end,
                        withVelocity: XCUIGestureVelocity(120), thenHoldForDuration: 0.3)
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
