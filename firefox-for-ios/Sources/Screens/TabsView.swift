import SwiftUI

struct TabsView: View {
    @EnvironmentObject private var store: FirefoxStore
    @State private var selected: SelectedURL?

    var body: some View {
        NavigationStack {
            List {
                ForEach(store.tabs) { tab in
                    Button {
                        if let url = URL(string: tab.urlString) {
                            selected = SelectedURL(url: url)
                        }
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: tab.isPrivate ? "eyeglasses" : "globe")
                                .foregroundStyle(tab.isPrivate ? .purple : .orange)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(tab.title)
                                    .font(.subheadline.weight(.semibold))
                                    .foregroundStyle(.primary)
                                    .lineLimit(1)
                                Text(tab.isPrivate ? "Private tab" : tab.urlString)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                        }
                    }
                }
                .onDelete { offsets in
                    store.close(at: offsets)
                }
            }
            .navigationTitle("Tabs")
            .toolbar {
                Button {
                    store.addPrivateTab()
                } label: {
                    Label("Private tab", systemImage: "plus")
                }
            }
            .sheet(item: $selected) { item in
                BrowserScreen(url: item.url)
            }
        }
    }
}

struct SelectedURL: Identifiable {
    let id = UUID()
    let url: URL
}
