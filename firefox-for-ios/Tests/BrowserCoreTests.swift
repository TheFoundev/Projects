import XCTest
@testable import Firefox

final class BrowserCoreTests: XCTestCase {

    // MARK: - Search

    func testATextThatLooksLikeAUrlIsOpened() {
        XCTAssertTrue(BrowserCore.looksLikeURL("developer.mozilla.org"))
        XCTAssertFalse(BrowserCore.looksLikeURL("what is a content rule list"))
    }

    func testAUrlGetsTheScheme() {
        let engine = BrowserCore.defaultEngines[0]
        XCTAssertEqual(
            BrowserCore.destination(for: "developer.mozilla.org", engine: engine),
            "https://developer.mozilla.org"
        )
    }

    func testAnythingElseIsSearched() {
        let engine = BrowserCore.defaultEngines[0]
        XCTAssertEqual(
            BrowserCore.destination(for: "content rules", engine: engine),
            "https://www.google.com/search?q=content%20rules"
        )
    }

    func testTheSearchEngineCanBeChosen() {
        let wikipedia = BrowserCore.defaultEngines.first { $0.id == "wikipedia" }!
        XCTAssertEqual(
            BrowserCore.destination(for: "swift", engine: wikipedia),
            "https://en.wikipedia.org/w/index.php?search=swift"
        )
    }

    // MARK: - The tracking protection

    func testTheStandardLevelBlocksTheUsualTrackers() {
        let trackers = BrowserCore.ProtectionLevel.standard.blockedTrackers()
        XCTAssertGreaterThan(trackers.count, 5)
        XCTAssertTrue(trackers.contains { $0.contains("doubleclick") })
    }

    func testTheStrictLevelBlocksMore() {
        let standard = BrowserCore.ProtectionLevel.standard.blockedTrackers().count
        let strict = BrowserCore.ProtectionLevel.strict.blockedTrackers().count
        XCTAssertGreaterThan(strict, standard)
    }

    func testTheCustomLevelUsesTheTrackersOfTheUser() {
        let level = BrowserCore.ProtectionLevel.custom
        XCTAssertEqual(
            level.blockedTrackers(custom: ["\\.example\\.com.*"]),
            ["\\.example\\.com.*"]
        )
    }

    func testTheContentRuleListIsValidJsonWithOneRulePerTracker() {
        let json = BrowserCore.contentRuleListJSON(level: .standard)
        let parsed = try? JSONSerialization.jsonObject(with: Data(json.utf8))
        let rules = parsed as? [[String: Any]]
        XCTAssertEqual(rules?.count, BrowserCore.ProtectionLevel.standard.blockedTrackers().count)
    }

    func testTheNumberOfBlockersIsCountedFromTheLevel() {
        XCTAssertEqual(
            BrowserCore.blockedCount(level: .standard),
            BrowserCore.ProtectionLevel.standard.blockedTrackers().count
        )
    }

    // MARK: - The tabs

    func testClosingATabLeavesTheOthers() {
        let tabs = [
            BrowserTabInfo(title: "One", urlString: "https://one.test"),
            BrowserTabInfo(title: "Two", urlString: "https://two.test"),
        ]
        let result = BrowserCore.tabsAfterClosing(tabs, at: IndexSet(integer: 0))
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].title, "Two")
    }

    func testClosingTheLastTabLeavesOne() {
        let tabs = [BrowserTabInfo(title: "One", urlString: "https://one.test")]
        let result = BrowserCore.tabsAfterClosing(tabs, at: IndexSet(integer: 0))
        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result[0].urlString, "https://www.mozilla.org")
    }

    func testTheTitleComesFromTheUrl() {
        XCTAssertEqual(
            BrowserCore.title(for: "https://developer.mozilla.org/docs"),
            "developer.mozilla.org/docs"
        )
    }

    // MARK: - The store

    func testTheTabsAreKeptBetweenTwoLaunches() {
        let defaults = UserDefaults(suiteName: "firefox.tests")!
        defaults.removePersistentDomain(forName: "firefox.tests")

        let first = FirefoxStore(defaults: defaults)
        first.open(urlString: "https://example.test")
        XCTAssertEqual(first.tabs.count, 2)

        let second = FirefoxStore(defaults: defaults)
        XCTAssertEqual(second.tabs.count, 2)
        XCTAssertEqual(second.tabs[1].urlString, "https://example.test")

        defaults.removePersistentDomain(forName: "firefox.tests")
    }

    func testTheProtectionLevelIsKept() {
        let defaults = UserDefaults(suiteName: "firefox.tests")!
        defaults.removePersistentDomain(forName: "firefox.tests")

        let store = FirefoxStore(defaults: defaults)
        store.setProtectionLevel(.strict)

        let second = FirefoxStore(defaults: defaults)
        XCTAssertEqual(second.protectionLevel, .strict)
        XCTAssertGreaterThan(second.blockedTrackerCount, BrowserCore.blockedCount(level: .standard))

        defaults.removePersistentDomain(forName: "firefox.tests")
    }

    func testTheSearchEngineIsKept() {
        let defaults = UserDefaults(suiteName: "firefox.tests")!
        defaults.removePersistentDomain(forName: "firefox.tests")

        let store = FirefoxStore(defaults: defaults)
        let bing = BrowserCore.defaultEngines.first { $0.id == "bing" }!
        store.chooseEngine(bing)

        let second = FirefoxStore(defaults: defaults)
        XCTAssertEqual(second.engine.id, "bing")

        defaults.removePersistentDomain(forName: "firefox.tests")
    }
}
