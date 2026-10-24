import SwiftUI

/// The page of a project.
///
/// It shows what the project is about, how much it has and the form to back
/// it. The pledge is checked by the rules of the app, so the button says what
/// is wrong instead of doing nothing.
struct ProjectDetailView: View {
    let project: Project

    @EnvironmentObject private var store: ProjectStore
    @State private var amount = ""
    @State private var problem: String?
    @State private var thanks = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(project.category.uppercased())
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.secondary)

                Text(project.title)
                    .font(.largeTitle.bold())

                Text("by \(project.creator)")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                Text(project.blurb)
                    .font(.body)

                VStack(alignment: .leading, spacing: 8) {
                    ProgressView(value: project.progress)
                    HStack {
                        Text("\(project.pledged) pledged")
                        Spacer()
                        Text("of \(project.goal)")
                    }
                    .font(.caption)
                    .foregroundStyle(.secondary)

                    Text("\(project.backers) backers · \(project.daysLeft) days left · \(ProjectCore.state(of: project.info))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if store.backed.contains(project.id) {
                    Label("You backed this project", systemImage: "checkmark.seal.fill")
                        .foregroundStyle(.green)
                } else {
                    VStack(alignment: .leading, spacing: 10) {
                        TextField("Amount", text: $amount)
                            .keyboardType(.numberPad)
                            .textFieldStyle(.roundedBorder)

                        if let problem {
                            Text(problem)
                                .font(.footnote)
                                .foregroundStyle(.red)
                        }

                        Button("Back this project") {
                            let value = Int(amount) ?? 0
                            if let issue = store.back(project.id, amount: value) {
                                problem = issue
                                thanks = false
                            } else {
                                problem = nil
                                thanks = true
                                amount = ""
                            }
                        }
                        .buttonStyle(.borderedProminent)
                    }
                }

                Button(store.saved.contains(project.id) ? "Saved" : "Save this project") {
                    store.toggleSave(project.id)
                }
                .buttonStyle(.bordered)
            }
            .padding()
        }
        .navigationTitle(project.title)
        .navigationBarTitleDisplayMode(.inline)
        .alert("Thank you", isPresented: $thanks) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Your pledge of \(amount) was recorded. In a real app the payment would happen here.")
        }
    }
}
