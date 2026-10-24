//! Fetching pages over HTTP and resolving relative URLs.

use std::time::Duration;

use url::Url;

use crate::dom::{parse, Node};

/// The outcome of a successful page fetch.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FetchedPage {
    /// The final URL of the page (after redirects).
    pub url: String,
    pub status: u16,
    pub content_type: String,
    pub body: String,
}

/// Errors produced while fetching.
#[derive(Debug)]
pub enum FetchError {
    /// The URL could not be parsed.
    InvalidUrl(String),
    /// The request failed (DNS, TLS, connection, timeout, ...).
    Request(String),
}

impl std::fmt::Display for FetchError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            FetchError::InvalidUrl(url) => write!(formatter, "invalid URL: {url}"),
            FetchError::Request(message) => write!(formatter, "request failed: {message}"),
        }
    }
}

impl std::error::Error for FetchError {}

/// Resolve a possibly relative `reference` against a `base` URL.
///
/// Absolute references are returned unchanged (normalized).
pub fn resolve_url(base: &str, reference: &str) -> Result<String, FetchError> {
    let reference = reference.trim();
    if reference.is_empty() {
        return Ok(base.to_string());
    }
    if let Ok(parsed_reference) = Url::parse(reference) {
        if parsed_reference.has_host() {
            return Ok(parsed_reference.to_string());
        }
    }
    let parsed_base = Url::parse(base).map_err(|_| FetchError::InvalidUrl(base.to_string()))?;
    parsed_base
        .join(reference)
        .map(|url| url.to_string())
        .map_err(|_| FetchError::InvalidUrl(reference.to_string()))
}

/// An HTTP client that can download pages.
pub struct Fetcher {
    client: reqwest::blocking::Client,
}

impl Fetcher {
    /// Create a fetcher with the given timeout and user agent.
    pub fn new(timeout: Duration, user_agent: &str) -> Fetcher {
        let client = reqwest::blocking::Client::builder()
            .timeout(timeout)
            .user_agent(user_agent)
            .build()
            .expect("failed to build the HTTP client");
        Fetcher { client }
    }

    /// Create a fetcher with the default timeout and user agent.
    pub fn default_fetcher() -> Fetcher {
        Fetcher::new(Duration::from_secs(30), "toy-web-browser-engine/0.1")
    }

    /// Download a page.
    pub fn fetch(&self, url: &str) -> Result<FetchedPage, FetchError> {
        let parsed = Url::parse(url).map_err(|_| FetchError::InvalidUrl(url.to_string()))?;
        let response = self
            .client
            .get(parsed)
            .send()
            .map_err(|error| FetchError::Request(error.to_string()))?;
        let status = response.status();
        let content_type = response
            .headers()
            .get(reqwest::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok())
            .unwrap_or("text/html")
            .to_string();
        let body = response
            .text()
            .map_err(|error| FetchError::Request(error.to_string()))?;
        Ok(FetchedPage {
            url: url.to_string(),
            status: status.as_u16(),
            content_type,
            body,
        })
    }

    /// Download a page and parse it into a document tree.
    pub fn fetch_document(&self, url: &str) -> Result<(Node, FetchedPage), FetchError> {
        let page = self.fetch(url)?;
        let document = parse(&page.body);
        Ok((document, page))
    }
}

/// Collect the `href` of every `<a>` element in a document.
pub fn extract_links(root: &Node) -> Vec<String> {
    root.elements()
        .into_iter()
        .filter(|node| node.name == "a")
        .filter_map(|node| node.attribute("href").map(|href| href.to_string()))
        .collect()
}

/// Collect the `src` of every `<img>` element in a document.
pub fn extract_images(root: &Node) -> Vec<String> {
    root.elements()
        .into_iter()
        .filter(|node| node.name == "img")
        .filter_map(|node| node.attribute("src").map(|src| src.to_string()))
        .collect()
}

/// Resolve every link of a document against the URL it was loaded from.
pub fn resolve_links(root: &Node, base_url: &str) -> Vec<String> {
    extract_links(root)
        .into_iter()
        .filter_map(|href| resolve_url(base_url, &href).ok())
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::thread;

    fn spawn_server(body: &'static str) -> (String, thread::JoinHandle<String>) {
        let listener = TcpListener::bind("127.0.0.1:0").expect("bind");
        let address = listener.local_addr().expect("addr");
        let handle = thread::spawn(move || {
            let (mut stream, _) = listener.accept().expect("accept");
            let mut buffer = [0u8; 1024];
            let _ = stream.read(&mut buffer);
            let response = format!(
                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
                body.len(),
                body
            );
            let _ = stream.write_all(response.as_bytes());
            let _ = stream.flush();
            address.to_string()
        });
        (format!("http://{}", address), handle)
    }

    #[test]
    fn resolves_relative_urls() {
        assert_eq!(
            resolve_url("https://example.com/docs/index.html", "guide.html").unwrap(),
            "https://example.com/docs/guide.html"
        );
        assert_eq!(
            resolve_url("https://example.com/docs/index.html", "/root.html").unwrap(),
            "https://example.com/root.html"
        );
        assert_eq!(
            resolve_url(
                "https://example.com/docs/index.html",
                "https://other.test/x"
            )
            .unwrap(),
            "https://other.test/x"
        );
        assert_eq!(
            resolve_url("https://example.com/docs/index.html", "../up.html").unwrap(),
            "https://example.com/up.html"
        );
    }

    #[test]
    fn rejects_invalid_base_urls() {
        assert!(resolve_url("not a url", "x.html").is_err());
    }

    #[test]
    fn fetches_a_page_over_http() {
        let (url, handle) = spawn_server("<html><body><p>hello</p></body></html>");
        let fetcher = Fetcher::default_fetcher();
        let page = fetcher.fetch(&url).expect("fetch");
        assert_eq!(page.status, 200);
        assert!(page.content_type.contains("text/html"));
        assert!(page.body.contains("hello"));
        let _ = handle.join();
    }

    #[test]
    fn fetches_and_parses_a_document() {
        let (url, handle) = spawn_server("<html><body><a href=\"/next\">next</a></body></html>");
        let fetcher = Fetcher::default_fetcher();
        let (document, page) = fetcher.fetch_document(&url).expect("fetch");
        assert_eq!(page.status, 200);
        assert_eq!(extract_links(&document), vec!["/next".to_string()]);
        assert_eq!(resolve_links(&document, &url), vec![format!("{url}/next")]);
        let _ = handle.join();
    }
}
