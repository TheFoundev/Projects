import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var store: ProjectStore

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    HStack(spacing: 14) {
                        ZStack {
                            Circle()
                                .fill(Color.green.opacity(0.2))
                                .frame(width: 54, height: 54)
                            Text("AR")
                                .font(.headline)
                                .foregroundStyle(.green)
                        }
                        VStack(alignment: .leading, spacing: 3) {
                            Text("Alex Rivera")
                                .font(.headline)
                            Text("Backer since 2024")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.vertical, 4)
                }

                Section("Activity") {
                    LabeledContent("Projects saved", value: "\(store.saved.count)")
                    LabeledContent("Projects backed", value: "\(store.backed.count)")
                }

                Section("Settings") {
                    Label("Notifications", systemImage: "bell")
                    Label("Payment methods", systemImage: "creditcard")
                    Label("Help", systemImage: "questionmark.circle")
                }

                Section("About") {
                    Text("A student project inspired by Kickstarter. Projects and backing are mock data; there is no GraphQL API or payment flow.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Profile")
        }
    }
}
