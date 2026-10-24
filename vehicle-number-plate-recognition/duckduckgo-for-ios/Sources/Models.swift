import Foundation
import Combine

/// A tab of the browser.
struct BrowserTab: Identifiable, Equatable {
    let id = UUID()
    var title: String
    var urlString: String

    var info: BrowserTabInfo { BrowserTabInfo(title: title, urlString: urlString) }
}

final class BrowserStore: ObservableObject {
    /// The key the tabs are kept under.
    private static let tabsKey = "duckduckgo.tabs"
    /// The key the search engine is kept under.
    private static let engineKey = "duckduckgo.engine"
    /// The key the private mode is kept under.
    private static let privateKey = "duckduckgo.private"

    @Published var urlString = "https://duckduckgo.com"
    @Published var searchText = ""
    @Published var tabs: [BrowserTab]
    @Published var privateMode: Bool
    @Published var engine: BrowserCore.SearchEngine

    /// The number of the trackers that are blocked. It is counted from the
    /// rules, so it is never a number that was written down.
    var blockedTrackers: Int { BrowserCore.trackerCount }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.privateMode = defaults.bool(forKey: Self.privateKey)
        self.tabs = Self.loadTabs(defaults) ?? [BrowserTab(title: "DuckDuckGo", urlString: "https://duckduckgo.com")]
        let engineId = defaults.string(forKey: Self.engineKey) ?? "duckduckgo"
        self.engine = BrowserCore.defaultEngines.first(where: { $0.id == engineId }) ?? BrowserCore.defaultEngines[0]
    }

    private let defaults: UserDefaults

    // MARK: - The tabs

    /// Read the tabs that were saved.
    private static func loadTabs(_ defaults: UserDefaults) -> [BrowserTab]? {
        guard let data = defaults.data(forKey: tabsKey),
              let saved = try? JSONDecoder().decode([SavedTab].self, from: data) else { return nil }
        guard !saved.isEmpty else { return nil }
        return saved.map { BrowserTab(title: $0.title, urlString: $0.urlString) }
    }

    /// Write the tabs away, so they are there the next time the app opens.
    private func saveTabs() {
        let saved = tabs.map { SavedTab(title: $0.title, urlString: $0.urlString) }
        if let data = try? JSONEncoder().encode(saved) {
            defaults.set(data, forKey: Self.tabsKey)
        }
    }

    // MARK: - Searching

    func search() {
        let text = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        guard let destination = BrowserCore.destination(for: text, engine: engine) else { return }
        load(urlString: destination, title: text)
    }

    func load(urlString: String, title: String) {
        self.urlString = urlString
        if let index = tabs.firstIndex(where: { $0.urlString == urlString }) {
            tabs[index].title = title
        } else {
            tabs.append(BrowserTab(title: title, urlString: urlString))
        }
        searchText = ""
        saveTabs()
    }

    func select(_ tab: BrowserTab) {
        urlString = tab.urlString
    }

    func addTab() {
        let tab = BrowserTab(title: "New tab", urlString: "https://duckduckgo.com")
        tabs.append(tab)
        urlString = tab.urlString
        saveTabs()
    }

    func close(at offsets: IndexSet) {
        for index in offsets.sorted(by: >) where tabs.indices.contains(index) {
            tabs.remove(at: index)
        }
        if tabs.isEmpty {
            addTab()
        }
        saveTabs()
    }

    // MARK: - The settings

    /// Choose the search engine.
    func chooseEngine(_ engine: BrowserCore.SearchEngine) {
        self.engine = engine
        defaults.set(engine.id, forKey: Self.engineKey)
    }

    /// Turn the private mode on or off.
    func setPrivateMode(_ enabled: Bool) {
        privateMode = enabled
        defaults.set(enabled, forKey: Self.privateKey)
    }

    /// Clear the tabs and the counters.
    func clearData() {
        tabs = [BrowserTab(title: "DuckDuckGo", urlString: "https://duckduckgo.com")]
        urlString = "https://duckduckgo.com"
        defaults.removeObject(forKey: Self.tabsKey)
    }
}

/// The tab as it is written to the storage.
private struct SavedTab: Codable {
    var title: String
    var urlString: String
}
