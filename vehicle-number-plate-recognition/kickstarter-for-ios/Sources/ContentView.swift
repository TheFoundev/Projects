import SwiftUI

struct ContentView: View {
    @StateObject private var store = ProjectStore()

    var body: some View {
        TabView {
            DiscoverView()
                .tabItem { Label("Discover", systemImage: "safari") }
            SavedView()
                .tabItem { Label("Saved", systemImage: "bookmark") }
            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.crop.circle") }
        }
        .tint(.accentColor)
        .environmentObject(store)
    }
}

#Preview {
    ContentView()
}
