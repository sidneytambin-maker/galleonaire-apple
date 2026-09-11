import XCTest
import GalleonaireCore

final class GalleonaireUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset-test-game"]
        app.launch()
    }
    private func tap(_ element: XCUIElement) {
        guard element.waitForExistence(timeout: 5) else {
            XCTFail("Missing control: \(element)\n\(app.debugDescription)")
            return
        }
        for _ in 0..<12 {
            if element.exists && element.isHittable { element.tap(); return }
            app.swipeUp()
        }
        for _ in 0..<12 {
            app.swipeDown()
            if element.isHittable { element.tap(); return }
        }
        XCTFail("Control is not reachable: \(element)\n\(app.debugDescription)")
    }
    override func tearDownWithError() throws {
        screenshot("iphone-final-state")
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = "iphone-accessibility-tree"
        tree.lifetime = .keepAlways
        add(tree)
    }
    private func screenshot(_ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
    func testLaunchNewGameAndFourFullyLabelledAnswers() throws {
        screenshot("iphone-home")
        tap(app.buttons["New Game"])
        XCTAssertTrue(app.staticTexts["questionText"].waitForExistence(timeout: 5))
        for i in 0..<4 {
            let answer = app.buttons["answer\(i)"]
            XCTAssertTrue(answer.exists, app.debugDescription)
            XCTAssertGreaterThan(answer.label.count, 3)
        }
        screenshot("iphone-question")
    }
    func testSelectionConfirmationCancelAndCorrectResult() throws {
        tap(app.buttons["New Game"])
        let text = app.staticTexts["questionText"].label
        let q = try XCTUnwrap(QuestionBank.bundled().questions.first { $0.text == text })
        tap(app.buttons["answer\(q.correctIndex)"])
        tap(app.buttons["lockAnswer"])
        tap(app.buttons["Cancel"])
        XCTAssertFalse(app.staticTexts["gameResult"].exists)
        tap(app.buttons["lockAnswer"])
        tap(app.buttons["Lock Answer"])
        XCTAssertTrue(app.staticTexts["gameResult"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["gameResult"].label, "Correct!")
        screenshot("iphone-correct-result")
        tap(app.buttons["nextQuestion"])
        XCTAssertTrue(app.staticTexts["Question 2 of 15"].waitForExistence(timeout: 5))
    }
    func testWrongAnswerAndPlayAgain() throws {
        tap(app.buttons["New Game"])
        let text = app.staticTexts["questionText"].label
        let q = try XCTUnwrap(QuestionBank.bundled().questions.first { $0.text == text })
        tap(app.buttons["answer\((q.correctIndex + 1) % 4)"])
        tap(app.buttons["lockAnswer"])
        app.buttons["Lock Answer"].tap()
        XCTAssertTrue(app.staticTexts["gameResult"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["gameResult"].label, "Not this time")
        tap(app.buttons["Play Again"])
        XCTAssertTrue(app.staticTexts["Question 1 of 15"].waitForExistence(timeout: 5))
    }
    func testLifelineCanBeUsedWithoutLeavingGame() {
        tap(app.buttons["New Game"])
        tap(app.buttons["Lifelines"])
        tap(app.buttons["Fifty-Fifty"])
        app.buttons["Use Fifty-Fifty"].tap()
        XCTAssertTrue(app.staticTexts["Fifty-Fifty used. Two incorrect answers eliminated."].waitForExistence(timeout: 5))
        XCTAssertEqual((0..<4).filter { !app.buttons["answer\($0)"].isEnabled }.count, 2)
    }
    func testSettingsAndResumeAfterTermination() {
        tap(app.buttons["New Game"])
        let question = app.staticTexts["questionText"].label
        app.terminate()
        app.launchArguments = ["--ui-testing"]
        app.launch()
        XCTAssertTrue(app.staticTexts["questionText"].waitForExistence(timeout: 5))
        XCTAssertEqual(app.staticTexts["questionText"].label, question)
        let settings = app.buttons["settingsButton"]
        XCTAssertLessThanOrEqual(settings.frame.width, 60, "Settings must expose its own touch target, not the entire masthead")
        tap(settings)
        XCTAssertTrue(app.switches["musicEnabled"].waitForExistence(timeout: 5), app.debugDescription)
        XCTAssertTrue(app.sliders["musicVolume"].exists, app.debugDescription)
        screenshot("iphone-settings")
        tap(app.buttons["Done"])
        XCTAssertEqual(app.staticTexts["questionText"].label, question)
    }
    func testHomeAccessibilityAudit() throws {
        try app.performAccessibilityAudit(for: [.elementDetection, .sufficientElementDescription, .hitRegion, .contrast, .textClipped])
    }
    func testLargeTextQuestionScreen() {
        app.terminate()
        app.launchArguments = ["--ui-testing", "--reset-test-game", "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]
        app.launch()
        tap(app.buttons["New Game"])
        XCTAssertTrue(app.staticTexts["questionText"].exists)
        for i in 0..<4 { tap(app.buttons["answer\(i)"]) }
        screenshot("iphone-accessibility-large-text")
    }
}
