import SwiftUI

struct ContentView: View {
    @StateObject private var store = BrowserStore()

    var body: some View {
        TabView {
            BrowseView()
                .tabItem { Label("Browse", systemImage: "safari") }
            TabsView()
                .tabItem { Label("Tabs", systemImage: "square.on.square") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gearshape") }
        }
        .tint(.accentColor)
        .environmentObject(store)
    }
}

#Preview {
    ContentView()
}
