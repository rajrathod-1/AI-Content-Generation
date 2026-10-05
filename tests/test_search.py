"""
Live source search: query cleaning, Wikipedia / OpenAlex / Tavily parsing, provider isolation.
Uses a fake HTTP session, so no network.
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


def test_abstract_text_rebuilds_word_order():
    assert rs.abstract_text({'hashing': [1], 'Spectral': [0], 'works': [2]}) == 'Spectral hashing works'
    assert rs.abstract_text(None) == ''


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


def wiki_page(pid, title, extract, index):
    return {'pageid': pid, 'title': title, 'extract': extract, 'index': index, 'fullurl': f'https://en.wikipedia.org/wiki/{title}'}


ABSTRACT = {word: [i] for i, word in enumerate('hash functions map data of arbitrary size to fixed size values used in tables and cryptography'.split())}
WORKS = [
    {'id': 'https://openalex.org/W1', 'doi': 'https://doi.org/10.1/x', 'title': 'Spectral Hashing', 'publication_year': 2008,
     'abstract_inverted_index': ABSTRACT, 'primary_location': {'source': {'display_name': 'NeurIPS'}},
     'authorships': [{'author': {'display_name': 'Y. Weiss'}}, {'author': {'display_name': 'A. Torralba'}}]},
    {'id': 'https://openalex.org/W2', 'doi': None, 'title': 'spectral hashing', 'publication_year': 2009,  # duplicate title
     'abstract_inverted_index': ABSTRACT, 'primary_location': {'landing_page_url': 'https://example.org/p'}, 'authorships': []},
    {'id': 'https://openalex.org/W3', 'doi': None, 'title': 'No abstract', 'abstract_inverted_index': None},
]


def make_searcher(tavily_key=None, broken=()):
    searcher = rs.RealTimeWebSearcher(tavily_api_key=tavily_key)
    calls = []

    def get(url, params, timeout):
        calls.append((url, params))
        if url in broken:
            raise rs.requests.ConnectionError('offline')
        if url == rs.WIKIPEDIA_URL:
            if ' OR ' in params['gsrsearch']:
                return FakeResponse({'query': {'pages': [wiki_page(1, 'Hash function', 'x' * 300, 2), wiki_page(3, 'Hash table', 'y' * 300, 1)]}})
            return FakeResponse({'query': {'pages': [wiki_page(1, 'Hash function', 'x' * 300, 1), wiki_page(2, 'Hash (disambiguation)', 'Hash may refer to:', 2)]}})
        if url == rs.OPENALEX_URL:
            return FakeResponse({'results': WORKS})
        raise AssertionError(url)

    def post(url, headers, json, timeout):
        calls.append((url, headers))
        return FakeResponse({'results': [{'title': 'Hashing explained', 'url': 'https://blog.dev/hashing', 'content': 'z' * 300, 'score': 0.9}]})

    searcher.session.get = get
    searcher.session.post = post
    return searcher, calls


def test_wikipedia_falls_back_to_or_and_skips_stubs():
    searcher, calls = make_searcher()
    results = searcher.search_wikipedia('how do hash tables work', 'hash tables', 3)
    assert [p['gsrsearch'] for url, p in calls] == ['hash tables', 'hash OR tables']
    assert [r['title'] for r in results] == ['Hash function', 'Hash table']
    assert results[0]['source_type'] == 'web' and results[0]['meta'] == 'Wikipedia' and results[0]['score'] == 0.0


def test_papers_rebuild_abstracts_dedupe_and_describe_authors():
    searcher, calls = make_searcher()
    papers = searcher.search_papers('how does hashing work', 'hashing', 5)
    assert [p['title'] for p in papers] == ['Spectral Hashing']
    assert papers[0]['url'] == 'https://doi.org/10.1/x'
    assert papers[0]['meta'] == 'Y. Weiss et al. · 2008 · NeurIPS'
    assert papers[0]['content'].startswith('hash functions map data')
    assert 'cited_by_count:>2' in calls[0][1]['filter']


def test_search_runs_every_provider_and_survives_failures():
    searcher, _ = make_searcher()
    assert {r['source_type'] for r in searcher.search('hash tables')} == {'web', 'paper'}  # no Tavily without a key

    searcher, calls = make_searcher(tavily_key='tvly-test')
    titles = {r['title'] for r in searcher.search('hash tables')}
    assert 'Hashing explained' in titles and 'Spectral Hashing' in titles
    assert ('https://api.tavily.com/search', {'Authorization': 'Bearer tvly-test'}) in calls

    searcher, _ = make_searcher(broken={rs.WIKIPEDIA_URL})
    assert {r['source_type'] for r in searcher.search('hash tables')} == {'paper'}


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
