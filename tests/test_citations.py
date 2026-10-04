"""
The answer's [n] markers must point at the n-th source the API returns.
Loads the real content_generator with its heavy imports stubbed.
Run:  python -m pytest tests  (or: python tests/test_citations.py)
"""
import importlib.util
import os
import sys
import types

ROOT = os.path.join(os.path.dirname(__file__), '..')


def stub(name, **attrs):
    module = sys.modules.get(name) or types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module


for pkg in ('src', 'src.services'):
    if pkg not in sys.modules:  # don't clobber the real package if another test already imported it
        stub(pkg, __path__=[])
stub('src.services.openai_service', OpenAIService=object, GenerationResult=object)
stub('src.services.vector_service', VectorService=object, SearchResult=object)
stub('src.services.cache_service', CacheService=object)
stub('src.services.realtime_search', RealTimeWebSearcher=object)
stub('src.services.query_classifier', QueryClassifier=object, QueryType=object)

spec = importlib.util.spec_from_file_location(
    'src.services._content_generator_under_test', os.path.join(ROOT, 'src', 'services', 'content_generator.py'))
cg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cg)

generator = cg.ContentGenerator.__new__(cg.ContentGenerator)
generator.max_context_length = 4000


def test_sources_are_numbered_in_order_and_returned():
    sources = [
        {'title': 'A', 'content': 'alpha', 'source_type': 'web'},
        {'title': 'Empty', 'content': '', 'snippet': ''},  # skipped: nothing to cite
        {'title': 'B', 'snippet': 'beta', 'source_type': 'knowledge_base'},
    ]
    context, used = generator._prepare_combined_context(sources, 'q')
    assert context.splitlines()[0] == '[1] A (web): alpha'
    assert '[2] B (knowledge_base): beta' in context
    assert [s['title'] for s in used] == ['A', 'B']


def test_cap_and_token_budget():
    many = [{'title': str(i), 'content': 'x'} for i in range(20)]
    _, used = generator._prepare_combined_context(many, 'q')
    assert len(used) == 8

    huge = [{'title': 'big', 'content': 'word ' * 4000}, {'title': 'small', 'content': 'ok'}]
    context, used = generator._prepare_combined_context(huge, 'q')
    assert used == [] and context == ''  # over budget: nothing numbered, caller falls back


def test_select_sources_keeps_only_close_matches_best_first():
    candidates = [
        {'title': 'kb agriculture', 'score': 0.49},
        {'title': 'web hash function', 'score': 0.78},
        {'title': 'kb blockchain', 'score': 0.57},
        {'title': 'web cryptographic hash', 'score': 0.74},
    ]
    assert [s['title'] for s in cg.select_sources(candidates)] == ['web hash function', 'web cryptographic hash']
    assert len(cg.select_sources([{'score': 0.9}] * 9)) == 5


def test_select_sources_without_scores_keeps_search_order():
    unscored = [{'title': 'a', 'score': 0.0}, {'title': 'b', 'score': 0.0}]
    assert [s['title'] for s in cg.select_sources(unscored)] == ['a', 'b']
    assert cg.select_sources([]) == []


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
