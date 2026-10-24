import SwiftUI

struct SavedView: View {
    @EnvironmentObject private var store: ProjectStore

    var body: some View {
        NavigationStack {
            Group {
                if store.savedProjects.isEmpty {
                    VStack(spacing: 8) {
                        Image(systemName: "bookmark")
                            .font(.largeTitle)
                            .foregroundStyle(.secondary)
                        Text("Nothing saved yet")
                            .font(.headline)
                        Text("Tap the bookmark on a project to keep it here.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else {
                    ScrollView {
                        VStack(spacing: 12) {
                            ForEach(store.savedProjects) { project in
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
                }
            }
            .navigationTitle("Saved")
        }
    }
}
