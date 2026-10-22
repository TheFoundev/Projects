# Firefox for iOS

A simple SwiftUI browser shell with shortcuts and tabs.

> Mozilla's Firefox browser for iOS with tab management, sync and content blocking.

## Overview

An original, self-contained implementation of the **Firefox for iOS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- Three levels of the tracking protection (standard, strict and the trackers
  the user picks), applied with a content rule list of WebKit
- Several search engines, and the one that is used can be chosen
- A private mode that keeps the data in a store of its own
- The tabs are kept between the launches
- A test target with the rules of the browser

## Stack

`Swift; iOS; WebKit; Rust components`

The CSV stack is Swift + iOS + WebKit + Rust components. This build is the SwiftUI/WebKit shell; the Rust engine components are out of scope.

## Run

```bash
brew install xcodegen
xcodegen generate
open Firefox.xcodeproj
# choose an iPhone simulator and press Run
```

## Structure

```text
firefox-for-ios/
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
xcodebuild test -scheme Firefox -destination 'platform=iOS Simulator,name=iPhone 15'
```

The suite covers the search rules, the levels of the tracking protection (the
rules, the number of the blockers and the content rule list), the tabs that
are kept between two launches and the settings that are kept.


## Notes and limitations

- Search uses Google in this demo; Firefox's real search configuration is not included.
- Tracking protection and sync are UI toggles with no engine behind them.
- Pages are loaded in a sheet and tabs are kept in memory only.

## License

MPL-2.0. See `LICENSE`.

## Running the app

This is a SwiftUI project described with an XcodeGen spec. On a Mac:

```bash
brew install xcodegen       # once
xcodegen generate
open Firefox.xcodeproj
```

Pick an iPhone simulator and press Run. If you prefer not to use XcodeGen,
create a new iOS App project in Xcode and drag the `Sources` folder into it.

## Scope

This is a student/portfolio build. It focuses on the main screens and uses
sample data so it runs without API keys. Anything mocked is listed in the
project notes above.
