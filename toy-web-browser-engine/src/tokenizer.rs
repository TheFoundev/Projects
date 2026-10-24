//! HTML tokenizer.
//!
//! The tokenizer turns a byte string into a flat list of tokens. It is
//! intentionally forgiving (like the HTML5 tokenizer in "script data" states
//! it is not) but it does implement the parts of the spec that matter for a
//! usable browser engine:
//!
//! * quoted attribute values may contain spaces and `>` characters,
//! * attribute values and text are entity-decoded,
//! * comments, doctypes and bogus comments are recognised,
//! * `<` followed by a non-letter is treated as literal text.

use std::collections::HashMap;

/// A single token produced by [`tokenize`].
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Token {
    Doctype,
    Comment(String),
    OpenTag {
        name: String,
        attributes: Vec<(String, String)>,
        self_closing: bool,
    },
    CloseTag(String),
    Text(String),
}

impl Token {
    /// Convenience accessor for the tag name of an open tag.
    pub fn open_tag_name(&self) -> Option<&str> {
        match self {
            Token::OpenTag { name, .. } => Some(name.as_str()),
            _ => None,
        }
    }
}

const NAMED_ENTITIES: &[(&str, &str)] = &[
    ("amp", "&"),
    ("lt", "<"),
    ("gt", ">"),
    ("quot", "\""),
    ("apos", "'"),
    ("nbsp", "\u{a0}"),
    ("copy", "\u{a9}"),
    ("reg", "\u{ae}"),
    ("hellip", "\u{2026}"),
    ("mdash", "\u{2014}"),
    ("ndash", "\u{2013}"),
    ("lsquo", "\u{2018}"),
    ("rsquo", "\u{2019}"),
    ("ldquo", "\u{201c}"),
    ("rdquo", "\u{201d}"),
    ("trade", "\u{2122}"),
    ("euro", "\u{20ac}"),
    ("pound", "\u{a3}"),
    ("yen", "\u{a5}"),
    ("sect", "\u{a7}"),
    ("para", "\u{b6}"),
    ("middot", "\u{b7}"),
    ("bull", "\u{2022}"),
    ("dagger", "\u{2020}"),
    ("permil", "\u{2030}"),
    ("deg", "\u{b0}"),
    ("plusmn", "\u{b1}"),
    ("times", "\u{d7}"),
    ("divide", "\u{f7}"),
    ("frac12", "\u{bd}"),
    ("frac14", "\u{bc}"),
    ("frac34", "\u{be}"),
    ("sup2", "\u{b2}"),
    ("sup3", "\u{b3}"),
    ("micro", "\u{b5}"),
    ("alpha", "\u{3b1}"),
    ("beta", "\u{3b2}"),
    ("gamma", "\u{3b3}"),
    ("delta", "\u{3b4}"),
    ("pi", "\u{3c0}"),
    ("sigma", "\u{3c3}"),
    ("omega", "\u{3c9}"),
    ("larr", "\u{2190}"),
    ("uarr", "\u{2191}"),
    ("rarr", "\u{2192}"),
    ("darr", "\u{2193}"),
    ("harr", "\u{2194}"),
    ("spades", "\u{2660}"),
    ("clubs", "\u{2663}"),
    ("hearts", "\u{2665}"),
    ("diams", "\u{2666}"),
];

/// Decode HTML character references in `input`.
///
/// Numeric references (`&#65;` and `&#x41;`) and the common named
/// references are supported. Unknown references are left untouched, which
/// matches browser behaviour.
pub fn decode_entities(input: &str) -> String {
    if !input.contains('&') {
        return input.to_string();
    }
    let bytes: Vec<char> = input.chars().collect();
    let mut output = String::with_capacity(input.len());
    let mut index = 0;
    while index < bytes.len() {
        if bytes[index] != '&' {
            output.push(bytes[index]);
            index += 1;
            continue;
        }
        // Find the terminating `;` within a reasonable window.
        let limit = (index + 32).min(bytes.len());
        let mut end = None;
        for (offset, character) in bytes[(index + 1)..limit].iter().enumerate() {
            let position = index + 1 + offset;
            if *character == ';' {
                end = Some(position);
                break;
            }
            if *character == '&' || character.is_whitespace() || *character == '<' {
                break;
            }
        }
        let Some(end) = end else {
            output.push('&');
            index += 1;
            continue;
        };
        let name: String = bytes[(index + 1)..end].iter().collect();
        let replacement = if let Some(digits) = name.strip_prefix('#') {
            let parsed = if let Some(hex) = digits
                .strip_prefix('x')
                .or_else(|| digits.strip_prefix('X'))
            {
                u32::from_str_radix(hex, 16).ok()
            } else {
                digits.parse::<u32>().ok()
            };
            parsed.and_then(char::from_u32).map(|c| c.to_string())
        } else {
            NAMED_ENTITIES
                .iter()
                .find(|(key, _)| *key == name)
                .map(|(_, value)| (*value).to_string())
        };
        match replacement {
            Some(text) => {
                output.push_str(&text);
                index = end + 1;
            }
            None => {
                output.push('&');
                index += 1;
            }
        }
    }
    output
}

