"""A small same-host crawler with an HTML link parser."""
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip()


def make_site(base, quick=True):
    site = base / "site"
    (site / "guides").mkdir(parents=True, exist_ok=True)
    pages = {
        "index.html": '<title>Home</title><a href="guides/start.html">start</a>'
                      '<a href="guides/tools.html">tools</a><a href="missing.html">missing</a>',
        "guides/start.html": '<title>Start</title><a href="../index.html">home</a>'
                             '<a href="tools.html">tools</a>',
        "guides/tools.html": '<title>Tools</title><a href="start.html">start</a>'
                             '<a href="../index.html">home</a>',
    }
    if not quick:
        pages["guides/notes.html"] = '<title>Notes</title><a href="tools.html">tools</a>'
    for name, html in pages.items():
        (site / name).write_text(f"<!doctype html><html><body>{html}</body></html>", encoding="utf-8")
    return site, len(pages)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def crawl(root, max_depth=2, limit=20):
    seen = {}
    broken = []
    # The root is a path and the urls are strings, so the first url is built
    # from the path.
    start = str(root).rstrip("/") + "/index.html"
    queue = [(start, 0)]
    while queue and len(seen) < limit:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, OSError):
            broken.append(url)
            continue

        parser = LinkParser()
        parser.feed(body)
        seen[url] = {"title": parser.title, "links": len(parser.links)}
        if depth < max_depth:
            for link in parser.links:
                if link.startswith("http"):
                    continue
                target = urllib.parse.urljoin(url, link)
                if target.startswith(root):
                    queue.append((target, depth + 1))
    return seen, broken


def run(quick=False, base_dir="artifacts"):
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    site, page_count = make_site(base, quick=quick)

    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(site), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        seen, broken = crawl(f"http://127.0.0.1:{port}", max_depth=3 if quick else 4)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    (base / "pages.jsonl").write_text(
        "\n".join(json.dumps({"url": url, **data}) for url, data in seen.items()) + "\n", encoding="utf-8")
    (base / "broken.txt").write_text("\n".join(broken) + "\n", encoding="utf-8")
    return {
        "generated_pages": page_count,
        "crawled_pages": len(seen),
        "links_seen": int(sum(page["links"] for page in seen.values())),
        "broken_links": len(broken),
        "index": str(base / "pages.jsonl"),
    }


def demo(base_dir="artifacts"):
    summary = run(quick=True, base_dir=base_dir)
    print(f"Crawled {summary['crawled_pages']} pages, saw {summary['links_seen']} links.")
    for line in (Path(base_dir) / "pages.jsonl").read_text().strip().splitlines():
        row = json.loads(line)
        print(f"  {row['title'] or '(no title)':12s} {row['url']}")
    print(f"Broken links: {summary['broken_links']}")
