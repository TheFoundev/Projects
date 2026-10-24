# MovieSwiftUI

A small movie browser inspired by The Movie Database.

> A SwiftUI and Combine movie discovery app backed by The Movie Database API with a custom Flux store.

## Overview

An original, self-contained implementation of the **MovieSwiftUI** concept, built for the Foundev portfolio. It focuses on the core workflow described in the project brief and keeps the architecture small enough to read end to end.

## Features

- A client for the API of the films: the answer is turned into the shape the
  app uses, with the poster, the year, the genres and the rating
- The films are searched by title, overview and genre, and the genres come
  from the films the app has
- The films can be sorted by rating and by year, and the running time is
  written the way a person reads it
- The watchlist is kept between the launches
- A test target with the rules of the app

## Stack

`Swift; SwiftUI; Combine; The Movie Database API`

The CSV stack is Swift + SwiftUI + Combine + The Movie Database API. This build uses SwiftUI and ObservableObject with sample data; no API key is needed.

## Run

```bash
brew install xcodegen
xcodegen generate
open MovieSwiftUI.xcodeproj
# choose an iPhone simulator and press Run
```

## Structure

```text
movieswiftui/
├── project.yml              XcodeGen project spec
├── Sources/App.swift        app entry point
├── Sources/ContentView.swift tab shell
├── Sources/Models.swift     models, sample data and store
├── Sources/Screens/         one SwiftUI view per screen
├── Sources/Components.swift poster and genre views
```

## Testing

```bash
xcodegen generate
xcodebuild test -scheme MovieSwiftUI -destination 'platform=iOS Simulator,name=iPhone 15'
```

The suite covers the answer of the API, the search, the genres, the order and
the running time, and the watchlist that is kept between two launches.


## Notes and limitations

- Movies are sample data in `Sources/Models.swift`; no TMDB request is made.
- Posters are coloured placeholders rather than remote images.
- The watchlist is held in memory and resets when the app is closed.

## License

Apache-2.0. See `LICENSE`.

## Running the app

This is a SwiftUI project described with an XcodeGen spec. On a Mac:

```bash
brew install xcodegen       # once
xcodegen generate
open MovieSwiftUI.xcodeproj
```

Pick an iPhone simulator and press Run. If you prefer not to use XcodeGen,
create a new iOS App project in Xcode and drag the `Sources` folder into it.

## Scope

This is a student/portfolio build. It focuses on the main screens and uses
sample data so it runs without API keys. Anything mocked is listed in the
project notes above.
