import SwiftUI

struct ContentView: View {
    @StateObject private var store = FirefoxStore()

    var body: some View {
        TabView {
            HomeView()
                .tabItem { Label("Home", systemImage: "house") }
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
