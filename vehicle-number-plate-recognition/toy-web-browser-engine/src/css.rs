//! A small CSS engine: stylesheet parsing, selector matching and cascade.

use std::collections::HashMap;

use crate::dom::{is_invisible_element, is_void_element, Node, NodeKind};

/// A compound selector such as `div.card#main`.
#[derive(Clone, Debug, PartialEq, Eq, Default)]
pub struct SimpleSelector {
    /// `None` matches any element (`*`).
    pub tag: Option<String>,
    pub id: Option<String>,
    pub classes: Vec<String>,
}

impl SimpleSelector {
    /// Parse a single compound selector.
    pub fn parse(text: &str) -> SimpleSelector {
        let mut selector = SimpleSelector::default();
        let mut rest = text.trim();
        if rest == "*" {
            return selector;
        }
        while let Some(stripped) = rest.strip_prefix('*') {
            rest = stripped;
        }
        let name_end = rest
            .find(|character: char| ['.', '#'].contains(&character))
            .unwrap_or(rest.len());
        let name = &rest[..name_end];
        if !name.is_empty() {
            selector.tag = Some(name.to_ascii_lowercase());
        }
        rest = &rest[name_end..];
        while let Some(remainder) = rest.strip_prefix('.') {
            let end = remainder
                .find(|character: char| ['.', '#'].contains(&character))
                .unwrap_or(remainder.len());
            selector.classes.push(remainder[..end].to_ascii_lowercase());
            rest = &remainder[end..];
        }
        while let Some(remainder) = rest.strip_prefix('#') {
            let end = remainder
                .find(|character: char| ['.', '#'].contains(&character))
                .unwrap_or(remainder.len());
            selector.id = Some(remainder[..end].to_ascii_lowercase());
            rest = &remainder[end..];
        }
        selector
    }

    /// Does this selector match the given element?
    pub fn matches(&self, node: &Node) -> bool {
        if node.kind != NodeKind::Element {
            return false;
        }
        if let Some(tag) = &self.tag {
            if node.name != *tag {
                return false;
            }
        }
        if let Some(id) = &self.id {
            if node.attribute("id").map(|value| value.to_ascii_lowercase()) != Some(id.clone()) {
                return false;
            }
        }
        if !self.classes.is_empty() {
            let classes: Vec<String> = node
                .classes()
                .into_iter()
                .map(|class| class.to_ascii_lowercase())
                .collect();
            for required in &self.classes {
                if !classes.contains(required) {
                    return false;
                }
            }
        }
        true
    }
}

/// A full selector: a chain of compound selectors joined by descendant
/// combinators.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Selector {
    pub parts: Vec<SimpleSelector>,
}

impl Selector {
    /// Parse a descendant-combinator selector.
    pub fn parse(text: &str) -> Selector {
        let parts = text.split_whitespace().map(SimpleSelector::parse).collect();
        Selector { parts }
    }

    /// Specificity of the selector, as a comparable number.
    pub fn specificity(&self) -> u32 {
        let mut ids = 0;
        let mut classes = 0;
        let mut types = 0;
        for part in &self.parts {
            if part.id.is_some() {
                ids += 1;
            }
            classes += part.classes.len() as u32;
            if part.tag.is_some() {
                types += 1;
            }
        }
        ids * 10_000 + classes * 100 + types
    }

    /// Does this selector match `node` in the context of its ancestors?
    pub fn matches(&self, node: &Node, ancestors: &[&Node]) -> bool {
        let count = self.parts.len();
        if count == 0 {
            return false;
        }
        if !self.parts[count - 1].matches(node) {
            return false;
        }
        if count == 1 {
            return true;
        }
        self.matches_ancestors(ancestors, count - 2)
    }

    fn matches_ancestors(&self, ancestors: &[&Node], index: usize) -> bool {
        let required = &self.parts[index];
        let mut position = ancestors.len();
        while position > 0 {
            position -= 1;
            if !required.matches(ancestors[position]) {
                continue;
            }
            if index == 0 {
                return true;
            }
            if self.matches_ancestors(&ancestors[..position], index - 1) {
                return true;
            }
        }
        false
    }
}

/// A single CSS rule: a selector plus its declarations.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct StyleRule {
    pub selector: Selector,
    pub declarations: Vec<(String, String)>,
}

impl StyleRule {
    /// Specificity of the rule's selector.
    pub fn specificity(&self) -> u32 {
        self.selector.specificity()
    }
}

