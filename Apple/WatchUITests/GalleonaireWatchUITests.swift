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
        // Small crown movements do not fling past compact rows, and materialize
        // off-screen SwiftUI List cells that are absent from the initial tree.
        for _ in 0..<50 {
            let top = app.frame.minY + 66
            let bottom = app.frame.maxY - 12
            if element.exists, element.isHittable,
               element.frame.midY >= top, element.frame.midY <= bottom {
                element.tap()
                return
            }
            let upward = element.exists && element.frame.midY < top
            XCUIDevice.shared.rotateDigitalCrown(delta: upward ? 0.15 : -0.15, velocity: XCUIGestureVelocity(0.5))
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
