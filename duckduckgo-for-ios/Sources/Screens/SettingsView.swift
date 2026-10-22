import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var store: BrowserStore
    @State private var showCleared = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Privacy") {
                    Toggle("Private mode", isOn: Binding(
                        get: { store.privateMode },
                        set: { store.setPrivateMode($0) }
                    ))
                    LabeledContent("Trackers blocked", value: "\(store.blockedTrackers)")
                    Picker("Search engine", selection: Binding(
                        get: { store.engine.id },
                        set: { id in
                            if let engine = BrowserCore.defaultEngines.first(where: { $0.id == id }) {
                                store.chooseEngine(engine)
                            }
                        }
                    )) {
                        ForEach(BrowserCore.defaultEngines) { engine in
                            Text(engine.name).tag(engine.id)
                        }
                    }
                }

                Section("Browsing data") {
                    Button("Clear tabs and counters", role: .destructive) {
                        store.clearData()
                        showCleared = true
                    }
                }

                Section("About") {
                    Text("A student project inspired by DuckDuckGo. The browser uses WKWebView, blocks the trackers of its rule list and keeps the tabs between the launches. It has no bookmarks and no history.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Settings")
            .alert("Cleared", isPresented: $showCleared) {
                Button("OK", role: .cancel) {}
            } message: {
                Text("Demo tabs and the tracker counter were reset.")
            }
        }
    }
}
