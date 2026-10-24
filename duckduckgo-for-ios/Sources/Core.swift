import Foundation

/// The rules of the browser, without any SwiftUI or WebKit in them, so they
/// can be tested on their own.
public enum BrowserCore {

    // MARK: - Search

    /// A search engine the browser knows.
    public struct SearchEngine: Identifiable, Equatable {
        public let id: String
        public let name: String
        public let template: String

        public init(id: String, name: String, template: String) {
            self.id = id
            self.name = name
            self.template = template
        }

        /// The url of a search.
        public func url(for query: String) -> String {
            template.replacingOccurrences(of: "{query}", with: query)
        }
    }

    public static let defaultEngines: [SearchEngine] = [
        SearchEngine(id: "duckduckgo", name: "DuckDuckGo", template: "https://duckduckgo.com/?q={query}"),
        SearchEngine(id: "google", name: "Google", template: "https://www.google.com/search?q={query}"),
        SearchEngine(id: "bing", name: "Bing", template: "https://www.bing.com/search?q={query}"),
        SearchEngine(id: "startpage", name: "Startpage", template: "https://www.startpage.com/sp/search?query={query}"),
    ]

    /// True when the text is a url and not a search.
    public static func looksLikeURL(_ text: String) -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.contains(" "), trimmed.contains("."), trimmed.count > 4 else { return false }
        return true
    }

    /// The url the browser goes to for what was typed.
    ///
    /// A text that looks like a url is opened, everything else is searched
    /// for with the engine that was chosen.
    public static func destination(for text: String, engine: SearchEngine) -> String? {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return nil }

        if looksLikeURL(trimmed) {
            return trimmed.lowercased().hasPrefix("http") ? trimmed : "https://\(trimmed)"
        }

        guard let encoded = trimmed.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) else {
            return nil
        }
        return engine.url(for: encoded)
    }

    // MARK: - Tracking

    /// The trackers the browser blocks.
    ///
    /// The rules are the patterns of the request urls, the way the content
    /// rule list of WebKit takes them.
    public static let trackerPatterns: [String] = [
        ".*doubleclick\\.net.*",
        ".*googlesyndication\\.com.*",
        ".*google-analytics\\.com.*",
        ".*facebook\\.net.*",
        ".*amazon-adsystem\\.com.*",
        ".*hotjar\\.com.*",
        ".*segment\\.io.*",
        ".*mixpanel\\.com.*",
        ".*taboola\\.com.*",
        ".*criteo\\.com.*",
        ".*outbrain\\.com.*",
        ".*scorecardresearch\\.com.*",
        ".*quantserve\\.com.*",
        ".*adnxs\\.com.*",
    ]

    /// The number of the trackers that are blocked.
    public static var trackerCount: Int { trackerPatterns.count }

    /// The rules of the content rule list of WebKit, as json.
    public static func contentRuleListJSON() -> String {
        let rules = trackerPatterns.map { pattern in
            "{\"trigger\":{\"url-filter\":\"\(pattern)\"},\"action\":{\"type\":\"block\"}}"
        }
        return "[\(rules.joined(separator: ","))]"
    }

    /// The number of the rules in the content rule list.
    public static var blockingRuleCount: Int { trackerPatterns.count }

    // MARK: - Private mode

    /// The name of the data store of the private mode.
    ///
    /// A private window keeps its data in a store of its own, which is
    /// thrown away when the window closes.
    public static let privateStoreName = "duckduckgo-private"

    /// True when the data store of a window has to be thrown away.
    public static func shouldDiscardData(privateMode: Bool) -> Bool { privateMode }

    // MARK: - The tabs

    /// The tabs that are left after a tab is closed.
    public static func tabsAfterClosing(_ tabs: [BrowserTabInfo], at offset: Int) -> [BrowserTabInfo] {
        var result = tabs
        if result.indices.contains(offset) {
            result.remove(at: offset)
        }
        if result.isEmpty {
            result = [BrowserTabInfo(title: "DuckDuckGo", urlString: "https://duckduckgo.com")]
        }
        return result
    }
}

/// The information of a tab, without the identity of the object.
public struct BrowserTabInfo: Equatable {
    public var title: String
    public var urlString: String

    public init(title: String, urlString: String) {
        self.title = title
        self.urlString = urlString
    }
}
