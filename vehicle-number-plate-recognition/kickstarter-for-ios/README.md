# Kickstarter for iOS

Browse and save crowdfunding projects in a small SwiftUI app.

> Kickstarter's open-source iOS app for discovering and backing crowdfunding projects.

## Overview

An original, self-contained implementation of the **Kickstarter for iOS** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- The projects are grouped in categories and can be searched by title, blurb
  or creator
- A pledge that is checked before it is made: the smallest pledge, the
  largest one, a project that is over and a project that is already funded
- Backing a project raises the money and the number of backers
- The saved and the backed projects are kept between the launches
- A test target with the rules of the app

## Stack

`Swift; iOS; ReactiveSwift; GraphQL`

The CSV stack is Swift + iOS + ReactiveSwift + GraphQL. This build uses plain SwiftUI state instead of ReactiveSwift and mock data instead of GraphQL.

## Run

```bash
brew install xcodegen
xcodegen generate
open Kickstarter.xcodeproj
# choose an iPhone simulator and press Run
```

## Structure

```text
kickstarter-for-ios/
├── project.yml              XcodeGen project spec
├── Sources/App.swift        app entry point
├── Sources/ContentView.swift tab shell
├── Sources/Models.swift     models, sample data and store
├── Sources/Screens/         one SwiftUI view per screen
├── Sources/Components.swift project card view
```

## Testing

```bash
xcodegen generate
xcodebuild test -scheme Kickstarter -destination 'platform=iOS Simulator,name=iPhone 15'
```

The suite covers the categories, the search, the rules of a pledge, the state
of a project, the projects that need help the most and the persistence of the
saved and the backed projects.


## Notes and limitations

- Projects are sample data in `Sources/Models.swift`; no Kickstarter API is called.
- Backing a project only updates a local set and does not process a payment.
- Saved projects and backed projects reset when the app restarts.

## License

Apache-2.0. See `LICENSE`.

## Running the app

This is a SwiftUI project described with an XcodeGen spec. On a Mac:

```bash
brew install xcodegen       # once
xcodegen generate
open Kickstarter.xcodeproj
```

Pick an iPhone simulator and press Run. If you prefer not to use XcodeGen,
create a new iOS App project in Xcode and drag the `Sources` folder into it.

## Scope

This is a student/portfolio build. It focuses on the main screens and uses
sample data so it runs without API keys. Anything mocked is listed in the
project notes above.
