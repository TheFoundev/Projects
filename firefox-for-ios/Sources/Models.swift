import Foundation
import Combine

struct BrowserTab: Identifiable, Equatable {
    let id = UUID()
    var title: String
    var urlString: String
    var isPrivate: Bool = false

    var info: BrowserTabInfo { BrowserTabInfo(title: title, urlString: urlString, isPrivate: isPrivate) }
}

struct Shortcut: Identifiable {
    let id = UUID()
    let title: String
    let url: String
    let symbol: String
}

let shortcuts = [
    Shortcut(title: "Mozilla", url: "https://www.mozilla.org", symbol: "flame"),
    Shortcut(title: "Wikipedia", url: "https://www.wikipedia.org", symbol: "book"),
    Shortcut(title: "MDN", url: "https://developer.mozilla.org", symbol: "chevron.left.forwardslash.chevron.right"),
    Shortcut(title: "Hacker News", url: "https://news.ycombinator.com", symbol: "newspaper"),
]

final class FirefoxStore: ObservableObject {
    private static let tabsKey = "firefox.tabs"
    private static let levelKey = "firefox.protection"
    private static let engineKey = "firefox.engine"
    private static let customKey = "firefox.custom"

    @Published var urlString = "https://www.mozilla.org"
    @Published var tabs: [BrowserTab]
    @Published var blockTrackers = true
    @Published var syncEnabled = false
    @Published var privateMode = false
    @Published var protectionLevel: BrowserCore.ProtectionLevel
    @Published var engine: BrowserCore.SearchEngine
    @Published var customTrackers: [String]

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.tabs = Self.loadTabs(defaults) ?? [BrowserTab(title: "Mozilla", urlString: "https://www.mozilla.org")]
        let levelName = defaults.string(forKey: Self.levelKey) ?? "standard"
        self.protectionLevel = BrowserCore.ProtectionLevel.named(levelName) ?? .standard
        let engineId = defaults.string(forKey: Self.engineKey) ?? "google"
        self.engine = BrowserCore.defaultEngines.first(where: { $0.id == engineId }) ?? BrowserCore.defaultEngines[0]
        self.customTrackers = defaults.stringArray(forKey: Self.customKey) ?? BrowserCore.customTrackers
    }

    /// The number of the trackers that are blocked.
    var blockedTrackerCount: Int {
        BrowserCore.blockedCount(level: protectionLevel, custom: customTrackers)
    }

    // MARK: - The tabs

    private static func loadTabs(_ defaults: UserDefaults) -> [BrowserTab]? {
        guard let data = defaults.data(forKey: tabsKey),
              let saved = try? JSONDecoder().decode([SavedTab].self, from: data) else { return nil }
        guard !saved.isEmpty else { return nil }
        return saved.map { BrowserTab(title: $0.title, urlString: $0.urlString, isPrivate: $0.isPrivate) }
    }

    private func saveTabs() {
        let saved = tabs.map { SavedTab(title: $0.title, urlString: $0.urlString, isPrivate: $0.isPrivate) }
        if let data = try? JSONEncoder().encode(saved) {
            defaults.set(data, forKey: Self.tabsKey)
        }
    }

    // MARK: - Searching

    func search(_ text: String) {
        let value = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !value.isEmpty else { return }
        guard let destination = BrowserCore.destination(for: value, engine: engine) else { return }
        open(urlString: destination)
    }

    func open(urlString: String) {
        self.urlString = urlString
        let title = BrowserCore.title(for: urlString)
        let tab = BrowserTab(title: title, urlString: urlString, isPrivate: privateMode)
        if let index = tabs.firstIndex(where: { $0.urlString == urlString }) {
            tabs[index] = tab
        } else {
            tabs.append(tab)
        }
        saveTabs()
    }

    func addPrivateTab() {
        privateMode = true
        let tab = BrowserTab(title: "Private tab", urlString: "about:blank", isPrivate: true)
        tabs.append(tab)
        saveTabs()
    }

    func close(at offsets: IndexSet) {
        for index in offsets.sorted(by: >) where tabs.indices.contains(index) {
            tabs.remove(at: index)
        }
        if tabs.isEmpty {
            tabs.append(BrowserTab(title: "Mozilla", urlString: "https://www.mozilla.org"))
        }
        saveTabs()
    }

    // MARK: - The settings

    /// The level of the tracking protection.
    func setProtectionLevel(_ level: BrowserCore.ProtectionLevel) {
        protectionLevel = level
        defaults.set(level.rawValue, forKey: Self.levelKey)
    }

    /// The search engine.
    func chooseEngine(_ engine: BrowserCore.SearchEngine) {
        self.engine = engine
        defaults.set(engine.id, forKey: Self.engineKey)
    }

    /// The trackers the user blocks by hand.
    func setCustomTrackers(_ trackers: [String]) {
        customTrackers = trackers
        defaults.set(trackers, forKey: Self.customKey)
    }
}

/// The tab as it is written to the storage.
private struct SavedTab: Codable {
    var title: String
    var urlString: String
    var isPrivate: Bool
}
