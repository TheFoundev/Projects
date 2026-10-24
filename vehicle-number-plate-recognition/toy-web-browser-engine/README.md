# Toy Web Browser Engine

A small, self-contained browser engine in Rust: HTML tokenizer, DOM tree builder, HTML serializer, CSS cascade with selector matching, a CSS box-model layout engine and an HTTP fetcher.

## Overview

An original implementation of the **Toy Web Browser Engine** concept, built for the Foundev portfolio. The pipeline mirrors what a real engine does, in a size you can read end to end:

```text
HTML text ──▶ tokenizer ──▶ tree builder ──▶ DOM ──▶ serializer
                                    │
                                    ├──▶ CSS parser ──▶ selector matching ──▶ computed styles
                                    └──▶ layout engine ──▶ boxes (content/padding/border/margin)
```

## Features

- HTML tokenizer with tags, attributes, text, comments, doctypes and self-closing tags
- Attribute values may contain spaces, `>` characters and character references
- Entity decoding for text and attribute values (named and numeric)
- Tree builder with void-element handling, implicit end tags and stray end-tag recovery
- DOM with element, text and comment nodes
- HTML serializer that round-trips the parsed document
- CSS parser: rules, declarations, comments, selector lists
- Selector matching for type, `.class`, `#id` and descendant combinators, with specificity-based cascade and property inheritance
- Layout engine implementing the CSS box model (content-box and border-box), margin/border/padding, percentage widths and block flow
- HTTP fetching with URL resolution for relative links and assets
- 34 unit and integration tests

## Stack

`Rust`
The stack is Rust. The engine depends on `reqwest` (blocking client with rustls) and `url` (RFC 3986 URL parsing and resolution); everything else is handwritten.

## Run

```bash
cargo run --release                       # render the built-in sample page
cargo run -- --file page.html             # render a local HTML file
cargo run -- --fetch https://example.com  # download a page and resolve its links
```

## Structure

```text
toy-web-browser-engine/
├── src/lib.rs           public API (parse, render_page, re-exports)
├── src/tokenizer.rs     HTML tokenizer and entity decoding
├── src/dom.rs           DOM tree, tree builder and serializer
├── src/css.rs           stylesheet parsing, selector matching and cascade
├── src/layout.rs        box model and block layout
├── src/fetch.rs         HTTP fetching and URL resolution
├── src/main.rs          command line demo
├── tests/integration.rs end-to-end tests
└── Cargo.toml
```

## Testing

```bash
cargo test
```

The suite covers the tokenizer (quoted attributes, entities, self-closing tags, stray `<`), the tree builder (void elements, implicit closes, unmatched end tags), the serializer (round-trip and escaping), CSS (parsing, specificity, inheritance, lengths), the box model (content-box, border-box, auto width, percentages, vertical stacking) and fetching (URL resolution plus a real HTTP round-trip against a local server).

## Notes and limitations

- Malformed HTML is handled leniently; the full HTML5 tree-construction algorithm (active formatting elements, adoption agency) is not implemented.
- The layout engine implements block flow only: there is no inline layout, no flexbox or grid, no text measurement and no painting.
- CSS support covers type, class, id and descendant selectors; attribute selectors, pseudo-classes and at-rules are not implemented.
- There is no JavaScript engine.
- `reqwest` is used with the `rustls-tls` backend; plain HTTP and HTTPS are supported.

## License

MIT. See `LICENSE`.
