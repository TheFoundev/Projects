import SwiftUI

struct ProjectCard: View {
    let project: Project
    @EnvironmentObject private var store: ProjectStore

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(project.category.uppercased())
                    .font(.caption2.weight(.bold))
                    .foregroundStyle(.green)
                Spacer()
                Button {
                    store.toggleSave(project.id)
                } label: {
                    Image(systemName: store.saved.contains(project.id) ? "bookmark.fill" : "bookmark")
                        .foregroundStyle(.green)
                }
                .buttonStyle(.plain)
            }

            Text(project.title)
                .font(.headline)
                .foregroundStyle(.primary)

            Text(project.blurb)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .lineLimit(2)

            ProgressView(value: project.progress)
                .tint(.green)

            HStack(spacing: 8) {
                Text("\(Int(project.progress * 100))% funded")
                Spacer()
                Text("\(project.backers) backers")
                Text("\(project.daysLeft)d left")
            }
            .font(.caption2)
            .foregroundStyle(.secondary)
        }
        .padding(14)
        .background(Color.secondary.opacity(0.08))
        .clipShape(RoundedRectangle(cornerRadius: 14))
    }
}
