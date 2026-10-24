import SwiftUI

struct DiscoverView: View {
    @EnvironmentObject private var store: MovieStore

    private var featured: [Movie] {
        Array(sampleMovies.prefix(4))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Featured")
                            .font(.title2.bold())
                        Text("A small collection, picked by hand.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .padding(.horizontal)

                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 14) {
                            ForEach(featured) { movie in
                                NavigationLink {
                                    MovieDetailView(movie: movie)
                                } label: {
                                    MoviePoster(movie: movie, width: 140)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                        .padding(.horizontal)
                    }

                    Text("Top rated")
                        .font(.title3.bold())
                        .padding(.horizontal)

                    VStack(spacing: 10) {
                        ForEach(sampleMovies.sorted { $0.rating > $1.rating }) { movie in
                            NavigationLink {
                                MovieDetailView(movie: movie)
                            } label: {
                                HStack(spacing: 12) {
                                    MoviePoster(movie: movie, width: 62)
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(movie.title)
                                            .font(.subheadline.weight(.semibold))
                                            .foregroundStyle(.primary)
                                        Text("\(String(movie.year)) · \(movie.genres.first ?? "Film")")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                        Text("★ \(String(format: "%.1f", movie.rating))")
                                            .font(.caption.weight(.bold))
                                            .foregroundStyle(.orange)
                                    }
                                    Spacer()
                                }
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal)
                }
                .padding(.vertical)
            }
            .navigationTitle("Movies")
        }
    }
}
