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
        SearchEngine(id: "google", name: "Google", template: "https://www.google.com/search?q={query}"),
        SearchEngine(id: "duckduckgo", name: "DuckDuckGo", template: "https://duckduckgo.com/?q={query}"),
        SearchEngine(id: "bing", name: "Bing", template: "https://www.bing.com/search?q={query}"),
        SearchEngine(id: "wikipedia", name: "Wikipedia", template: "https://en.wikipedia.org/w/index.php?search={query}"),
    ]

    /// True when the text is a url and not a search.
    public static func looksLikeURL(_ text: String) -> Bool {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.contains(" "), trimmed.contains("."), trimmed.count > 4 else { return false }
        return true
    }

    /// The url the browser goes to for what was typed.
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

    // MARK: - The tracking protection

    /// The levels of the tracking protection.
    public enum ProtectionLevel: String, CaseIterable, Equatable {
        case standard
        case strict
        case custom

        /// The trackers that are blocked at this level.
        public func blockedTrackers(custom: [String] = BrowserCore.customTrackers) -> [String] {
            switch self {
            case .standard:
                return BrowserCore.standardTrackers
            case .strict:
                return BrowserCore.strictTrackers
            case .custom:
                return custom
            }
        }

        /// The level that goes with a name, when there is one.
        public static func named(_ name: String) -> ProtectionLevel? {
            ProtectionLevel(rawValue: name)
        }
    }

    /// The trackers that are always blocked.
    public static let standardTrackers: [String] = [
        ".*doubleclick\\.net.*",
        ".*googlesyndication\\.com.*",
        ".*google-analytics\\.com.*",
        ".*facebook\\.net.*",
        ".*amazon-adsystem\\.com.*",
        ".*hotjar\\.com.*",
        ".*segment\\.io.*",
        ".*criteo\\.com.*",
        ".*taboola\\.com.*",
        ".*outbrain\\.com.*",
    ]

    /// The trackers that are blocked when the protection is strict.
    public static let strictTrackers: [String] = standardTrackers + [
        ".*mixpanel\\.com.*",
        ".*quantserve\\.com.*",
        ".*adnxs\\.com.*",
        ".*scorecardresearch\\.com.*",
        ".*appsflyer\\.com.*",
        ".*branch\\.io.*",
    ]

    /// The trackers the user can block by hand.
    public static let customTrackers: [String] = [
        ".*twitter\\.com.*",
        ".*linkedin\\.com.*",
        ".*tiktok\\.com.*",
    ]

    /// The rules of the content rule list of WebKit, as json.
    public static func contentRuleListJSON(level: ProtectionLevel, custom: [String] = customTrackers) -> String {
        let rules = level.blockedTrackers(custom: custom).map { pattern in
            "{\"trigger\":{\"url-filter\":\"\(pattern)\"},\"action\":{\"type\":\"block\"}}"
        }
        return "[\(rules.joined(separator: ","))]"
    }

    /// The number of the trackers that are blocked at a level.
    public static func blockedCount(level: ProtectionLevel, custom: [String] = customTrackers) -> Int {
        level.blockedTrackers(custom: custom).count
    }

    // MARK: - The tabs

    /// The tabs that are left after a tab is closed.
    public static func tabsAfterClosing(_ tabs: [BrowserTabInfo], at offsets: IndexSet) -> [BrowserTabInfo] {
        var result = tabs
        for index in offsets.sorted(by: >) where result.indices.contains(index) {
            result.remove(at: index)
        }
        if result.isEmpty {
            result = [BrowserTabInfo(title: "Mozilla", urlString: "https://www.mozilla.org")]
        }
        return result
    }

    /// The title a tab gets from its url.
    public static func title(for urlString: String) -> String {
        urlString
            .replacingOccurrences(of: "https://", with: "")
            .replacingOccurrences(of: "http://", with: "")
    }
}

/// The information of a tab, without the identity of the object.
public struct BrowserTabInfo: Equatable {
    public var title: String
    public var urlString: String
    public var isPrivate: Bool

    public init(title: String, urlString: String, isPrivate: Bool = false) {
        self.title = title
        self.urlString = urlString
        self.isPrivate = isPrivate
    }
}
