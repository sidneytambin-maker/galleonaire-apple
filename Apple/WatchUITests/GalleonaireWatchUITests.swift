import XCTest
import GalleonaireCore

final class GalleonaireWatchUITests: XCTestCase {
    private var app: XCUIApplication!
    override func setUpWithError() throws {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--ui-testing", "--reset-test-game"]
        app.launch()
    }
    private func element(_ id: String) -> XCUIElement { app.descendants(matching: .any).matching(identifier: id).firstMatch }
    @discardableResult private func reveal(_ element: XCUIElement) -> Bool {
        _ = element.waitForExistence(timeout: 2)
        if element.exists, element.identifier.hasPrefix("tab-"), element.isHittable { return true }
        // The key window can be only the scroll indicator. Keep drags above the fixed tabs.
        let window = app.windows.allElementsBoundByIndex.max {
            $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height
        }!
        for attempt in 0..<25 {
            let top = window.frame.minY + 66
            let tab = app.buttons["tab-game"]
            let bottom = tab.exists && tab.isHittable ? tab.frame.minY - 4 : window.frame.maxY - 12
            if element.exists, element.isHittable, element.frame.midY >= top, element.frame.midY <= bottom {
                return true
            }
            let upward = element.exists && element.frame.midY < top
            print("Watch scroll \(attempt): target \(element.exists ? element.frame.debugDescription : "not yet materialized")")
            let start = window.coordinate(withNormalizedOffset: .zero).withOffset(CGVector(dx: window.frame.width / 2, dy: (upward ? top + 14 : bottom - 8) - window.frame.minY))
            let end = window.coordinate(withNormalizedOffset: .zero).withOffset(CGVector(dx: window.frame.width / 2, dy: (upward ? bottom - 8 : top + 14) - window.frame.minY))
            start.press(forDuration: 0.05, thenDragTo: end, withVelocity: XCUIGestureVelocity(120), thenHoldForDuration: 0.3)
        }
        XCTFail("Watch control is not reachable: \(element)\n\(app.debugDescription)")
        return false
    }
    private func tap(_ element: XCUIElement) { if reveal(element) { element.tap() } }
    override func tearDownWithError() throws {
        capture("watch-final-state")
        let tree = XCTAttachment(string: app.debugDescription)
        tree.name = "watch-accessibility-tree"; tree.lifetime = .keepAlways; add(tree)
    }
    private func capture(_ name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name; attachment.lifetime = .keepAlways; add(attachment)
    }
    private func question() throws -> Question {
        let text = element("questionText").label
        return try XCTUnwrap(QuestionBank.bundled().questions.first { text.hasSuffix($0.text) })
    }
    func testIndependentWatchGameAdvancesCorrectAnswersImmediately() throws {
        capture("watch-home")
        XCTAssertEqual(element("gameHeading").label, "Galleonaire: a magical quiz game")
        tap(app.buttons["newGame"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        capture("watch-question")
        let q = try question()
        tap(app.buttons["answer\(q.correctIndex)"])
        XCTAssertTrue(element("questionText").label.contains("Correct."))
        XCTAssertTrue(element("questionText").label.contains(q.explanation))
        XCTAssertTrue(element("questionText").label.contains("Question 2 of 15."))
        XCTAssertFalse(app.buttons["nextQuestion"].exists)
        XCTAssertFalse(element("gameResult").exists)
        capture("watch-automatic-next-question")
    }
    func testWatchWrongAnswerEndsGameWithReachedPrize() throws {
        tap(app.buttons["newGame"])
        let q = try question()
        tap(app.buttons["answer\((q.correctIndex + 1) % 4)"])
        XCTAssertTrue(element("gameResult").waitForExistence(timeout: 5))
        XCTAssertTrue(element("gameResult").label.contains("Correct answer:"))
        XCTAssertTrue(element("gameResult").label.contains("You reached question 1 of 15"))
        XCTAssertTrue(element("gameResult").label.contains("You leave with 0 galleons"))
        XCTAssertFalse(app.alerts.firstMatch.exists)
        XCTAssertFalse(app.buttons["lockAnswer"].exists)
        XCTAssertFalse(app.buttons["answer0"].exists)
        capture("watch-answer-result")
    }
    func testWatchTabsSwapQuestionAndSettingsPreserveGame() {
        let tabs = ["game", "rules", "settings"].map { app.buttons["tab-\($0)"] }
        XCTAssertEqual(tabs.map(\.label), ["Game", "How to play", "Settings"])
        XCTAssertLessThan(tabs[0].frame.minX, tabs[1].frame.minX)
        XCTAssertLessThan(tabs[1].frame.minX, tabs[2].frame.minX)
        tap(app.buttons["newGame"])
        let old = element("questionText").label
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-freePass"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        XCTAssertNotEqual(element("questionText").label, old)
        let replacement = element("questionText").label
        tap(tabs[1]); XCTAssertTrue(element("tabHeading").exists)
        tap(tabs[2]); reveal(app.sliders["musicVolume"])
        XCTAssertEqual(app.sliders["musicVolume"].label, "Music Volume")
        capture("watch-settings")
        tap(tabs[0]); XCTAssertEqual(element("questionText").label, replacement)
        app.terminate(); app.launchArguments = ["--ui-testing"]; app.launch()
        XCTAssertTrue(app.buttons["newGame"].exists)
        XCTAssertFalse(element("questionText").exists)
    }
    func testWatchFiftyFiftyRemovesControlsAndAudienceVotesLabelEachAnswer() {
        tap(app.buttons["newGame"])
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-fiftyFifty"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        let remaining = (0..<4).filter { app.buttons["answer\($0)"].exists }
        XCTAssertEqual(remaining.count, 2)
        tap(app.buttons["lifelines"]); tap(app.buttons["lifeline-audience"])
        XCTAssertTrue(element("questionText").waitForExistence(timeout: 5))
        for i in remaining { XCTAssertTrue(app.buttons["answer\(i)"].label.contains("percent")) }
        capture("watch-audience-answers")
    }
    func testWatchWalkAwayReturnsToPersistedMenu() {
        tap(app.buttons["newGame"])
        tap(app.buttons["walkAway"])
        tap(app.buttons["Walk Away with 0 galleons"])
        XCTAssertTrue(element("gameResult").waitForExistence(timeout: 5))
        tap(app.buttons["mainMenu"])
        XCTAssertTrue(app.buttons["newGame"].exists)
        app.terminate(); app.launchArguments = ["--ui-testing"]; app.launch()
        XCTAssertTrue(app.buttons["newGame"].exists)
        XCTAssertFalse(element("gameResult").exists)
    }
}
