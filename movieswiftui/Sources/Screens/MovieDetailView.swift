import SwiftUI

/// The page of a film.
///
/// It shows the film, the rating, the running time and whether it is in the
/// watchlist. The button adds the film to the watchlist, and the watchlist is
/// kept between the launches.
struct MovieDetailView: View {
    let movie: Movie

    @EnvironmentObject private var store: MovieStore

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                MoviePoster(movie: movie, width: 240)

                Text(movie.title)
                    .font(.title.bold())

                Text("\(movie.year) · \(MovieCore.runtime(movie.runtime))")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                HStack(spacing: 8) {
                    Label(String(format: "%.1f", movie.rating), systemImage: "star.fill")
                        .foregroundStyle(.yellow)
                    ForEach(movie.genres, id: \.self) { genre in
                        Text(genre)
                            .font(.caption)
                            .padding(.horizontal, 8)
                            .padding(.vertical, 3)
                            .background(Color.secondary.opacity(0.15), in: Capsule())
                    }
                }

                Text(movie.overview)
                    .font(.body)

                Button(store.isInWatchlist(movie.id) ? "In your watchlist" : "Add to the watchlist") {
                    store.toggleWatchlist(movie.id)
                }
                .buttonStyle(.borderedProminent)
            }
            .padding()
        }
        .navigationTitle(movie.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}
