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
    private func element(_ id: String) -> XCUIElement { app.descendants(matching: .any).matching(identifier: id).firstMatch }
    private func reveal(_ element: XCUIElement) {
        _ = element.waitForExistence(timeout: 2)
        for _ in 0..<12 {
            if element.exists && element.isHittable { return }
            app.swipeUp()
        }
        for _ in 0..<12 {
            app.swipeDown()
            if element.exists && element.isHittable { return }
        }
        XCTFail("Control is not reachable: \(element)\n\(app.debugDescription)")
    }
    private func tap(_ element: XCUIElement) { reveal(element); element.tap() }
    private func sliderValue(_ slider: XCUIElement) -> Int {
        Int((slider.value as? String ?? "").components(separatedBy: CharacterSet.decimalDigits.inverted).joined()) ?? -999
    }
    private func dragSlider(_ slider: XCUIElement, to position: Double) {
        // Grab the visible thumb; XCTest's normalized-slider shortcut sometimes misses it in a SwiftUI List.
        let current = sliderValue(slider)
        XCTAssertTrue((0...100).contains(current))
        let radius = slider.frame.height / 2
        let travel = slider.frame.width - radius * 2
        let origin = slider.coordinate(withNormalizedOffset: CGVector(dx: 0, dy: 0.5))
        let start = origin.withOffset(CGVector(dx: radius + CGFloat(current) / 100 * travel, dy: 0))
        let destination = position == 0 ? 0 : position == 1 ? slider.frame.width : radius + CGFloat(position) * travel
        start.press(forDuration: 0.15, thenDragTo: origin.withOffset(CGVector(dx: destination, dy: 0)),
                    withVelocity: XCUIGestureVelocity(150), thenHoldForDuration: 0.15)
    }
    private func question() throws -> Question {
        let text = element("questionText").label
        return try XCTUnwrap(QuestionBank.bundled().questions.first { text.hasSuffix($0.text) })
    }
    private func relaunch() {
        app.terminate(); app.launchArguments = ["--ui-testing"]; app.launch()
    }
    override func tearDownWithError() throws {
        screenshot("iphone-final-state")
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = "iphone-accessibility-tree"; tree.lifetime = .keepAlways; add(tree)
    }
    private func screenshot(_ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }
    func testThreeBottomTabsAndSingleFirstGameHeading() {
        let tabs = app.tabBars.buttons.allElementsBoundByIndex
        XCTAssertEqual(tabs.map(\.label), ["Game", "How to play", "Settings"])
        XCTAssertLessThan(tabs[0].frame.minX, tabs[1].frame.minX)
        XCTAssertLessThan(tabs[1].frame.minX, tabs[2].frame.minX)
        XCTAssertGreaterThan(tabs[0].frame.minY, app.frame.height / 2)
        XCTAssertEqual(element("gameHeading").label, "Galleonaire: a magical quiz game")
        XCTAssertLessThan(element("gameHeading").frame.minY, app.buttons["newGame"].frame.minY)
        screenshot("iphone-home")
        tap(tabs[1]); XCTAssertEqual(element("tabHeading").label, "How to play")
        tap(tabs[2]); XCTAssertEqual(element("tabHeading").label, "Settings")
        tap(tabs[0]); XCTAssertTrue(app.buttons["newGame"].exists)
    }
    func testSingleActivationGivesCombinedResultAndNextQuestion() throws {
        tap(app.buttons["newGame"])
        let q = try question()
        for i in 0..<4 { XCTAssertGreaterThan(app.buttons["answer\(i)"].label.count, 3) }
        screenshot("iphone-question")
        tap(app.buttons["answer\(q.correctIndex)"])
        XCTAssertTrue(element("gameResult").waitForExistence(timeout: 5))
        XCTAssertTrue(element("gameResult").label.contains("Correct!"))
        XCTAssertTrue(element("gameResult").label.contains(q.answers[q.correctIndex]))
        XCTAssertTrue(element("gameResult").label.contains(q.explanation))
        XCTAssertFalse(app.alerts.firstMatch.exists)
        XCTAssertFalse(app.buttons["lockAnswer"].exists)
        XCTAssertFalse(app.buttons["answer0"].exists)
        XCTAssertLessThan(element("gameResult").frame.minY, app.buttons["nextQuestion"].frame.minY)
        screenshot("iphone-correct-result")
        tap(app.buttons["nextQuestion"])
        XCTAssertTrue(element("questionText").label.hasPrefix("Question 2 of 15."))
    }
    func testLossCanReturnToMenuAndStaysThereAfterRelaunch() throws {
        tap(app.buttons["newGame"])
        let q = try question()
        tap(app.buttons["answer\((q.correctIndex + 1) % 4)"])
        XCTAssertTrue(element("gameResult").waitForExistence(timeout: 5))
        XCTAssertTrue(element("gameResult").label.contains("Incorrect."))
        tap(app.buttons["mainMenu"])
        XCTAssertTrue(app.buttons["newGame"].exists)
        relaunch()
        XCTAssertTrue(app.buttons["newGame"].exists)
        XCTAssertFalse(element("gameResult").exists)
    }
    func testWalkAwayCancelThenFinishAndReturnToMenu() throws {
        tap(app.buttons["newGame"])
        tap(app.buttons["answer\(try question().correctIndex)"])
        tap(app.buttons["walkAway"])
        tap(app.alerts.buttons["Cancel"])
        XCTAssertTrue(app.buttons["nextQuestion"].exists)
        tap(app.buttons["walkAway"])
        tap(app.alerts.buttons["Walk Away with 100 galleons"])
        XCTAssertTrue(element("gameResult").label.contains("100 galleons"))
        screenshot("iphone-walk-away")
        tap(app.buttons["mainMenu"])
        XCTAssertTrue(app.staticTexts["Highest prize reached: 100 galleons"].exists)
    }
    func testFiftyFiftyRemovesButtonsAndAudienceVotesAreInsideRemainingAnswers() throws {
        tap(app.buttons["newGame"])
        let q = try question()
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-fiftyFifty"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        let remaining = (0..<4).filter { app.buttons["answer\($0)"].exists }
        XCTAssertEqual(remaining.count, 2)
        XCTAssertTrue(remaining.contains(q.correctIndex))
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-audience"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        for i in remaining { XCTAssertTrue(app.buttons["answer\(i)"].label.contains("percent")) }
        XCTAssertFalse(app.staticTexts["Audience Vote"].exists)
        screenshot("iphone-two-answers-audience")
        tap(app.buttons["answer\(q.correctIndex)"])
        XCTAssertTrue(element("gameResult").label.contains("Correct!"))
    }
    func testSwapQuestionAndTabsPreserveTheCurrentGame() {
        tap(app.buttons["newGame"])
        let old = element("questionText").label
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-freePass"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        let replacement = element("questionText").label
        XCTAssertNotEqual(old, replacement)
        XCTAssertTrue(replacement.hasPrefix("Question 1 of 15."))
        tap(app.tabBars.buttons["How to play"])
        tap(app.tabBars.buttons["Settings"])
        tap(app.tabBars.buttons["Game"])
        XCTAssertEqual(element("questionText").label, replacement)
        relaunch()
        XCTAssertTrue(app.buttons["newGame"].exists)
        XCTAssertFalse(element("questionText").exists)
    }
    func testFreshLaunchDiscardsUnfinishedGameButKeepsHighestPrize() throws {
        tap(app.buttons["newGame"])
        tap(app.buttons["answer\(try question().correctIndex)"])
        tap(app.buttons["nextQuestion"])
        XCTAssertTrue(element("questionText").label.hasPrefix("Question 2 of 15."))
        relaunch()
        XCTAssertTrue(app.buttons["newGame"].exists)
        XCTAssertFalse(element("questionText").exists)
        XCTAssertTrue(app.staticTexts["Highest prize reached: 100 galleons"].exists)
        tap(app.buttons["newGame"])
        XCTAssertTrue(element("questionText").label.hasPrefix("Question 1 of 15."))
    }
    func testVolumeSlidersExposeFullRangeAndPersist() {
        tap(app.tabBars.buttons["Settings"])
        for id in ["musicVolume", "effectsVolume"] {
            let slider = app.sliders[id]
            reveal(slider)
            var previous = sliderValue(slider)
            var previousPosition = Double(previous) / 100
            for position in [0.0, 0.25, 0.5, 0.75, 1.0, 0.75, 0.5, 0.25, 0.0, 1.0] {
                dragSlider(slider, to: position)
                let value = sliderValue(slider)
                // Drag coordinates are approximate; exact gains are tested for every integer in core tests.
                XCTAssertEqual(Double(value), position * 100, accuracy: 10)
                if position > previousPosition { XCTAssertGreaterThan(value, previous) }
                else if position < previousPosition { XCTAssertLessThan(value, previous) }
                previous = value
                previousPosition = position
                if position == 0 || position == 1 { XCTAssertEqual(value, Int(position * 100)) }
            }
        }
        screenshot("iphone-settings-volume")
        relaunch(); tap(app.tabBars.buttons["Settings"])
        XCTAssertEqual(app.sliders["musicVolume"].value as? String, "100%")
        XCTAssertEqual(app.sliders["effectsVolume"].value as? String, "100%")
    }
    func testHomeAccessibilityAudit() throws {
        try app.performAccessibilityAudit(for: [.elementDetection, .sufficientElementDescription, .hitRegion, .contrast, .textClipped])
    }
    func testEverySoundHasItsOwnPreviewButton() {
        tap(app.tabBars.buttons["Settings"])
        for event in ["correct", "incorrect", "fiftyFifty", "audience", "swapQuestion", "nextQuestion", "milestone", "majorMilestone", "victory"] {
            let preview = app.buttons["preview-\(event)"]
            tap(preview)
            XCTAssertFalse(app.alerts.firstMatch.exists)
        }
        screenshot("iphone-sound-previews")
    }
    func testLargeTextQuestionScreen() {
        app.terminate()
        app.launchArguments = ["--ui-testing", "--reset-test-game", "-UIPreferredContentSizeCategoryName", "UICTContentSizeCategoryAccessibilityXXXL"]
        app.launch()
        tap(app.buttons["newGame"])
        XCTAssertTrue(element("questionText").exists)
        for i in 0..<4 {
            let answer = app.buttons["answer\(i)"]
            reveal(answer)
            XCTAssertGreaterThanOrEqual(answer.frame.height, 52)
            XCTAssertGreaterThan(answer.label.count, 3)
            screenshot("iphone-large-answer-\(i)")
        }
        XCTAssertFalse(element("gameResult").exists, "Scrolling must not choose an answer")
    }
}
