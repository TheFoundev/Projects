import SwiftUI

struct SearchView: View {
    @EnvironmentObject private var store: MovieStore

    var body: some View {
        NavigationStack {
            List {
                if store.filtered.isEmpty {
                    Text("No movies match that search.")
                        .foregroundStyle(.secondary)
                }

                ForEach(store.filtered) { movie in
                    NavigationLink {
                        MovieDetailView(movie: movie)
                    } label: {
                        HStack(spacing: 12) {
                            MoviePoster(movie: movie, width: 54)
                            VStack(alignment: .leading, spacing: 3) {
                                Text(movie.title)
                                    .font(.subheadline.weight(.semibold))
                                Text(movie.genres.joined(separator: " · "))
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }
            .searchable(text: $store.query, prompt: "Title or genre")
            .navigationTitle("Search")
        }
    }
}
