import SwiftUI

struct BrowseView: View {
    @EnvironmentObject private var store: BrowserStore

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                HStack(spacing: 8) {
                    TextField("Search or enter address", text: $store.searchText)
                        .textFieldStyle(.roundedBorder)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .onSubmit { store.search() }

                    Button {
                        store.search()
                    } label: {
                        Image(systemName: "magnifyingglass")
                    }
                    .buttonStyle(.borderedProminent)
                }
                .padding(.horizontal)
                .padding(.vertical, 8)

                HStack {
                    Label("\(store.blockedTrackers) trackers blocked", systemImage: "shield.lefthalf.filled")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Toggle("Private", isOn: $store.privateMode)
                        .labelsHidden()
                        .scaleEffect(0.8)
                    Text("Private")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                .padding(.horizontal)
                .padding(.bottom, 6)

                WebView(privateMode: store.privateMode, url: URL(string: store.urlString))
                    .overlay {
                        if store.privateMode {
                            VStack {
                                Text("Private mode")
                                    .font(.caption.weight(.bold))
                                Text("History is not stored in this demo.")
                                    .font(.caption2)
                            }
                            .padding(6)
                            .background(.thinMaterial)
                            .clipShape(Capsule())
                            .padding(.top, 8)
                            .frame(maxHeight: .infinity, alignment: .top)
                        }
                    }
            }
            .navigationTitle("DuckDuckGo")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}
