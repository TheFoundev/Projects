use toy_web_browser_engine::fetch::{resolve_links, Fetcher};
use toy_web_browser_engine::{layout, parse, parse_stylesheet, render, serialize};

const PAGE: &str = r#"<!doctype html>
<html>
  <head>
    <title>Demo</title>
    <style>
      body { margin: 0 }
      .card { padding: 10px; border-width: 2px }
      #hero { width: 400px; height: 50px }
    </style>
  </head>
  <body>
    <h1 id="hero">Hello</h1>
    <p class="card">Body text</p>
    <a href="/next">next</a>
  </body>
</html>"#;

#[test]
fn parses_and_serializes_a_full_page() {
    let document = parse(PAGE);
    assert!(document.find("title").is_some());
    let serialized = serialize(&document);
    assert!(serialized.contains("<title>Demo</title>"));
    assert!(serialized.contains("id=\"hero\""));
    // The document must round-trip.
    assert_eq!(parse(&serialized), document);
}

#[test]
fn renders_visible_text_only() {
    let text = render(PAGE);
    assert!(text.contains("Hello"));
    assert!(text.contains("Body text"));
    assert!(!text.contains("body { margin"));
}

#[test]
fn applies_the_box_model() {
    let document = parse(PAGE);
    let rules = parse_stylesheet("body { margin: 0 } .card { padding: 10px; border-width: 2px } #hero { width: 400px; height: 50px }");
    let boxes = layout(&document, &rules, 800.0);

    let hero = boxes
        .iter()
        .find(|entry| entry.id.as_deref() == Some("hero"))
        .unwrap();
    assert_eq!(hero.metrics.content_width, 400.0);
    assert_eq!(hero.metrics.content_height, 50.0);

    let card = boxes.iter().find(|entry| entry.name == "p").unwrap();
    // Auto width shrinks the content box so that the border box fills the
    // containing block.
    assert_eq!(card.width(), 800.0);
    assert_eq!(card.metrics.content_width, 800.0 - 20.0 - 4.0);
    assert_eq!(card.metrics.padding.top, 10.0);
    assert_eq!(card.metrics.border.left, 2.0);
}

#[test]
fn resolves_links_against_the_page_url() {
    let document = parse(PAGE);
    let links = resolve_links(&document, "https://example.com/docs/index.html");
    assert_eq!(links, vec!["https://example.com/next".to_string()]);
}

#[test]
fn fetches_a_page_from_a_local_server() {
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::thread;

    let listener = TcpListener::bind("127.0.0.1:0").expect("bind");
    let address = listener.local_addr().expect("addr");
    let handle = thread::spawn(move || {
        let (mut stream, _) = listener.accept().expect("accept");
        let mut buffer = [0u8; 1024];
        let _ = stream.read(&mut buffer);
        let body = "<html><body><h1>Remote</h1></body></html>";
        let response = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
            body.len(),
            body
        );
        let _ = stream.write_all(response.as_bytes());
        let _ = stream.flush();
    });

    let url = format!("http://{address}/");
    let fetcher = Fetcher::default_fetcher();
    let (document, page) = fetcher.fetch_document(&url).expect("fetch");
    assert_eq!(page.status, 200);
    assert!(document.find("h1").is_some());
    assert!(render(&page.body).contains("Remote"));
    let _ = handle.join();
}
