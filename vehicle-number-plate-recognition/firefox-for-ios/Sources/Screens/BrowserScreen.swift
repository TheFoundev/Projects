import SwiftUI

/// The window a page is shown in.
///
/// It carries the settings of the browser: the trackers are blocked with a
/// content rule list of WebKit, and a private tab uses a data store of its
/// own.
struct BrowserScreen: View {
    let url: URL

    @EnvironmentObject private var store: FirefoxStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            WebView(
                blockTrackers: store.blockTrackers,
                protectionLevel: store.protectionLevel,
                customTrackers: store.customTrackers,
                privateMode: store.privateMode,
                url: url
            )
            .navigationTitle(store.urlString)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
