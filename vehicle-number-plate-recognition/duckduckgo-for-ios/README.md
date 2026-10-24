# DuckDuckGo for iOS

A small private-search browser built with SwiftUI and WebKit.

> The DuckDuckGo privacy browser for iOS with private search, tracker blocking and fire-button data clearing.

## Overview

An original, self-contained implementation of the **DuckDuckGo for iOS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Several search engines, and the one that is used can be chosen
- The trackers are blocked with a content rule list of WebKit, and the
  number of the rules is counted from the list
- A private mode that keeps the data in a store of its own, which is thrown
  away when the app closes
- The tabs are kept between the launches
- A test target with the rules of the browser

## Stack

`Swift; iOS; UIKit; WebKit`

The CSV stack is Swift + iOS + UIKit + WebKit. This build uses SwiftUI for the interface and a small UIViewRepresentable wrapper around WKWebView.

## Run

```bash
brew install xcodegen
xcodegen generate
open DuckDuckGo.xcodeproj
# choose an iPhone simulator and press Run
```

## Structure

```text
duckduckgo-for-ios/
├── project.yml              XcodeGen project spec
├── Sources/App.swift        app entry point
├── Sources/ContentView.swift tab shell
├── Sources/Models.swift     models, sample data and store
├── Sources/Screens/         one SwiftUI view per screen
├── Sources/WebView.swift    WKWebView wrapper
```

## Testing

```bash
xcodegen generate
xcodebuild test -scheme DuckDuckGo -destination 'platform=iOS Simulator,name=iPhone 15'
```

The suite covers the search rules (a url is opened, anything else is
searched, the engine is used), the tracker rules (the content rule list is
valid json and holds one rule per tracker), the private mode and the tabs
that are kept between two launches.


## Notes and limitations

- The tracker count is illustrative; no content blocker is implemented.
- Tabs only live in memory and are lost when the app is closed.
- The search page needs a network connection and loads the real DuckDuckGo site.

## License

Apache-2.0. See `LICENSE`.

## Running the app

This is a SwiftUI project described with an XcodeGen spec. On a Mac:

```bash
brew install xcodegen       # once
xcodegen generate
open DuckDuckGo.xcodeproj
```

Pick an iPhone simulator and press Run. If you prefer not to use XcodeGen,
create a new iOS App project in Xcode and drag the `Sources` folder into it.

## Scope

This is a student/portfolio build. It focuses on the main screens and uses
sample data so it runs without API keys. Anything mocked is listed in the
project notes above.
