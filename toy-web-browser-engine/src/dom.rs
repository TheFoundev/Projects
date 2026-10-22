//! DOM tree, tree builder and HTML serializer.

use crate::tokenizer::{tokenize, Token};

/// The kind of a DOM node.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum NodeKind {
    Document,
    Element,
    Text,
    Comment,
}

/// A node in the document tree.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Node {
    pub kind: NodeKind,
    /// Tag name for elements, empty for text/comment nodes.
    pub name: String,
    pub attributes: Vec<(String, String)>,
    /// Raw text of a text or comment node.
    pub text: String,
    pub children: Vec<Node>,
}

impl Node {
    /// Create an element node.
    pub fn element(name: &str) -> Node {
        Node {
            kind: NodeKind::Element,
            name: name.to_string(),
            attributes: Vec::new(),
            text: String::new(),
            children: Vec::new(),
        }
    }

    /// Create a text node.
    pub fn text_node(text: &str) -> Node {
        Node {
            kind: NodeKind::Text,
            name: "#text".to_string(),
            attributes: Vec::new(),
            text: text.to_string(),
            children: Vec::new(),
        }
    }

    /// Create a comment node.
    pub fn comment(text: &str) -> Node {
        Node {
            kind: NodeKind::Comment,
            name: "#comment".to_string(),
            attributes: Vec::new(),
            text: text.to_string(),
            children: Vec::new(),
        }
    }

    /// Value of an attribute, if present.
    pub fn attribute(&self, name: &str) -> Option<&str> {
        self.attributes
            .iter()
            .find(|(key, _)| key == name)
            .map(|(_, value)| value.as_str())
    }

    /// All classes listed in the `class` attribute.
    pub fn classes(&self) -> Vec<String> {
        self.attribute("class")
            .map(|value| {
                value
                    .split_whitespace()
                    .map(|class| class.to_string())
                    .collect()
            })
            .unwrap_or_default()
    }

    /// The visible text of this subtree.
    pub fn text_content(&self) -> String {
        text_content(self)
    }

    /// The raw text of this subtree, including invisible elements.
    pub fn raw_text(&self) -> String {
        let mut output = String::new();
        collect_raw_text(self, &mut output);
        output
    }

    /// Direct child elements with the given tag name.
    pub fn children_named(&self, name: &str) -> Vec<&Node> {
        self.children
            .iter()
            .filter(|child| child.kind == NodeKind::Element && child.name == name)
            .collect()
    }

    /// Depth-first search for the first descendant (or self) with `name`.
    pub fn find(&self, name: &str) -> Option<&Node> {
        if self.kind == NodeKind::Element && self.name == name {
            return Some(self);
        }
        for child in &self.children {
            if let Some(found) = child.find(name) {
                return Some(found);
            }
        }
        None
    }

    /// Walk every element in the tree in document order.
    pub fn elements(&self) -> Vec<&Node> {
        let mut collected = Vec::new();
        self.collect_elements(&mut collected);
        collected
    }

    fn collect_elements<'a>(&'a self, collected: &mut Vec<&'a Node>) {
        if self.kind == NodeKind::Element {
            collected.push(self);
        }
        for child in &self.children {
            child.collect_elements(collected);
        }
    }
}

/// Elements that never have children and are serialized without an end tag.
pub fn is_void_element(name: &str) -> bool {
    matches!(
        name,
        "area"
            | "base"
            | "br"
            | "col"
            | "embed"
            | "hr"
            | "img"
            | "input"
            | "link"
            | "meta"
            | "param"
            | "source"
            | "track"
            | "wbr"
    )
}

/// Elements that are never rendered as content (metadata and script holders).
pub fn is_invisible_element(name: &str) -> bool {
    matches!(
        name,
        "style" | "script" | "noscript" | "template" | "head" | "title" | "meta" | "link" | "base"
    )
}

