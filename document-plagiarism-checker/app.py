from flask import Flask, render_template, request, redirect, url_for, flash
import PyPDF2
import inspect
import os
import re
import threading
import time
from urllib.parse import unquote
from werkzeug.utils import secure_filename

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

try:
    from googlesearch import search
except ImportError:
    search = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
WORD_FILE = os.path.join(BASE_DIR, 'word.txt')
ALLOWED_EXTENSIONS = {'pdf'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.config['SECRET_KEY'] = 'super secret key'

LINK_BLOCKED = ["id.linkedin.com", "linkedin.com", "youtube.com", "instagram.com", "facebook.com", "tokopedia.com",
                "twitter.com", "reddit.com", "bukalapak.com", "shopee.com", "blibli.com"]

REGION = "id-id"
RESULTS_PER_QUERY = 10
SEARCH_TIMEOUT = 20
SEARCH_DELAY = 0.8
PHRASE_WORDS = 10
SEARCH_BACKENDS = ["auto", "bing"]
SEARCH_LOCK = threading.Lock()
_CLIENT = None


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _client():
    global _CLIENT
    if _CLIENT is None and DDGS is not None:
        _CLIENT = DDGS(timeout=SEARCH_TIMEOUT)
    return _CLIENT


def _google_results(query):
    if search is None:
        return []
    try:
        params = inspect.signature(search).parameters
    except (TypeError, ValueError):
        params = {}
    kwargs = {}
    if 'advanced' in params:
        kwargs['advanced'] = True
    if 'tld' in params:
        kwargs['tld'] = 'co.id'
    if 'region' in params:
        kwargs['region'] = 'id-ID'
    if 'num_results' in params:
        kwargs['num_results'] = RESULTS_PER_QUERY
    elif 'num' in params:
        kwargs['num'] = RESULTS_PER_QUERY
    if 'sleep_interval' in params:
        kwargs['sleep_interval'] = 1
    elif 'pause' in params:
        kwargs['pause'] = 1
    try:
        rows = list(search(query, **kwargs))
    except Exception as exc:
        app.logger.warning("google search failed for %r: %s", query, exc)
        return None
    results = []
    for row in rows:
        if isinstance(row, str):
            results.append({'url': row, 'title': '', 'body': ''})
        else:
            results.append({
                'url': getattr(row, 'link', None) or getattr(row, 'url', '') or '',
                'title': getattr(row, 'title', '') or '',
                'body': getattr(row, 'description', '') or getattr(row, 'body', '') or '',
            })
    return [r for r in results if r['url']]


def _ddgs_results(query):
    """Search through the ddgs backends, rotating them when one is throttled."""
    client = _client()
    if client is None:
        return None
    hard_failure = False
    for index, backend in enumerate(SEARCH_BACKENDS):
        try:
            with SEARCH_LOCK:
                rows = client.text(query, max_results=RESULTS_PER_QUERY, region=REGION, backend=backend)
            results = []
            for row in rows or []:
                url = row.get('href') or row.get('url') or ''
                if not url:
                    continue
                results.append({
                    'url': url,
                    'title': row.get('title') or '',
                    'body': row.get('body') or '',
                })
            if results:
                return results
        except Exception as exc:
            message = str(exc).lower()
            if 'no results' not in message:
                hard_failure = True
                app.logger.warning("search (%s) failed for %r: %s", backend, query, exc)
            if index < len(SEARCH_BACKENDS) - 1:
                time.sleep(0.5)
    return None if hard_failure else []


def search_results(query):
    """Return a list of {'url', 'title', 'body'} dicts, or None when the engine is unusable."""
    results = _ddgs_results(query)
    if results is not None:
        return results
    return _google_results(query)


def normalize(text):
    text = unquote(text or '').lower()
    text = re.sub(r'[^a-z0-9\s]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def is_blocked(link):
    return any(blocked in link for blocked in LINK_BLOCKED)


def phrase_of(sentence):
    """A short, distinctive part of the sentence used as the exact-phrase query."""
    words = normalize(sentence).split()
    return ' '.join(words[:PHRASE_WORDS])


def sentence_matches(sentence, result):
    """True when the sentence (or its distinctive phrase) is found in the result."""
    needle = normalize(sentence)
    if not needle:
        return False
    haystack = normalize(' '.join([result.get('title', ''), result.get('body', ''), result.get('url', '')]))
    if not haystack:
        return False
    if needle in haystack:
        return True
    phrase = phrase_of(sentence)
    if phrase and len(phrase.split()) >= 4 and phrase in haystack:
        return True
    tokens = [token for token in needle.split() if len(token) > 3]
    return len(tokens) >= 6 and all(token in haystack for token in tokens)


def extract_pdf_text(filepath):
    """Extract the text of a PDF, supporting both the legacy and current PyPDF2 API."""
    with open(filepath, 'rb') as fh:
        reader_cls = getattr(PyPDF2, 'PdfReader', None)
        if reader_cls is not None:
            reader = reader_cls(fh)
            return ''.join((page.extract_text() or '') for page in reader.pages)
        reader = PyPDF2.PdfFileReader(fh)
        return ''.join((reader.getPage(i).extractText() or '') for i in range(reader.numPages))


def split_sentences(text):
    """Split on sentence-ending punctuation, so PDF paragraphs become real sentences."""
    flat = re.sub(r'\s+', ' ', text or '').strip()
    if not flat:
        return []
    parts = re.split(r'(?<=[.!?])\s+', flat)
    return [part.strip() for part in parts if part.strip()]


def scan_text(text):
    """Look up every sentence and collect the ones found online."""
    sentences = split_sentences(text)
    matched_sentences = []
    matched_links = []
    engine_down = bool(sentences)
    for sentence in sentences:
        phrase = phrase_of(sentence)
        query = '"' + (phrase or sentence.strip().replace('"', "'")) + '"'
        results = search_results(query)
        if results is None:
            time.sleep(SEARCH_DELAY)
            continue
        engine_down = False
        for result in results:
            if is_blocked(result['url']):
                continue
            if sentence_matches(sentence, result):
                matched_sentences.append(sentence)
                matched_links.append(result['url'])
                break
        time.sleep(SEARCH_DELAY)
    count = len(sentences)
    percent = (len(matched_links) / count * 100) if count else 0.0
    return sentences, matched_sentences, matched_links, percent, engine_down


def save_upload(file):
    filename = secure_filename(file.filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return filename


def read_word_file():
    if not os.path.exists(WORD_FILE):
        return ""
    with open(WORD_FILE, "r", encoding='utf-8') as f:
        return f.read()


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('text', '')
        upload = request.files.get('file')
        filename = upload.filename if upload else ''
        if text != '' and filename == '':
            with open(WORD_FILE, 'w', encoding='utf-8') as f:
                f.write(text)
            return redirect(url_for('plagiarism', name="word") + "#hasil")
        elif filename != '' and text == '':
            if not upload or filename == '':
                flash('No selected file')
                return redirect(request.url)
            if allowed_file(filename):
                saved = save_upload(upload)
                return redirect(url_for('plagiarism', name=saved) + "#hasil")
            flash('Only PDF files are allowed')
            return redirect(request.url)
        else:
            flash('Please fill the form')
            return redirect(request.url)
    return render_template("index.html")


@app.route('/plagiarism/<name>', methods=['GET', 'POST'])
def plagiarism(name):
    text = ""
    try:
        if request.method == 'POST':
            posted_text = request.form.get('text', '')
            upload = request.files.get('file')
            filename = upload.filename if upload else ''
            if posted_text != '' and filename == '':
                with open(WORD_FILE, 'w', encoding='utf-8') as f:
                    f.write(posted_text)
                text = posted_text
            elif filename != '' and posted_text == '':
                if not allowed_file(filename):
                    flash('Only PDF files are allowed')
                    return redirect(url_for('index'))
                saved = save_upload(upload)
                text = extract_pdf_text(os.path.join(app.config['UPLOAD_FOLDER'], saved))
            else:
                flash('Please fill the form')
                return redirect(request.url)
        elif name == "word":
            text = read_word_file()
        else:
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(name))
            if not os.path.exists(upload_path):
                flash('Uploaded document not found')
                return redirect(url_for('index'))
            text = extract_pdf_text(upload_path)

        sentences, matched_sentences, matched_links, percent, engine_down = scan_text(text)
    except Exception as exc:
        app.logger.exception("scan failed")
        flash('The scan could not be completed: %s' % exc)
        return redirect(url_for('index'))

    if engine_down:
        flash('The search engine is unreachable from this server, so no result could be verified. '
              'Check the network access and try again.')
        return redirect(url_for('index'))

    return render_template("index.html", hasil_persen=percent, data=sentences,
                           hasil_plagiarism=matched_sentences,
                           link_output=matched_links, hasil_link=matched_links)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)