fn is_tag_name_start(character: char) -> bool {
    character.is_ascii_alphabetic()
}

/// Parse the inside of a start tag into a name and a list of attributes.
///
/// `inner` is the raw text between `<` and `>`, without the angle brackets.
pub fn parse_start_tag(inner: &str) -> (String, Vec<(String, String)>, bool) {
    let mut characters = inner.char_indices().peekable();
    let mut name = String::new();
    let mut attributes: Vec<(String, String)> = Vec::new();
    let mut self_closing = false;

    // Tag name.
    while let Some((_, character)) = characters.peek().copied() {
        if character.is_whitespace() || character == '>' || character == '/' {
            break;
        }
        name.push(character.to_ascii_lowercase());
        characters.next();
    }

    loop {
        // Skip whitespace between attributes.
        while let Some((_, character)) = characters.peek().copied() {
            if character.is_whitespace() {
                characters.next();
            } else {
                break;
            }
        }
        let Some((_, next_character)) = characters.peek().copied() else {
            break;
        };
        if next_character == '>' {
            break;
        }
        if next_character == '/' {
            characters.next();
            // `/` immediately before `>` (or at the end of the tag) marks a
            // self-closing tag.
            match characters.peek().copied() {
                Some((_, '>')) => self_closing = true,
                None => self_closing = true,
                _ => {}
            }
            continue;
        }

        // Attribute name.
        let mut attribute_name = String::new();
        while let Some((_, character)) = characters.peek().copied() {
            if character.is_whitespace() || character == '=' || character == '>' || character == '/'
            {
                break;
            }
            attribute_name.push(character.to_ascii_lowercase());
            characters.next();
        }
        if attribute_name.is_empty() {
            characters.next();
            continue;
        }

        // Optional `=` and value.
        let mut saw_equals = false;
        let mut value = String::new();
        let mut lookahead = characters.clone();
        while let Some((_, character)) = lookahead.peek().copied() {
            if character.is_whitespace() {
                lookahead.next();
            } else {
                break;
            }
        }
        if let Some((_, '=')) = lookahead.peek().copied() {
            saw_equals = true;
            lookahead.next();
            while let Some((_, character)) = lookahead.peek().copied() {
                if character.is_whitespace() {
                    lookahead.next();
                } else {
                    break;
                }
            }
            match lookahead.peek().copied() {
                Some((_, quote @ ('"' | '\''))) => {
                    lookahead.next();
                    let mut raw = String::new();
                    while let Some((_, character)) = lookahead.peek().copied() {
                        if character == quote {
                            lookahead.next();
                            break;
                        }
                        raw.push(character);
                        lookahead.next();
                    }
                    value = decode_entities(&raw);
                }
                Some(_) => {
                    let mut raw = String::new();
                    while let Some((_, character)) = lookahead.peek().copied() {
                        if character.is_whitespace() || character == '>' {
                            break;
                        }
                        raw.push(character);
                        lookahead.next();
                    }
                    value = decode_entities(&raw);
                }
                None => {}
            }
            characters = lookahead;
        }

        if !saw_equals {
            // Boolean attribute: value is the empty string.
            value = String::new();
        }
        attributes.push((attribute_name, value));
    }

    (name, attributes, self_closing)
}

/// Tokenize an HTML document into a flat token list.
pub fn tokenize(html: &str) -> Vec<Token> {
    let characters: Vec<char> = html.chars().collect();
    let mut tokens: Vec<Token> = Vec::new();
    let mut text = String::new();
    let mut index = 0;

    macro_rules! flush_text {
        () => {
            if !text.is_empty() {
                let decoded = decode_entities(&text);
                if !decoded.trim().is_empty() {
                    tokens.push(Token::Text(decoded.trim().to_string()));
                }
                text.clear();
            }
        };
    }

    while index < characters.len() {
        if characters[index] != '<' {
            text.push(characters[index]);
            index += 1;
            continue;
        }
        let rest: String = characters[index..].iter().collect();
        if rest.starts_with("<!--") {
            flush_text!();
            match rest.find("-->") {
                Some(end) => {
                    let body: String = rest[4..end].to_string();
                    tokens.push(Token::Comment(body));
                    index += characters_of(&rest[..4 + end + 3]);
                }
                None => {
                    tokens.push(Token::Comment(
                        rest.strip_prefix("<!--").unwrap_or(&rest).to_string(),
                    ));
                    index = characters.len();
                }
            }
            continue;
        }
        if rest.starts_with("<!") {
            flush_text!();
            match rest.find('>') {
                Some(end) => {
                    tokens.push(Token::Doctype);
                    index += characters_of(&rest[..end + 1]);
                }
                None => {
                    tokens.push(Token::Doctype);
                    index = characters.len();
                }
            }
            continue;
        }
        if rest.starts_with("</") {
            let body: String = rest.strip_prefix("</").unwrap_or(&rest).to_string();
            let name: String = body
                .chars()
                .take_while(|character| !character.is_whitespace() && *character != '>')
                .collect();
            if name.is_empty() {
                text.push('<');
                index += 1;
                continue;
            }
            flush_text!();
            tokens.push(Token::CloseTag(name.to_ascii_lowercase()));
            let consumed = body
                .chars()
                .take_while(|character| !character.is_whitespace() && *character != '>')
                .count()
                + 2;
            // Skip any trailing whitespace up to and including `>`.
            let tail: String = rest[consumed..].to_string();
            let tail_trimmed = tail.trim_start();
            let extra = tail.len() - tail_trimmed.len();
            let closing = tail_trimmed.chars().next();
            match closing {
                Some('>') => index += characters_of(&rest[..consumed + extra + 1]),
                _ => index += characters_of(&rest[..consumed]),
            }
            continue;
        }
        if rest.starts_with("<?") {
            flush_text!();
            match rest.find('>') {
                Some(end) => {
                    tokens.push(Token::Comment(rest[2..end].to_string()));
                    index += characters_of(&rest[..end + 1]);
                }
                None => {
                    tokens.push(Token::Comment(
                        rest.strip_prefix("<?").unwrap_or(&rest).to_string(),
                    ));
                    index = characters.len();
                }
            }
            continue;
        }
        if rest.len() > 1 && is_tag_name_start(rest.chars().nth(1).unwrap()) {
            flush_text!();
            match find_tag_end(&rest) {
                Some(end) => {
                    let inner = &rest[1..end];
                    let (name, attributes, self_closing) = parse_start_tag(inner);
                    tokens.push(Token::OpenTag {
                        name,
                        attributes,
                        self_closing,
                    });
                    index += characters_of(&rest[..end + 1]);
                }
                None => {
                    // Unterminated tag: treat the remainder as text.
                    text.push('<');
                    index += 1;
                }
            }
            continue;
        }
        text.push('<');
        index += 1;
    }
    flush_text!();
    tokens
}

