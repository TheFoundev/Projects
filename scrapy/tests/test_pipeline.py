"""Tests for the crawler."""
import threading
from http.server import ThreadingHTTPServer

from src.pipeline import QuietHandler, crawl, demo, make_site, run


def _serve(directory):
    """A server for the site, and the port it listens on."""
    handler = lambda *args, **kwargs: QuietHandler(*args, directory=str(directory), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, server.server_address[1], thread


def test_pipeline_runs(tmp_path, capsys):
    summary = run(quick=True, base_dir=str(tmp_path))
    assert isinstance(summary, dict)
    assert summary
    assert any(tmp_path.iterdir())

    demo(base_dir=str(tmp_path))
    assert capsys.readouterr().out.strip()


def test_the_site_is_crawled(tmp_path):
    site, _ = make_site(tmp_path, quick=True)
    server, port, _thread = _serve(site)
    try:
        seen, _broken = crawl(f"http://127.0.0.1:{port}", max_depth=2, limit=20)
    finally:
        server.shutdown()
        server.server_close()

    assert seen
    assert all("title" in page for page in seen.values())
    assert all(url.startswith("http://") for url in seen)


def test_the_depth_is_respected(tmp_path):
    site, _ = make_site(tmp_path, quick=True)
    server, port, _thread = _serve(site)
    try:
        shallow, _ = crawl(f"http://127.0.0.1:{port}", max_depth=1, limit=50)
        deep, _ = crawl(f"http://127.0.0.1:{port}", max_depth=3, limit=50)
    finally:
        server.shutdown()
        server.server_close()

    assert len(shallow) <= len(deep)


def test_the_limit_is_respected(tmp_path):
    site, _ = make_site(tmp_path, quick=True)
    server, port, _thread = _serve(site)
    try:
        seen, _ = crawl(f"http://127.0.0.1:{port}", max_depth=3, limit=3)
    finally:
        server.shutdown()
        server.server_close()

    assert len(seen) <= 3


def test_the_missing_page_is_reported(tmp_path):
    site, _ = make_site(tmp_path, quick=True)
    server, port, _thread = _serve(site)
    try:
        _seen, broken = crawl(f"http://127.0.0.1:{port}", max_depth=2, limit=20)
    finally:
        server.shutdown()
        server.server_close()

    assert any("missing" in url for url in broken)
