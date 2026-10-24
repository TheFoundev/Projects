import SwiftUI

struct DiscoverView: View {
    @EnvironmentObject private var store: ProjectStore
    @State private var category = "All"

    private let categories = ["All", "Technology", "Design", "Food", "Music", "Community"]

    private var visible: [Project] {
        category == "All" ? sampleProjects : sampleProjects.filter { $0.category == category }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(categories, id: \.self) { item in
                                Button {
                                    category = item
                                } label: {
                                    Text(item)
                                        .font(.caption.weight(.semibold))
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(category == item ? Color.green : Color.secondary.opacity(0.12))
                                        .foregroundStyle(category == item ? Color.white : Color.primary)
                                        .clipShape(Capsule())
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    ForEach(visible) { project in
                        NavigationLink {
                            ProjectDetailView(project: project)
                        } label: {
                            ProjectCard(project: project)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding()
            }
            .navigationTitle("Discover")
        }
    }
}
