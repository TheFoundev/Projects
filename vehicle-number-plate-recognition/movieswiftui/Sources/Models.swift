import Foundation
import Combine

struct Movie: Identifiable, Hashable {
    let id: Int
    var title: String
    var year: Int
    var genres: [String]
    var overview: String
    var rating: Double
    var runtime: Int
    var posterHue: Double
    var posterURL: String = ""

    /// The film as the rules take it.
    var info: MovieInfo {
        MovieInfo(
            id: id, title: title, year: year, genres: genres, overview: overview,
            rating: rating, runtime: runtime, posterURL: posterURL
        )
    }
}

let sampleMovies = [
    Movie(id: 1, title: "Arrival", year: 2016, genres: ["Sci-Fi", "Drama"],
          overview: "A linguist is recruited to communicate with visitors whose language bends the shape of time.",
          rating: 7.9, runtime: 116, posterHue: 0.58),
    Movie(id: 2, title: "Paddington 2", year: 2017, genres: ["Comedy", "Family"],
          overview: "A polite bear settles into community life and ends up trying to clear his name.",
          rating: 7.8, runtime: 103, posterHue: 0.09),
    Movie(id: 3, title: "The Social Network", year: 2010, genres: ["Drama", "History"],
          overview: "The messy early years of a social network, told through depositions and dorm rooms.",
          rating: 7.8, runtime: 120, posterHue: 0.62),
    Movie(id: 4, title: "Spider-Man: Into the Spider-Verse", year: 2018, genres: ["Animation", "Action"],
          overview: "A teenager discovers that many versions of Spider-Man share the same multiverse.",
          rating: 8.4, runtime: 117, posterHue: 0.92),
    Movie(id: 5, title: "The Farewell", year: 2019, genres: ["Drama", "Comedy"],
          overview: "A family gathers in China and decides not to tell the grandmother about her diagnosis.",
          rating: 7.5, runtime: 100, posterHue: 0.33),
    Movie(id: 6, title: "Mad Max: Fury Road", year: 2015, genres: ["Action", "Adventure"],
          overview: "A chase across a desert wasteland becomes a story about escape and trust.",
          rating: 8.1, runtime: 120, posterHue: 0.04),
    Movie(id: 7, title: "Everything Everywhere All at Once", year: 2022, genres: ["Sci-Fi", "Comedy"],
          overview: "A laundromat owner is pulled into a multiverse fight while her family falls apart.",
          rating: 7.8, runtime: 139, posterHue: 0.78),
    Movie(id: 8, title: "The Iron Giant", year: 1999, genres: ["Animation", "Family"],
          overview: "A boy befriends a giant robot and tries to hide it from a suspicious town.",
          rating: 8.1, runtime: 86, posterHue: 0.55),
]

final class MovieStore: ObservableObject {
    private static let watchlistKey = "movies.watchlist"

    @Published var watchlist: Set<Int>
    @Published var query = ""
    @Published var movies: [Movie]

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.movies = sampleMovies
        self.watchlist = Set(defaults.array(forKey: Self.watchlistKey) as? [Int] ?? [])
    }

    /// The films that match the search and the genre.
    var filtered: [Movie] {
        let ids = MovieCore.search(movies.map(\.info), query: query).map(\.id)
        return movies.filter { ids.contains($0.id) }
    }

    /// The films of the watchlist.
    var watchlistMovies: [Movie] {
        movies.filter { watchlist.contains($0.id) }
    }

    /// The genres of the films the app has.
    var genres: [String] {
        MovieCore.genres(of: movies.map(\.info))
    }

    /// Add a film to the watchlist, or take it out.
    func toggleWatchlist(_ id: Int) {
        if watchlist.contains(id) {
            watchlist.remove(id)
        } else {
            watchlist.insert(id)
        }
        defaults.set(Array(watchlist), forKey: Self.watchlistKey)
    }

    /// True when the film is in the watchlist.
    func isInWatchlist(_ id: Int) -> Bool {
        watchlist.contains(id)
    }

    /// The films of the watchlist, the best rated first.
    var watchlistByRating: [Movie] {
        let ids = MovieCore.sortedByRating(watchlistMovies.map(\.info)).map(\.id)
        return watchlistMovies.filter { ids.contains($0.id) }
    }
}
