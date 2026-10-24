#!/usr/bin/env python3
from __future__ import annotations
import sys, time
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from config.settings import get_settings
from src.factory import create_chatbot
from src.query_normalizer import normalize_query

TEST_QUERIES = [
    ('When was the college established?',     ['established','establishment','founded','2001','history']),
    ('What is the establishment year?',       ['established','establishment','founded','2001','history']),
    ('In which year did the college start?',  ['established','establishment','founded','2001','history']),
    ('When did the institution begin?',       ['established','establishment','founded','2001','history']),
    ('History of the college',                ['established','establishment','founded','history','example education trust']),
    ('Who founded the college?',              ['founded','established','trust','management','history']),
    ('About the college',                     ['autonomous','established','founded','engineering','example']),
]

def _chunk_hits(chunks, keywords):
    for doc in chunks:
        text = doc.page_content.lower()
        if any(kw.lower() in text for kw in keywords):
            return True
    return False

def main():
    print('=' * 70)
    print('Retrieval Evaluation -- Establishment Year Queries')
    print('=' * 70)
    settings = get_settings()
    settings_eval = settings.model_copy(update={'enable_query_rewriting': False})
    print('Loading chatbot...')
    chatbot = create_chatbot(settings_eval)
    retriever = chatbot._retriever
    passed = 0
    failed_queries = []
    results = []
    for query, keywords in TEST_QUERIES:
        norm = normalize_query(query)
        t0 = time.perf_counter()
        result = retriever.retrieve(query=query, rewritten_query=norm)
        latency_ms = (time.perf_counter() - t0) * 1000
        hit = _chunk_hits(result.documents, keywords)
        best_score = max(result.scores) if result.scores else 0.0
        status = 'PASS' if hit else 'FAIL'
        if hit:
            passed += 1
        else:
            failed_queries.append(query)
        results.append({'query': query, 'status': status, 'best_score': best_score,
                        'chunks': len(result.documents), 'latency_ms': latency_ms})
        print('-' * 70)
        print('Query   : ' + query)
        print('Status  : ' + status)
        print('Score   : %.4f  | Chunks: %d  | Latency: %.1f ms' % (best_score, len(result.documents), latency_ms))
        if result.documents:
            top = result.documents[0]
            print('Top chunk: ' + top.page_content[:150].replace(chr(10), ' '))
    total = len(TEST_QUERIES)
    accuracy = passed / total * 100
    print('=' * 70)
    print('RESULTS: %d/%d queries passed  (%.1f%% accuracy)' % (passed, total, accuracy))
    print('=' * 70)
    if failed_queries:
        print('Failed queries:')
        for q in failed_queries:
            print('  FAIL: ' + q)
    else:
        print('All queries passed!')
    print('')
    print('Detailed results:')
    print('  %-45s %-6s %7s %6s %6s' % ('Query', 'Status', 'Score', 'Chunks', 'ms'))
    print('  ' + '-' * 72)
    for r in results:
        print('  %-45s %-6s %7.4f %6d %6.0f' % (r['query'], r['status'], r['best_score'], r['chunks'], r['latency_ms']))

if __name__ == '__main__':
    main()
