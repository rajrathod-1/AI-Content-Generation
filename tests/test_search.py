"""
Web search: query cleaning and Wikipedia response handling, with a fake HTTP session (no network).
Run:  python -m pytest tests  (or: python tests/test_search.py)
"""
import importlib.util
import os

ROOT = os.path.join(os.path.dirname(__file__), '..')
spec = importlib.util.spec_from_file_location('_realtime_search_under_test', os.path.join(ROOT, 'src', 'services', 'realtime_search.py'))
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def test_keywords_strip_question_words():
    assert rs.keywords('Explain how does hashing works?') == 'hashing'
    assert rs.keywords('When should I use RAG instead of fine-tuning?') == 'RAG fine-tuning'
    assert rs.keywords('Summarize the latest Python release notes.') == 'Python release notes'
    assert rs.keywords('How does it work?') == 'How does it work?'  # nothing left: search the original


class FakeResponse:
    def __init__(self, pages):
        self.pages = pages

    def raise_for_status(self):
        pass

    def json(self):
        return {'query': {'pages': self.pages}}


def page(pid, title, extract, index):
    return {'pageid': pid, 'title': title, 'extract': extract, 'index': index, 'fullurl': f'https://en.wikipedia.org/wiki/{title}'}


def test_search_web_parses_falls_back_to_or_and_skips_stubs():
    searcher = rs.RealTimeWebSearcher()
    queries = []

    def fake_get(url, timeout, params):
        queries.append(params['gsrsearch'])
        if ' OR ' in params['gsrsearch']:
            return FakeResponse([page(1, 'Hash function', 'x' * 300, 2), page(3, 'Hash table', 'y' * 300, 1)])
        return FakeResponse([page(1, 'Hash function', 'x' * 300, 1), page(2, 'Hash (disambiguation)', 'Hash may refer to:', 2)])

    searcher.session.get = fake_get
    results = searcher.search_web('how do hash tables work', num_results=3)
    assert queries == ['hash tables', 'hash OR tables']
    assert [r['title'] for r in results] == ['Hash function', 'Hash table']  # stub dropped, no duplicates
    assert results[0]['url'] == 'https://en.wikipedia.org/wiki/Hash function' and results[0]['score'] == 0.0


def test_search_failure_returns_nothing():
    searcher = rs.RealTimeWebSearcher()

    def broken(*args, **kwargs):
        raise rs.requests.ConnectionError('offline')

    searcher.session.get = broken
    assert searcher.search_web('hashing') == []


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
