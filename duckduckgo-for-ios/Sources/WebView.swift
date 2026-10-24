import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {
    let url: URL?
    /// True when the window is in the private mode.
    var privateMode: Bool = false

    func makeCoordinator() -> Coordinator {
        Coordinator(privateMode: privateMode)
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()

        // The private mode keeps the data in a store of its own, which is
        // thrown away when the app closes.
        if context.coordinator.privateMode {
            configuration.websiteDataStore = .nonPersistent()
        } else if let store = WKWebsiteDataStore(forIdentifier: WKWebsiteDataStore.default().identifier) {
            configuration.websiteDataStore = store
        }

        // The trackers are blocked with a content rule list, the way the
        // blocker of a real browser works.
        let controller = WKUserContentController()
        if let rules = try? WKContentRuleListStore.default()
            .compileContentRuleList(
                forIdentifier: "actual.trackers",
                encodedContentRuleList: BrowserCore.contentRuleListJSON().data(using: .utf8) ?? Data()
            ) {
            controller.add(rules)
        }
        configuration.userContentController = controller

        let view = WKWebView(frame: .zero, configuration: configuration)
        view.allowsBackForwardNavigationGestures = true
        view.isOpaque = false
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {
        guard let url else { return }
        if view.url != url {
            view.load(URLRequest(url: url))
        }
    }

    final class Coordinator {
        let privateMode: Bool

        init(privateMode: Bool) {
            self.privateMode = privateMode
        }
    }
}