/// Number of characters in `text` (not bytes).
fn characters_of(text: &str) -> usize {
    text.chars().count()
}

/// Find the index of the `>` that closes a start tag, honouring quoted
/// attribute values that may themselves contain `>`.
fn find_tag_end(text: &str) -> Option<usize> {
    let characters: Vec<char> = text.chars().collect();
    let mut index = 1;
    let mut quote: Option<char> = None;
    while index < characters.len() {
        let character = characters[index];
        match quote {
            Some(active) => {
                if character == active {
                    quote = None;
                }
            }
            None => {
                if character == '"' || character == '\'' {
                    quote = Some(character);
                } else if character == '>' {
                    return Some(index);
                }
            }
        }
        index += 1;
    }
    None
}

/// Collect the attributes of a tag into a map, keeping the first occurrence.
pub fn attribute_map(attributes: &[(String, String)]) -> HashMap<String, String> {
    let mut map = HashMap::new();
    for (key, value) in attributes {
        map.entry(key.clone()).or_insert_with(|| value.clone());
    }
    map
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_quoted_attribute_with_spaces_and_angle_bracket() {
        let tokens = tokenize("<a href=\"/a b\" title=\"x > y\">link</a>");
        match &tokens[0] {
            Token::OpenTag {
                name, attributes, ..
            } => {
                assert_eq!(name, "a");
                assert_eq!(attribute_map(attributes).get("href").unwrap(), "/a b");
                assert_eq!(attribute_map(attributes).get("title").unwrap(), "x > y");
            }
            other => panic!("unexpected token: {other:?}"),
        }
    }

    #[test]
    fn decodes_entities_in_text_and_attributes() {
        let tokens = tokenize("<p title=\"a&amp;b\">5 &lt; 6 &#65;</p>");
        match &tokens[0] {
            Token::OpenTag { attributes, .. } => {
                assert_eq!(attribute_map(attributes).get("title").unwrap(), "a&b");
            }
            other => panic!("unexpected token: {other:?}"),
        }
        assert_eq!(tokens[1], Token::Text("5 < 6 A".to_string()));
    }

    #[test]
    fn recognises_self_closing_and_boolean_attributes() {
        let tokens = tokenize("<img src=\"a.png\" alt=\"\" />");
        match &tokens[0] {
            Token::OpenTag {
                name,
                attributes,
                self_closing,
            } => {
                assert_eq!(name, "img");
                assert!(*self_closing);
                let map = attribute_map(attributes);
                assert_eq!(map.get("src").unwrap(), "a.png");
                assert_eq!(map.get("alt").unwrap(), "");
            }
            other => panic!("unexpected token: {other:?}"),
        }
    }

    #[test]
    fn treats_stray_angle_bracket_as_text() {
        let tokens = tokenize("5 < 6");
        assert_eq!(tokens.len(), 1);
        assert_eq!(tokens[0], Token::Text("5 < 6".to_string()));
    }

    #[test]
    fn unquoted_attribute_values_stop_at_whitespace() {
        let tokens = tokenize("<a href=/about class=lead>x</a>");
        match &tokens[0] {
            Token::OpenTag { attributes, .. } => {
                let map = attribute_map(attributes);
                assert_eq!(map.get("href").unwrap(), "/about");
                assert_eq!(map.get("class").unwrap(), "lead");
            }
            other => panic!("unexpected token: {other:?}"),
        }
    }
}
