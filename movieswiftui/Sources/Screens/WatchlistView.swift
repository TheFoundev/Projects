import SwiftUI

struct WatchlistView: View {
    @EnvironmentObject private var store: MovieStore

    var body: some View {
        NavigationStack {
            Group {
                if store.watchlistMovies.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "bookmark")
                            .font(.largeTitle)
                            .foregroundStyle(.secondary)
                        Text("Your watchlist is empty")
                            .font(.headline)
                        Text("Add a movie from its detail page.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                } else {
                    List {
                        ForEach(store.watchlistMovies) { movie in
                            NavigationLink {
                                MovieDetailView(movie: movie)
                            } label: {
                                HStack(spacing: 12) {
                                    MoviePoster(movie: movie, width: 54)
                                    VStack(alignment: .leading, spacing: 3) {
                                        Text(movie.title)
                                            .font(.subheadline.weight(.semibold))
                                        Text(String(movie.year))
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                            }
                        }
                        .onDelete { offsets in
                            for index in offsets {
                                store.toggleWatchlist(store.watchlistMovies[index].id)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Watchlist")
        }
    }
}
