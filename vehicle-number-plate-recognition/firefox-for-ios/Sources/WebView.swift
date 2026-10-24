import SwiftUI
import WebKit

struct WebView: UIViewRepresentable {
    let url: URL
    /// True when the trackers are blocked.
    var blockTrackers: Bool = true
    /// The level of the tracking protection.
    var protectionLevel: BrowserCore.ProtectionLevel = .standard
    /// The trackers the user blocks by hand.
    var customTrackers: [String] = BrowserCore.customTrackers
    /// True when the tab is in the private mode.
    var privateMode: Bool = false

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()

        // A private tab keeps its data in a store of its own, which is thrown
        // away when the app closes.
        if privateMode {
            configuration.websiteDataStore = .nonPersistent()
        }

        // The trackers are blocked with a content rule list of WebKit.
        if blockTrackers {
            let controller = WKUserContentController()
            let json = BrowserCore.contentRuleListJSON(level: protectionLevel, custom: customTrackers)
            if let rules = try? WKContentRuleListStore.default().compileContentRuleList(
                forIdentifier: "firefox.trackers.\(protectionLevel.rawValue)",
                encodedContentRuleList: Data(json.utf8)
            ) {
                controller.add(rules)
            }
            configuration.userContentController = controller
        }

        let view = WKWebView(frame: .zero, configuration: configuration)
        view.allowsBackForwardNavigationGestures = true
        return view
    }

    func updateUIView(_ view: WKWebView, context: Context) {
        guard let url else { return }
        if view.url != url {
            view.load(URLRequest(url: url))
        }
    }

    final class Coordinator {}
}
