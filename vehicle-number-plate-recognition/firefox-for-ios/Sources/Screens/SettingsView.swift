import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var store: FirefoxStore

    var body: some View {
        NavigationStack {
            Form {
                Section("Privacy") {
                    Toggle("Block trackers", isOn: $store.blockTrackers)
                    Toggle("Private mode by default", isOn: $store.privateMode)
                    Picker("Protection", selection: Binding(
                        get: { store.protectionLevel.rawValue },
                        set: { name in
                            if let level = BrowserCore.ProtectionLevel.named(name) {
                                store.setProtectionLevel(level)
                            }
                        }
                    )) {
                        ForEach(BrowserCore.ProtectionLevel.allCases, id: \.rawValue) { level in
                            Text(level.rawValue.capitalized).tag(level.rawValue)
                        }
                    }
                    LabeledContent("Trackers blocked", value: "\(store.blockedTrackerCount)")
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

                Section("Sync") {
                    Toggle("Sync bookmarks", isOn: $store.syncEnabled)
                    Text("Sync is a visual toggle in this demo. No Mozilla account is used.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("About") {
                    LabeledContent("Engine", value: "WKWebView")
                    LabeledContent("Version", value: "1.0 demo")
                    Text("A student project inspired by Firefox for iOS. It is not affiliated with Mozilla and does not include the Rust engine components. The tracking protection is a content rule list of WebKit and the tabs are kept between the launches.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Settings")
        }
    }
}
