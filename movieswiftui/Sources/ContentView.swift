import SwiftUI

struct ContentView: View {
    @StateObject private var store = MovieStore()

    var body: some View {
        TabView {
            DiscoverView()
                .tabItem { Label("Discover", systemImage: "sparkles") }
            SearchView()
                .tabItem { Label("Search", systemImage: "magnifyingglass") }
            WatchlistView()
                .tabItem { Label("Watchlist", systemImage: "bookmark") }
        }
        .tint(.accentColor)
        .environmentObject(store)
    }
}

#Preview {
    ContentView()
}