/// Parse a stylesheet into a list of rules.
///
/// Comments are stripped, at-rules are ignored and declaration blocks that
/// cannot be parsed are skipped.
pub fn parse_stylesheet(css: &str) -> Vec<StyleRule> {
    let without_comments = strip_comments(css);
    let mut rules = Vec::new();
    let mut rest = without_comments.as_str();
    while let Some(open) = rest.find('{') {
        let prelude = rest[..open].trim();
        let Some(close_offset) = rest[open..].find('}') else {
            break;
        };
        let body = &rest[open + 1..open + close_offset];
        let after = &rest[open + close_offset + 1..];
        if !prelude.starts_with('@') {
            let declarations = parse_declarations(body);
            if !declarations.is_empty() {
                for selector_text in prelude.split(',') {
                    let selector_text = selector_text.trim();
                    if selector_text.is_empty() {
                        continue;
                    }
                    rules.push(StyleRule {
                        selector: Selector::parse(selector_text),
                        declarations: declarations.clone(),
                    });
                }
            }
        }
        rest = after;
    }
    rules
}

fn strip_comments(css: &str) -> String {
    let mut output = String::with_capacity(css.len());
    let mut characters = css.chars().peekable();
    while let Some(character) = characters.next() {
        if character == '/' && characters.peek() == Some(&'*') {
            characters.next();
            let mut previous = '\0';
            for inner in characters.by_ref() {
                if previous == '*' && inner == '/' {
                    break;
                }
                previous = inner;
            }
            output.push(' ');
            continue;
        }
        output.push(character);
    }
    output
}

/// Parse a declaration block into `(property, value)` pairs.
pub fn parse_declarations(body: &str) -> Vec<(String, String)> {
    let mut declarations = Vec::new();
    for statement in body.split(';') {
        let Some(colon) = statement.find(':') else {
            continue;
        };
        let property = statement[..colon].trim().to_ascii_lowercase();
        let value = statement[colon + 1..].trim().to_string();
        if property.is_empty() || value.is_empty() {
            continue;
        }
        declarations.push((property, value));
    }
    declarations
}

/// Properties that are inherited by children.
const INHERITED_PROPERTIES: &[&str] = &[
    "color",
    "font-family",
    "font-size",
    "font-style",
    "font-weight",
    "letter-spacing",
    "line-height",
    "text-align",
    "text-transform",
    "visibility",
    "white-space",
    "word-spacing",
];

/// The computed style of a single element.
#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct ComputedStyle {
    pub declarations: HashMap<String, String>,
}

impl ComputedStyle {
    /// Value of a property, if it was set.
    pub fn get(&self, property: &str) -> Option<&str> {
        self.declarations.get(property).map(|value| value.as_str())
    }

    /// Value of a property, or the supplied fallback.
    pub fn get_or<'a>(&'a self, property: &str, fallback: &'a str) -> &'a str {
        self.get(property).unwrap_or(fallback)
    }

    /// Numeric value of a length property, in pixels. Percentages are
    /// resolved against `basis` when it is supplied.
    pub fn length(&self, property: &str, basis: Option<f64>) -> Option<f64> {
        let raw = self.get(property)?;
        let raw = raw.trim();
        if raw.eq_ignore_ascii_case("auto") || raw.eq_ignore_ascii_case("none") {
            return None;
        }
        if let Some(number) = raw.strip_suffix('%') {
            let percent: f64 = number.trim().parse().ok()?;
            return Some(basis? * percent / 100.0);
        }
        let number: f64 = raw.trim_end_matches("px").trim().parse().ok()?;
        Some(number)
    }
}

/// Compute the style of `node` given its ancestors, the applicable rules and
/// the inherited style of its parent.
pub fn compute_style(
    node: &Node,
    ancestors: &[&Node],
    rules: &[StyleRule],
    parent_style: &ComputedStyle,
) -> ComputedStyle {
    let mut matched: Vec<&StyleRule> = rules
        .iter()
        .filter(|rule| rule.selector.matches(node, ancestors))
        .collect();
    matched.sort_by_key(|rule| rule.specificity());

    let mut declarations: HashMap<String, String> = HashMap::new();
    // Inherited properties come first so that more specific rules can override
    // them.
    for property in INHERITED_PROPERTIES {
        if let Some(value) = parent_style.get(property) {
            declarations.insert((*property).to_string(), value.to_string());
        }
    }
    for rule in matched {
        for (property, value) in &rule.declarations {
            declarations.insert(property.clone(), value.clone());
        }
    }
    ComputedStyle { declarations }
}

/// Compute the styles of every element in a document.
///
/// The returned map is keyed by the index of the element inside
/// [`crate::dom::Node::elements`].
pub fn compute_all_styles(root: &Node, rules: &[StyleRule]) -> Vec<ComputedStyle> {
    let mut styles = Vec::new();
    let mut ancestors: Vec<&Node> = Vec::new();
    compute_all_into(
        root,
        rules,
        &mut ancestors,
        &ComputedStyle::default(),
        &mut styles,
    );
    styles
}

