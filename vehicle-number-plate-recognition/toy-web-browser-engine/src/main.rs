use toy_web_browser_engine::{
    fetch::Fetcher, layout::layout, parse, parse_stylesheet, render, tokenize,
};

const SAMPLE: &str = "<!doctype html><html><head><title>Demo</title></head><body><!-- page --><h1>Hello</h1><p>A tiny browser engine.</p><a href=\"https://example.com\">link</a></body></html>";

fn main() {
    let arguments: Vec<String> = std::env::args().collect();
    let mut fetch_url: Option<String> = None;
    let mut file_path: Option<String> = None;
    let mut index = 1;
    while index < arguments.len() {
        match arguments[index].as_str() {
            "--fetch" => {
                index += 1;
                fetch_url = arguments.get(index).cloned();
            }
            "--file" => {
                index += 1;
                file_path = arguments.get(index).cloned();
            }
            "--help" | "-h" => {
                println!("usage: toy_web_browser_engine [--fetch <url>] [--file <path>]");
                return;
            }
            other => {
                if other.starts_with("http://") || other.starts_with("https://") {
                    fetch_url = Some(other.to_string());
                } else {
                    file_path = Some(other.to_string());
                }
            }
        }
        index += 1;
    }

    let (html, base_url) = match (&fetch_url, &file_path) {
        (Some(url), _) => {
            let fetcher = Fetcher::default_fetcher();
            match fetcher.fetch(url) {
                Ok(page) => (page.body, Some(page.url)),
                Err(error) => {
                    eprintln!("could not fetch {}: {}", url, error);
                    std::process::exit(1);
                }
            }
        }
        (None, Some(path)) => {
            let html = std::fs::read_to_string(path).unwrap_or_else(|error| {
                eprintln!("could not read {}: {}", path, error);
                std::process::exit(1);
            });
            (html, None)
        }
        (None, None) => (SAMPLE.to_string(), None),
    };

    println!("tokens: {}", tokenize(&html).len());

    let document = parse(&html);
    let rules = parse_stylesheet("");
    let boxes = layout(&document, &rules, 1024.0);
    println!("boxes: {}", boxes.len());
    for entry in &boxes {
        println!(
            "  <{}> x={:.0} y={:.0} w={:.0} h={:.0}",
            entry.name,
            entry.x,
            entry.y,
            entry.width(),
            entry.height()
        );
    }

    if let Some(base) = base_url {
        let links = toy_web_browser_engine::fetch::resolve_links(&document, &base);
        println!("--- resolved links ---");
        for link in links {
            println!("  {link}");
        }
    }

    println!("--- rendered text ---");
    print!("{}", render(&html));
}
