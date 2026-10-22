import XCTest
@testable import MoviesSwiftUI

final class MovieCoreTests: XCTestCase {

    private func info(
        id: Int = 1,
        title: String = "A film",
        year: Int = 2020,
        genres: [String] = ["Drama"],
        overview: String = "An overview",
        rating: Double = 7.5,
        runtime: Int = 120,
        posterURL: String = ""
    ) -> MovieInfo {
        MovieInfo(
            id: id, title: title, year: year, genres: genres, overview: overview,
            rating: rating, runtime: runtime, posterURL: posterURL
        )
    }

    // MARK: - The answer of the API

    func testAFilmOfTheApiIsTurnedIntoTheShapeOfTheApp() {
        let movie = MovieCore.movie(from: [
            "id": 603,
            "title": "The Matrix",
            "overview": "A hacker learns the truth.",
            "vote_average": 8.2,
            "runtime": 136,
            "release_date": "1999-03-31",
            "poster_path": "/f89U3ADr1oiF1s9GkdPOEpXUk5H.jpg",
            "genres": [["id": 28, "name": "Action"], ["id": 878, "name": "Science Fiction"]],
        ])

        XCTAssertNotNil(movie)
        XCTAssertEqual(movie?.id, 603)
        XCTAssertEqual(movie?.title, "The Matrix")
        XCTAssertEqual(movie?.year, 1999)
        XCTAssertEqual(movie?.rating, 8.2)
        XCTAssertEqual(movie?.runtime, 136)
        XCTAssertEqual(movie?.genres.count, 2)
        XCTAssertEqual(movie?.genres.first, "Action")
        XCTAssertTrue(movie?.posterURL.contains("image.tmdb.org") ?? false)
    }

    func testAFilmWithoutTheFieldsIsRefused() {
        XCTAssertNil(MovieCore.movie(from: ["id": 1]))
        XCTAssertNil(MovieCore.movie(from: ["title": "No id"]))
    }

    func testTheFilmsOfAnAnswerAreTurned() {
        let movies = MovieCore.movies(from: [
            "results": [
                ["id": 1, "title": "One", "release_date": "2020-01-01"],
                ["id": 2, "title": "Two", "release_date": "2021-01-01"],
                ["title": "No id"],
            ]
        ])
        XCTAssertEqual(movies.count, 2)
    }

    // MARK: - The search

    func testTheSearchLooksInTheTitleTheOverviewAndTheGenres() {
        let movies = [
            info(id: 1, title: "Arrival", overview: "Linguists", genres: ["Sci-Fi"]),
            info(id: 2, title: "Paddington", overview: "A bear", genres: ["Comedy"]),
        ]
        XCTAssertEqual(MovieCore.search(movies, query: "arrival").count, 1)
        XCTAssertEqual(MovieCore.search(movies, query: "bear").count, 1)
        XCTAssertEqual(MovieCore.search(movies, query: "sci-fi").count, 1)
        XCTAssertEqual(MovieCore.search(movies, query: "").count, 2)
        XCTAssertEqual(MovieCore.search(movies, query: "nothing").count, 0)
    }

    func testTheFilmsOfAGenre() {
        let movies = [
            info(id: 1, genres: ["Drama"]),
            info(id: 2, genres: ["Comedy"]),
        ]
        XCTAssertEqual(MovieCore.search(movies, genre: "Drama").count, 1)
        XCTAssertEqual(MovieCore.search(movies, genre: "All").count, 2)
    }

    func testTheGenresOfTheFilms() {
        let movies = [
            info(id: 1, genres: ["Drama", "Comedy"]),
            info(id: 2, genres: ["Comedy", "Action"]),
        ]
        let genres = MovieCore.genres(of: movies)
        XCTAssertEqual(genres.count, 3)
        XCTAssertTrue(genres.contains("Drama"))
    }

    // MARK: - The order and the running time

    func testTheFilmsAreSortedByRating() {
        let movies = [
            info(id: 1, title: "B", rating: 6.0),
            info(id: 2, title: "A", rating: 9.0),
            info(id: 3, title: "C", rating: 7.0),
        ]
        let sorted = MovieCore.sortedByRating(movies)
        XCTAssertEqual(sorted.map(\.id), [2, 3, 1])
    }

    func testTheFilmsAreSortedByYear() {
        let movies = [
            info(id: 1, year: 2010),
            info(id: 2, year: 2022),
        ]
        XCTAssertEqual(MovieCore.sortedByYear(movies).map(\.id), [2, 1])
    }

    func testTheRunningTimeIsReadable() {
        XCTAssertEqual(MovieCore.runtime(136), "2h 16m")
        XCTAssertEqual(MovieCore.runtime(0), "—")
    }

    // MARK: - The store

    func testTheWatchlistIsKeptBetweenTwoLaunches() {
        let defaults = UserDefaults(suiteName: "movies.tests")!
        defaults.removePersistentDomain(forName: "movies.tests")

        let store = MovieStore(defaults: defaults)
        store.toggleWatchlist(603)

        let second = MovieStore(defaults: defaults)
        XCTAssertTrue(second.isInWatchlist(603))
        XCTAssertEqual(second.watchlistMovies.count, 1)

        defaults.removePersistentDomain(forName: "movies.tests")
    }

    func testTheWatchlistCanBeTakenOut() {
        let defaults = UserDefaults(suiteName: "movies.tests")!
        let store = MovieStore(defaults: defaults)

        store.toggleWatchlist(1)
        XCTAssertTrue(store.isInWatchlist(1))
        store.toggleWatchlist(1)
        XCTAssertFalse(store.isInWatchlist(1))

        defaults.removePersistentDomain(forName: "movies.tests")
    }

    func testTheSearchOfTheStore() {
        let defaults = UserDefaults(suiteName: "movies.tests")!
        let store = MovieStore(defaults: defaults)
        XCTAssertEqual(store.filtered.count, store.movies.count)
        defaults.removePersistentDomain(forName: "movies.tests")
    }
}
