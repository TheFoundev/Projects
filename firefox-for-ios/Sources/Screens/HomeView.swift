import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var store: FirefoxStore
    @State private var query = ""
    @State private var showBrowser = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text("Firefox")
                            .font(.largeTitle.bold())
                        Text("A small browser shell for iOS")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }

                    HStack(spacing: 8) {
                        TextField("Search the web", text: $query)
                            .textFieldStyle(.roundedBorder)
                            .textInputAutocapitalization(.never)
                            .autocorrectionDisabled()
                            .onSubmit(openSearch)
                        Button(action: openSearch) {
                            Image(systemName: "magnifyingglass")
                        }
                        .buttonStyle(.borderedProminent)
                    }

                    Text("Shortcuts")
                        .font(.headline)

                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                        ForEach(shortcuts) { item in
                            Button {
                                store.open(urlString: item.url)
                                showBrowser = true
                            } label: {
                                VStack(alignment: .leading, spacing: 10) {
                                    Image(systemName: item.symbol)
                                        .font(.title2)
                                        .foregroundStyle(.orange)
                                    Text(item.title)
                                        .font(.subheadline.weight(.semibold))
                                        .foregroundStyle(.primary)
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding()
                                .background(Color.secondary.opacity(0.08))
                                .clipShape(RoundedRectangle(cornerRadius: 14))
                            }
                        }
                    }

                    HStack {
                        Toggle("Private mode", isOn: $store.privateMode)
                            .font(.subheadline)
                        Spacer()
                    }
                    .padding()
                    .background(Color.secondary.opacity(0.08))
                    .clipShape(RoundedRectangle(cornerRadius: 14))

                    Button {
                        store.addPrivateTab()
                    } label: {
                        Label("Open a private tab", systemImage: "eyeglasses")
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 6)
                    }
                    .buttonStyle(.bordered)
                }
                .padding()
            }
            .navigationTitle("Home")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                Button {
                    showBrowser = true
                } label: {
                    Label("Browser", systemImage: "safari")
                }
            }
            .sheet(isPresented: $showBrowser) {
                if let url = URL(string: store.urlString) {
                    BrowserScreen(url: url)
                } else {
                    Text("This address could not be opened.")
                        .padding()
                }
            }
        }
    }

    private func openSearch() {
        store.search(query)
        query = ""
        showBrowser = true
    }
}