/// Elements whose end tag may be omitted in HTML.
fn closes_implicitly(open_name: &str, new_name: &str) -> bool {
    match open_name {
        "p" => matches!(
            new_name,
            "address"
                | "article"
                | "aside"
                | "blockquote"
                | "div"
                | "dl"
                | "fieldset"
                | "figcaption"
                | "figure"
                | "footer"
                | "form"
                | "h1"
                | "h2"
                | "h3"
                | "h4"
                | "h5"
                | "h6"
                | "header"
                | "hr"
                | "main"
                | "nav"
                | "ol"
                | "p"
                | "pre"
                | "section"
                | "table"
                | "ul"
        ),
        "li" => new_name == "li",
        "dt" | "dd" => matches!(new_name, "dt" | "dd"),
        "option" => matches!(new_name, "option" | "optgroup"),
        "thead" | "tbody" | "tfoot" => matches!(new_name, "tbody" | "tfoot"),
        "tr" => matches!(new_name, "tr"),
        "td" | "th" => matches!(new_name, "td" | "th" | "tr"),
        "head" => new_name == "body",
        _ => false,
    }
}

/// Build a document tree from an HTML string.
pub fn parse(html: &str) -> Node {
    let document = Node {
        kind: NodeKind::Document,
        name: "#document".to_string(),
        attributes: Vec::new(),
        text: String::new(),
        children: Vec::new(),
    };
    let mut stack: Vec<Node> = vec![document];

    for token in tokenize(html) {
        match token {
            Token::Doctype => {}
            Token::Comment(body) => {
                stack
                    .last_mut()
                    .unwrap()
                    .children
                    .push(Node::comment(&body));
            }
            Token::Text(text) => {
                stack
                    .last_mut()
                    .unwrap()
                    .children
                    .push(Node::text_node(&text));
            }
            Token::OpenTag {
                name,
                attributes,
                self_closing,
            } => {
                // Implicit end tags: <p> is closed by the next block element.
                while stack.len() > 1 {
                    let open_name = stack.last().unwrap().name.clone();
                    if closes_implicitly(&open_name, &name) {
                        let node = stack.pop().unwrap();
                        stack.last_mut().unwrap().children.push(node);
                    } else {
                        break;
                    }
                }
                let mut node = Node::element(&name);
                node.attributes = attributes;
                if self_closing || is_void_element(&name) {
                    stack.last_mut().unwrap().children.push(node);
                } else {
                    stack.push(node);
                }
            }
            Token::CloseTag(name) => {
                if is_void_element(&name) {
                    continue;
                }
                // Find the matching open element; if there is none, ignore the
                // end tag instead of unwinding the whole stack.
                let matching = stack
                    .iter()
                    .rposition(|node| node.kind == NodeKind::Element && node.name == name);
                match matching {
                    Some(position) if position > 0 => {
                        while stack.len() > position + 1 {
                            let node = stack.pop().unwrap();
                            stack.last_mut().unwrap().children.push(node);
                        }
                        let node = stack.pop().unwrap();
                        stack.last_mut().unwrap().children.push(node);
                    }
                    _ => {}
                }
            }
        }
    }

    while stack.len() > 1 {
        let node = stack.pop().unwrap();
        stack.last_mut().unwrap().children.push(node);
    }
    stack.pop().unwrap()
}

/// Escape text content for serialization.
pub fn escape_text(text: &str) -> String {
    let mut output = String::with_capacity(text.len());
    for character in text.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            other => output.push(other),
        }
    }
    output
}

/// Escape an attribute value for serialization.
pub fn escape_attribute(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    for character in value.chars() {
        match character {
            '&' => output.push_str("&amp;"),
            '"' => output.push_str("&quot;"),
            '<' => output.push_str("&lt;"),
            '>' => output.push_str("&gt;"),
            other => output.push(other),
        }
    }
    output
}

/// Serialize a tree back into HTML text.
pub fn serialize(node: &Node) -> String {
    let mut output = String::new();
    serialize_into(node, &mut output);
    output
}

