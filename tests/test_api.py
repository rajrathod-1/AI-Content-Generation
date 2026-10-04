"""
API contract tests. The heavy services (OpenAI, FAISS, Redis) are stubbed so this
runs with only Flask installed:  pip install flask flask-cors python-dotenv psutil colorlog
Run:  python -m pytest tests  (or: python tests/test_api.py)
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ['OPENAI_API_KEY'] = 'test'
os.environ['INGEST_API_KEY'] = 'secret'

calls = {}


class FakeGenerator:
    def __init__(self, *args):
        pass

    def generate_with_rag(self, query, max_length, temperature):
        calls.update(query=query, max_length=max_length, temperature=temperature)
        return {
            'content': 'answer',
            'sources': [{'title': 't', 'url': 'https://x.dev', 'snippet': 's', 'score': 0.9,
                         'source_type': 'web', 'content': 'full scraped page ' * 1000}],
            'cached': False, 'used_rag': True, 'model_used': 'gpt-4.1-mini', 'tokens_used': 42,
        }


class FakeVector:
    def __init__(self, *args):
        pass

    def get_stats(self):
        return {'total_documents': 3}

    def add_documents(self, docs):
        return len(docs)

    def search(self, query, limit):
        return []


class FakeCache:
    def __init__(self, *args):
        pass

    def ping(self):
        return False


def stub(name, **attrs):
    module = types.ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module


stub('src.services.openai_service', OpenAIService=lambda config: object())
stub('src.services.vector_service', VectorService=FakeVector)
stub('src.services.cache_service', CacheService=FakeCache)
stub('src.services.content_generator', ContentGenerator=FakeGenerator)

from app import app  # noqa: E402

client = app.test_client()


def test_generate_validates_and_clamps():
    assert client.post('/api/generate', json={}).status_code == 400
    assert client.post('/api/generate', json=['not', 'a', 'dict']).status_code == 400
    assert client.post('/api/generate', json={'query': '   '}).status_code == 400
    assert client.post('/api/generate', json={'query': 'x' * 2001}).status_code == 400

    res = client.post('/api/generate', json={'query': ' hi ', 'max_length': 10**6, 'temperature': 'hot'})
    assert res.status_code == 200
    assert calls == {'query': 'hi', 'max_length': 1500, 'temperature': app.config['OPENAI_TEMPERATURE']}

    body = res.get_json()
    assert body['sources'] == [{'title': 't', 'url': 'https://x.dev', 'snippet': 's', 'score': 0.9, 'source_type': 'web'}]
    assert body['model'] == 'gpt-4.1-mini' and body['used_rag'] is True and body['cached'] is False


def test_ingest_requires_key():
    docs = {'documents': [{'title': 'a', 'content': 'b'}]}
    assert client.post('/api/ingest', json=docs).status_code == 401
    assert client.post('/api/ingest', json=docs, headers={'X-API-Key': 'wrong'}).status_code == 401
    assert client.post('/api/ingest', json=docs, headers={'X-API-Key': 'secret'}).get_json()['processed_count'] == 1


def test_health_and_metrics_shape():
    health = client.get('/api/health').get_json()
    assert health['status'] == 'healthy' and health['documents'] == 3 and health['cache'] is False

    client.post('/api/generate', json={'query': 'hi'})
    metrics = client.get('/api/metrics').get_json()
    assert 'generate' in metrics['service_breakdown'], metrics['service_breakdown']
    assert metrics['total_tokens_used'] >= 42
    for key in ('success_rate', 'average_response_time_ms', 'cache_hit_rate', 'response_time_distribution', 'system_metrics'):
        assert key in metrics


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
