import SwiftUI

struct TabsView: View {
    @EnvironmentObject private var store: BrowserStore

    var body: some View {
        NavigationStack {
            List {
                ForEach(store.tabs) { tab in
                    Button {
                        store.select(tab)
                    } label: {
                        HStack(spacing: 12) {
                            Image(systemName: "globe")
                                .foregroundStyle(.blue)
                            VStack(alignment: .leading, spacing: 2) {
                                Text(tab.title)
                                    .font(.subheadline.weight(.semibold))
                                    .foregroundStyle(.primary)
                                Text(tab.urlString)
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                            Spacer()
                            if store.urlString == tab.urlString {
                                Image(systemName: "checkmark.circle.fill")
                                    .foregroundStyle(.blue)
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
                    store.addTab()
                } label: {
                    Label("New tab", systemImage: "plus")
                }
            }
        }
    }
}