fn compute_all_into<'a>(
    node: &'a Node,
    rules: &[StyleRule],
    ancestors: &mut Vec<&'a Node>,
    parent_style: &ComputedStyle,
    styles: &mut Vec<ComputedStyle>,
) {
    for child in &node.children {
        match child.kind {
            NodeKind::Element => {
                if is_void_element(&child.name) || is_invisible_element(&child.name) {
                    continue;
                }
                let style = compute_style(child, ancestors, rules, parent_style);
                styles.push(style.clone());
                ancestors.push(child);
                compute_all_into(child, rules, ancestors, &style, styles);
                ancestors.pop();
            }
            NodeKind::Document => {
                compute_all_into(child, rules, ancestors, parent_style, styles);
            }
            _ => {}
        }
    }
}

/// Helper for tests and simple use: apply a stylesheet to a document and
/// return the style of the first element matching `selector`.
pub fn style_of(root: &Node, rules: &[StyleRule], selector: &str) -> Option<ComputedStyle> {
    let target = Selector::parse(selector);
    let mut ancestors: Vec<&Node> = Vec::new();
    let mut found = None;
    search_style(
        root,
        rules,
        &mut ancestors,
        &ComputedStyle::default(),
        &target,
        &mut found,
    );
    found
}

fn search_style<'a>(
    node: &'a Node,
    rules: &[StyleRule],
    ancestors: &mut Vec<&'a Node>,
    parent_style: &ComputedStyle,
    target: &Selector,
    found: &mut Option<ComputedStyle>,
) {
    for child in &node.children {
        if child.kind != NodeKind::Element
            || is_void_element(&child.name)
            || is_invisible_element(&child.name)
        {
            continue;
        }
        let style = compute_style(child, ancestors, rules, parent_style);
        if target.matches(child, ancestors) && found.is_none() {
            *found = Some(style.clone());
        }
        ancestors.push(child);
        search_style(child, rules, ancestors, &style, target, found);
        ancestors.pop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::dom::parse;

    #[test]
    fn parses_rules_and_declarations() {
        let rules = parse_stylesheet("body { color: red; margin: 0 } /* c */ p { color: blue }");
        assert_eq!(rules.len(), 2);
        assert_eq!(
            rules[0].declarations[0],
            ("color".to_string(), "red".to_string())
        );
        assert_eq!(
            rules[1].declarations[0],
            ("color".to_string(), "blue".to_string())
        );
    }

    #[test]
    fn matches_by_tag_class_and_id() {
        let document = parse("<div id=\"main\" class=\"card wide\"><p class=\"card\">x</p></div>");
        let main = document.find("div").unwrap();
        let selector = Selector::parse("div#main.card");
        assert!(selector.matches(main, &[]));
        let paragraph = document.find("p").unwrap();
        assert!(!selector.matches(paragraph, &[]));
        assert!(Selector::parse("p.card").matches(paragraph, &[]));
    }

    #[test]
    fn matches_descendant_combinator() {
        let document = parse("<section><div><span>x</span></div></section>");
        let span = document.find("span").unwrap();
        let ancestors = vec![
            document.find("section").unwrap(),
            document.find("div").unwrap(),
        ];
        assert!(Selector::parse("section span").matches(span, &ancestors));
        assert!(!Selector::parse("section p").matches(span, &ancestors));
    }

    #[test]
    fn specificity_orders_the_cascade() {
        let rules =
            parse_stylesheet("p { color: black } .lead { color: grey } #main { color: blue }");
        let document = parse("<p id=\"main\" class=\"lead\">x</p>");
        let style = style_of(&document, &rules, "p").unwrap();
        assert_eq!(style.get("color"), Some("blue"));
    }

    #[test]
    fn inherits_color_from_parent() {
        let rules = parse_stylesheet("body { color: green }");
        let document = parse("<body><p>x</p></body>");
        let style = style_of(&document, &rules, "p").unwrap();
        assert_eq!(style.get("color"), Some("green"));
    }

    #[test]
    fn parses_lengths_and_percentages() {
        let rules = parse_stylesheet("p { width: 50%; padding: 10px }");
        let document = parse("<p>x</p>");
        let style = style_of(&document, &rules, "p").unwrap();
        assert_eq!(style.length("width", Some(400.0)), Some(200.0));
        assert_eq!(style.length("padding", None), Some(10.0));
        assert_eq!(style.length("margin", None), None);
    }
}
