"""
VectorService against a fake embeddings client: no network, no API key.
Run:  python -m pytest tests  (or: python tests/test_vectors.py)
"""
import hashlib
import importlib.util
import json
import os
import stat
import tempfile
from types import SimpleNamespace

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), '..')

# Load the real module by path (test_api stubs `src.services.vector_service` in sys.modules)
spec = importlib.util.spec_from_file_location('_vector_service_under_test', os.path.join(ROOT, 'src', 'services', 'vector_service.py'))
vs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vs)


class FakeEmbeddings:
    """Bag-of-words vectors: texts sharing words point the same way."""

    def __init__(self):
        self.fail = False

    def create(self, model, input, dimensions):
        if self.fail:
            raise RuntimeError('network down')
        data = []
        for text in input:
            v = np.zeros(dimensions)
            for word in text.lower().split():
                # Stable hash: built-in hash() is randomized per process, which made rankings flaky
                v[int(hashlib.md5(word.strip('.,?').encode()).hexdigest(), 16) % dimensions] += 1
            data.append(SimpleNamespace(embedding=v.tolist()))
        return SimpleNamespace(data=data)


def make(index_path, fail=False):
    embeddings = FakeEmbeddings()
    embeddings.fail = fail
    service = vs.VectorService({'FAISS_INDEX_PATH': index_path, 'VECTOR_DIMENSION': 256}, client=SimpleNamespace(embeddings=embeddings))
    return service, embeddings


def write_docs(folder, docs):
    with open(os.path.join(folder, 'kb_docs.json'), 'w') as f:
        json.dump(docs, f)
    return os.path.join(folder, 'kb')


DOCS = [
    {'id': 'a', 'title': 'Quantum', 'url': 'u1', 'content': 'quantum computers use qubits and superposition'},
    {'id': 'b', 'title': 'Python', 'url': 'u2', 'content': 'python release notes list new language features'},
    {'id': 'c', 'title': 'Recipes', 'url': 'u3', 'content': 'bake bread with flour water and yeast'},
]


def test_repo_knowledge_base_loads():
    service, _ = make(os.path.join(ROOT, 'data', 'faiss_index'))
    assert service.get_stats()['total_documents'] == service.get_stats()['index_size'] > 0


def test_search_ranks_the_closest_document_first():
    with tempfile.TemporaryDirectory() as tmp:
        service, _ = make(write_docs(tmp, DOCS))
        results = service.search('what is new in the python release?', 2)
        assert [r.id for r in results][0] == 'b' and len(results) == 2


def test_similarities_score_texts_against_the_query():
    with tempfile.TemporaryDirectory() as tmp:
        service, embeddings = make(write_docs(tmp, DOCS))
        scores = service.similarities('python release', ['python release notes', 'bread and yeast'])
        assert scores[0] > scores[1]
        embeddings.fail = True
        assert service.similarities('python', ['a', 'b']) == [0.0, 0.0]
        assert service.similarities('python', []) == []


def test_failed_startup_embedding_heals_on_next_search():
    with tempfile.TemporaryDirectory() as tmp:
        service, embeddings = make(write_docs(tmp, DOCS), fail=True)
        stats = service.get_stats()
        assert (stats['total_documents'], stats['index_size']) == (3, 0)
        embeddings.fail = False
        assert service.search('bread yeast')[0].id == 'c'
        assert service.get_stats()['index_size'] == 3


def test_add_documents_persists_and_skips_duplicates_and_junk():
    with tempfile.TemporaryDirectory() as tmp:
        path = write_docs(tmp, DOCS)
        service, _ = make(path)
        new = {'title': 'FAISS', 'url': 'u4', 'content': 'faiss searches vectors fast'}
        assert service.add_documents([new, 'junk', {'title': 'no content'}]) == 1
        assert service.add_documents([new]) == 0
        with open(f'{path}_docs.json') as f:
            assert len(json.load(f)) == 4
        assert service.search('faiss vectors')[0].title == 'FAISS'


def test_read_only_filesystem_keeps_documents_in_memory():
    with tempfile.TemporaryDirectory() as tmp:
        locked = os.path.join(tmp, 'locked')
        os.mkdir(locked)
        os.chmod(locked, stat.S_IRUSR | stat.S_IXUSR)
        try:
            service, _ = make(os.path.join(locked, 'sub', 'kb'))
            assert service.add_documents([{'title': 't', 'url': 'u', 'content': 'kept in memory'}]) == 1
            assert service.search('kept in memory')[0].title == 't'
        finally:
            os.chmod(locked, stat.S_IRWXU)


if __name__ == '__main__':
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            fn()
            print('ok', name)
