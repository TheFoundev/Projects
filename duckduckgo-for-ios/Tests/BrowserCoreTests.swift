import XCTest
@testable import DuckDuckGo

final class BrowserCoreTests: XCTestCase {

    // MARK: - Search

    func testATextThatLooksLikeAUrlIsOpened() {
        XCTAssertTrue(BrowserCore.looksLikeURL("example.com"))
        XCTAssertTrue(BrowserCore.looksLikeURL("https://example.com/page"))
        XCTAssertFalse(BrowserCore.looksLikeURL("how to cook rice"))
        XCTAssertFalse(BrowserCore.looksLikeURL("a.b"))
    }

    func testAUrlGetsTheScheme() {
        let engine = BrowserCore.defaultEngines[0]
        XCTAssertEqual(
            BrowserCore.destination(for: "example.com", engine: engine),
            "https://example.com"
        )
        XCTAssertEqual(
            BrowserCore.destination(for: "http://example.com", engine: engine),
            "http://example.com"
        )
    }

    func testAnythingElseIsSearched() {
        let engine = BrowserCore.defaultEngines[0]
        let destination = BrowserCore.destination(for: "how to cook rice", engine: engine)
        XCTAssertEqual(destination, "https://duckduckgo.com/?q=how%20to%20cook%20rice")
    }

    func testAnEmptyTextGoesNowhere() {
        let engine = BrowserCore.defaultEngines[0]
        XCTAssertNil(BrowserCore.destination(for: "   ", engine: engine))
    }

    func testTheSearchEngineCanBeChosen() {
        let google = BrowserCore.defaultEngines.first { $0.id == "google" }
        XCTAssertNotNil(google)
        XCTAssertEqual(
            BrowserCore.destination(for: "swift", engine: google!),
            "https://www.google.com/search?q=swift"
        )
    }

    func testThereAreSeveralSearchEngines() {
        XCTAssertGreaterThan(BrowserCore.defaultEngines.count, 1)
        for engine in BrowserCore.defaultEngines {
            XCTAssertTrue(engine.template.contains("{query}"))
        }
    }

    // MARK: - Tracking

    func testThereAreTrackerRules() {
        XCTAssertGreaterThan(BrowserCore.trackerCount, 5)
        XCTAssertEqual(BrowserCore.trackerCount, BrowserCore.blockingRuleCount)
    }

    func testTheContentRuleListIsValidJson() {
        let json = BrowserCore.contentRuleListJSON()
        XCTAssertTrue(json.hasPrefix("["))
        XCTAssertTrue(json.hasSuffix("]"))
        let data = json.data(using: .utf8)!
        let parsed = try? JSONSerialization.jsonObject(with: data)
        XCTAssertNotNil(parsed)
        let rules = parsed as? [[String: Any]]
        XCTAssertEqual(rules?.count, BrowserCore.trackerCount)
    }

    func testEveryRuleBlocksSomething() {
        for pattern in BrowserCore.trackerPatterns {
            XCTAssertTrue(pattern.hasPrefix(".*"))
            XCTAssertTrue(pattern.hasSuffix(".*"))
        }
    }

    // MARK: - Private mode

    func testThePrivateModeThrowsTheDataAway() {
        XCTAssertTrue(BrowserCore.shouldDiscardData(privateMode: true))
        XCTAssertFalse(BrowserCore.shouldDiscardData(privateMode: false))
        XCTAssertFalse(BrowserCore.privateStoreName.isEmpty)
    }

    // MARK: - The tabs

    func testClosingATabLeavesTheOthers() {
        let tabs = [
            BrowserTabInfo(title: "One", urlString: "https://one.test"),
            BrowserTabInfo(title: "Two", urlString: "https://two.test"),
        ]
        let result = BrowserCore.tabsAfterClosing(tabs, at: 0)
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].title, "Two")
    }

    func testClosingTheLastTabLeavesOne() {
        let tabs = [BrowserTabInfo(title: "One", urlString: "https://one.test")]
        let result = BrowserCore.tabsAfterClosing(tabs, at: 0)
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].urlString, "https://duckduckgo.com")
    }

    // MARK: - The store

    func testTheTabsAreKeptBetweenTwoLaunches() {
        let defaults = UserDefaults(suiteName: "duckduckgo.tests")!
        defaults.removePersistentDomain(forName: "duckduckgo.tests")

        let first = BrowserStore(defaults: defaults)
        first.load(urlString: "https://example.test", title: "Example")
        XCTAssertEqual(first.tabs.count, 2)

        let second = BrowserStore(defaults: defaults)
        XCTAssertEqual(second.tabs.count, 2)
        XCTAssertEqual(second.tabs[1].title, "Example")

        defaults.removePersistentDomain(forName: "duckduckgo.tests")
    }

    func testTheSearchEngineIsKept() {
        let defaults = UserDefaults(suiteName: "duckduckgo.tests")!
        defaults.removePersistentDomain(forName: "duckduckgo.tests")

        let store = BrowserStore(defaults: defaults)
        let bing = BrowserCore.defaultEngines.first { $0.id == "bing" }!
        store.chooseEngine(bing)

        let second = BrowserStore(defaults: defaults)
        XCTAssertEqual(second.engine.id, "bing")

        defaults.removePersistentDomain(forName: "duckduckgo.tests")
    }

    func testTheNumberOfTrackersIsCountedFromTheRules() {
        let defaults = UserDefaults(suiteName: "duckduckgo.tests")!
        let store = BrowserStore(defaults: defaults)
        XCTAssertEqual(store.blockedTrackers, BrowserCore.trackerCount)
    }
}
