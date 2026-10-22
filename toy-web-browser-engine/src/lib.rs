//! A toy browser engine.
//!
//! The crate provides a small but complete pipeline:
//!
//! * [`tokenizer`] turns HTML text into tokens,
//! * [`dom`] builds a tree from those tokens and serializes it back to HTML,
//! * [`css`] parses stylesheets, matches selectors and computes styles,
//! * [`layout`] implements the CSS box model and a block layout algorithm,
//! * [`fetch`] downloads pages and resolves relative URLs.

pub mod css;
pub mod dom;
pub mod fetch;
pub mod layout;
pub mod tokenizer;

pub use css::{compute_style, parse_stylesheet, ComputedStyle, Selector, StyleRule};
pub use dom::{parse, render, serialize, text_content, Node, NodeKind};
pub use fetch::{resolve_url, Fetcher};
pub use layout::{layout, BoxMetrics, Edges, LayoutBox};
pub use tokenizer::{decode_entities, tokenize, Token};

/// Everything needed to display a page: its tree, its styles and its layout.
pub struct RenderedPage {
    pub document: Node,
    pub rules: Vec<StyleRule>,
    pub boxes: Vec<LayoutBox>,
    pub text: String,
}

/// The CSS contained in the `<style>` elements of a document.
pub fn extract_styles(document: &Node) -> String {
    document
        .elements()
        .into_iter()
        .filter(|node| node.name == "style")
        .map(|node| node.raw_text())
        .collect::<Vec<String>>()
        .join("\n")
}

/// Parse HTML, apply a stylesheet and lay the document out.
///
/// Stylesheets inside `<style>` elements of the document are applied before
/// the stylesheet passed in `css`.
pub fn render_page(html: &str, css: &str, viewport_width: f64) -> RenderedPage {
    let document = parse(html);
    let inline_css = extract_styles(&document);
    let mut combined = inline_css;
    if !css.trim().is_empty() {
        combined.push('\n');
        combined.push_str(css);
    }
    let rules = parse_stylesheet(&combined);
    let boxes = layout(&document, &rules, viewport_width);
    let text = text_content(&document);
    RenderedPage {
        document,
        rules,
        boxes,
        text,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn end_to_end_render_of_a_document() {
        let page = render_page(
            "<html><head><style>p { color: red; width: 200px }</style></head>\
             <body><h1>Title</h1><p class=\"lead\">Body text</p></body></html>",
            "p.lead { color: blue }",
            800.0,
        );
        assert!(page.text.contains("Title"));
        assert!(page.text.contains("Body text"));
        let paragraph = page
            .boxes
            .iter()
            .find(|entry| entry.name == "p")
            .expect("p box");
        assert_eq!(paragraph.metrics.content_width, 200.0);
        assert_eq!(page.rules.len(), 2);
    }
}
