import SwiftUI

/// The poster of a film.
///
/// When the film has a poster the picture is shown, and when it has none the
/// colour of the film is used with its title on it.
struct MoviePoster: View {
    let movie: Movie
    var width: CGFloat = 130

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            poster
                .frame(width: width, height: width * 1.45)
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

            Text(movie.title)
                .font(.subheadline.weight(.semibold))
                .lineLimit(1)
                .frame(width: width, alignment: .leading)

            Text(String(movie.year))
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    /// The picture of the film, or the colour when there is none.
    @ViewBuilder
    private var poster: some View {
        if !movie.posterURL.isEmpty, let url = URL(string: movie.posterURL) {
            AsyncImage(url: url) { image in
                image.resizable().aspectRatio(contentMode: .fill)
            } placeholder: {
                placeholder
            }
        } else {
            placeholder
        }
    }

    /// The colour of the film with its first letter on it.
    private var placeholder: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(hue: movie.posterHue, saturation: 0.5, brightness: 0.82),
                    Color(hue: movie.posterHue, saturation: 0.72, brightness: 0.42)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            Text(String(movie.title.prefix(1)))
                .font(.system(size: 42, weight: .black))
                .foregroundStyle(.white.opacity(0.85))
                .padding(10)
        }
    }
}

struct GenrePills: View {
    let genres: [String]

    var body: some View {
        HStack(spacing: 6) {
            ForEach(genres, id: \.self) { genre in
                Text(genre)
                    .font(.caption2.weight(.semibold))
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(Color.secondary.opacity(0.12))
                    .clipShape(Capsule())
            }
        }
    }
}
