import Foundation

/// The rules of the app, without any SwiftUI in them, so they can be tested
/// on their own.
public enum MovieCore {

    // MARK: - The catalogue

    /// The answer of the API of the films, in the shape the app uses.
    ///
    /// The API of TMDB answers with a dictionary per film, and the fields
    /// are named the way the API names them.
    public static func movie(from json: [String: Any]) -> MovieInfo? {
        guard let id = number(json["id"]) else { return nil }
        guard let title = json["title"] as? String else { return nil }

        let genres = (json["genres"] as? [[String: Any]] ?? [])
            .compactMap { $0["name"] as? String }
        let posterPath = (json["poster_path"] as? String) ?? ""
        let release = json["release_date"] as? String ?? ""

        return MovieInfo(
            id: id,
            title: title,
            year: Int(String(release.prefix(4))) ?? 0,
            genres: genres,
            overview: json["overview"] as? String ?? "",
            rating: number(json["vote_average"]) ?? 0,
            runtime: number(json["runtime"]) ?? 0,
            posterURL: posterPath.isEmpty ? "" : "https://image.tmdb.org/t/p/w500\(posterPath)"
        )
    }

    /// The films of an answer of the API.
    public static func movies(from json: [String: Any]) -> [MovieInfo] {
        let results = json["results"] as? [[String: Any]] ?? []
        return results.compactMap { movie(from: $0) }
    }

    private static func number(_ value: Any?) -> Double? {
        if let value = value as? Double { return value }
        if let value = value as? Int { return Double(value) }
        if let value = value as? String, let number = Double(value) { return number }
        return nil
    }

    // MARK: - The search

    /// The films that match a search.
    ///
    /// The title, the overview and the genres are searched.
    public static func search(_ movies: [MovieInfo], query: String) -> [MovieInfo] {
        let needle = query.trimmingCharacters(in: .whitespacesAndNewlines).lowercased()
        guard !needle.isEmpty else { return movies }
        return movies.filter { movie in
            let genres = movie.genres.joined(separator: " ").lowercased()
            return movie.title.lowercased().contains(needle)
                || movie.overview.lowercased().contains(needle)
                || genres.contains(needle)
        }
    }

    /// The films that match a genre.
    public static func search(_ movies: [MovieInfo], genre: String) -> [MovieInfo] {
        guard !genre.isEmpty, genre != "All" else { return movies }
        return movies.filter { $0.genres.contains(genre) }
    }

    /// The genres the app knows, from the films it has.
    public static func genres(of movies: [MovieInfo]) -> [String] {
        var seen = Set<String>()
        var result: [String] = []
        for movie in movies {
            for genre in movie.genres where !seen.contains(genre) {
                seen.insert(genre)
                result.append(genre)
            }
        }
        return result.sorted()
    }

    // MARK: - The films

    /// The films of a list, the best rated first.
    public static func sortedByRating(_ movies: [MovieInfo]) -> [MovieInfo] {
        movies.sorted { left, right in
            if left.rating == right.rating { return left.title < right.title }
            return left.rating > right.rating
        }
    }

    /// The films of a year, newest first.
    public static func sortedByYear(_ movies: [MovieInfo]) -> [MovieInfo] {
        movies.sorted { left, right in
            if left.year == right.year { return left.title < right.title }
            return left.year > right.year
        }
    }

    /// The running time of a film, the way a person reads it.
    public static func runtime(_ minutes: Int) -> String {
        guard minutes > 0 else { return "—" }
        return "\(minutes / 60)h \(minutes % 60)m"
    }
}

/// The information of a film, without the identity of the object.
public struct MovieInfo: Equatable {
    public var id: Int
    public var title: String
    public var year: Int
    public var genres: [String]
    public var overview: String
    public var rating: Double
    public var runtime: Int
    public var posterURL: String

    public init(
        id: Int,
        title: String,
        year: Int,
        genres: [String],
        overview: String,
        rating: Double,
        runtime: Int,
        posterURL: String = ""
    ) {
        self.id = id
        self.title = title
        self.year = year
        self.genres = genres
        self.overview = overview
        self.rating = rating
        self.runtime = runtime
        self.posterURL = posterURL
    }
}