fn serialize_into(node: &Node, output: &mut String) {
    match node.kind {
        NodeKind::Document => {
            for child in &node.children {
                serialize_into(child, output);
            }
        }
        NodeKind::Text => output.push_str(&escape_text(&node.text)),
        NodeKind::Comment => {
            output.push_str("<!--");
            output.push_str(&node.text);
            output.push_str("-->");
        }
        NodeKind::Element => {
            output.push('<');
            output.push_str(&node.name);
            for (key, value) in &node.attributes {
                output.push(' ');
                output.push_str(key);
                output.push_str("=\"");
                output.push_str(&escape_attribute(value));
                output.push('"');
            }
            if is_void_element(&node.name) {
                output.push('>');
                return;
            }
            output.push('>');
            for child in &node.children {
                serialize_into(child, output);
            }
            output.push_str("</");
            output.push_str(&node.name);
            output.push('>');
        }
    }
}

/// Concatenate the visible text of a subtree.
pub fn text_content(node: &Node) -> String {
    let mut output = String::new();
    collect_text(node, &mut output);
    output
}

fn collect_raw_text(node: &Node, output: &mut String) {
    if node.kind == NodeKind::Text {
        output.push_str(&node.text);
        return;
    }
    for child in &node.children {
        collect_raw_text(child, output);
    }
}

fn collect_text(node: &Node, output: &mut String) {
    match node.kind {
        NodeKind::Text => {
            output.push_str(&node.text);
            output.push('\n');
        }
        NodeKind::Element | NodeKind::Document => {
            if node.kind == NodeKind::Element && is_invisible_element(&node.name) {
                return;
            }
            for child in &node.children {
                collect_text(child, output);
            }
        }
        NodeKind::Comment => {}
    }
}

/// Render the visible text of an HTML document.
pub fn render(html: &str) -> String {
    text_content(&parse(html))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builds_nested_tree() {
        let document = parse("<html><body><h1>Title</h1></body></html>");
        let html = document.find("html").unwrap();
        assert!(html.find("h1").is_some());
        assert!(html.find("h1").unwrap().text_content().contains("Title"));
    }

    #[test]
    fn void_elements_have_no_children() {
        let document = parse("<p>a<br>b</p>");
        let paragraph = document.find("p").unwrap();
        assert!(paragraph.children_named("br").len() == 1);
        assert_eq!(paragraph.children_named("br")[0].children.len(), 0);
    }

    #[test]
    fn serializer_round_trips_the_document() {
        let source =
            "<!doctype html><html><body><p class=\"a\">Hi <b>there</b></p><br><img src=\"x.png\"></body></html>";
        let document = parse(source);
        let serialized = serialize(&document);
        let reparsed = parse(&serialized);
        assert_eq!(document, reparsed);
    }

    #[test]
    fn serializer_escapes_text_and_attributes() {
        let document = parse("<a title=\"a&amp;b\">1 &lt; 2</a>");
        let serialized = serialize(&document);
        assert!(serialized.contains("title=\"a&amp;b\""), "{serialized}");
        assert!(serialized.contains("1 &lt; 2"), "{serialized}");
    }

    #[test]
    fn unmatched_end_tag_is_ignored() {
        let document = parse("<div><span>text</span></div></p>");
        assert!(document.find("span").is_some());
    }

    #[test]
    fn implicit_paragraph_close() {
        let document = parse("<body><p>one<p>two</body>");
        let paragraphs = document
            .find("body")
            .map(|body| body.children_named("p").len())
            .unwrap_or(0);
        assert_eq!(paragraphs, 2);
    }

    #[test]
    fn text_content_joins_text_nodes() {
        let output = render("<html><body><h1>Title</h1><p>Body text</p></body></html>");
        assert!(output.contains("Title"));
        assert!(output.contains("Body text"));
        assert!(!output.contains("<h1>"));
    }
}
