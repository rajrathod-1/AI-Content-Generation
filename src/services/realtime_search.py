"""
Live source search for RAG: Wikipedia, research papers, and (optionally) the open web.

- Wikipedia's search API: established knowledge. Free, keyless, reliable from servers.
- OpenAlex: ~250M research papers with abstracts. Free, keyless (OPENALEX_API_KEY raises the budget).
- Tavily: general web search, used only when TAVILY_API_KEY is set (free tier: 1,000 searches/month).

All three run in parallel. Results come back unscored; the caller ranks them against the
question with the embedding model, which is what keeps off-topic papers out.
"""
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

import requests

WIKIPEDIA_URL = 'https://en.wikipedia.org/w/api.php'
OPENALEX_URL = 'https://api.openalex.org/works'
TAVILY_URL = 'https://api.tavily.com/search'
USER_AGENT = 'RAGGenerator/2.0 (https://github.com/rajrathod-1/AI-Content-Generation)'

# Question and filler words that make full-text search miss: "Explain how does hashing work?" -> "hashing"
STOPWORDS = frozenset("""
a an the and or but of to in on at for from by with about into over under is are was were be been being
do does did done doing how what which who whom whose why when where explain describe tell me please can could
would should will shall i you we they it this that these those my your our their its use using used instead vs
versus give show list summarize summarise latest recent current new month week year today works work working
way ways happen happens there here some any all more most best biggest top
""".split())


def keywords(query: str) -> str:
    """The query minus question words, or the query itself if nothing would be left."""
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9+#.\-]*", query)
    kept = [w.rstrip('.') for w in words if w.lower().rstrip('.') not in STOPWORDS]
    return ' '.join(kept) or query


def abstract_text(inverted: Optional[Dict[str, List[int]]]) -> str:
    """OpenAlex stores abstracts as {word: [positions]}; put the words back in order."""
    if not inverted:
        return ''
    return ' '.join(word for _, word in sorted((pos, word) for word, positions in inverted.items() for pos in positions))


def _source(title: str, url: str, text: str, source_type: str, meta: str) -> Dict:
    return {
        'title': title,
        'url': url,
        'snippet': text[:200],
        'content': text[:2000],
        'score': 0.0,
        'source_type': source_type,
        'meta': meta,
        'timestamp': time.time(),
    }


class RealTimeWebSearcher:
    """Finds candidate sources for a question across Wikipedia, research papers and the web."""

    def __init__(self, tavily_api_key: Optional[str] = None, openalex_api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.tavily_api_key = tavily_api_key
        self.openalex_api_key = openalex_api_key
        self.session = requests.Session()
        # Wikimedia and OpenAlex ask API clients to identify themselves
        self.session.headers['User-Agent'] = USER_AGENT

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Candidates from every configured provider, fetched in parallel. A failing provider is skipped."""
        terms = keywords(query)
        jobs: List[Callable[[str, str, int], List[Dict]]] = [self.search_wikipedia, self.search_papers]
        if self.tavily_api_key:
            jobs.append(self.search_tavily)
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            batches = list(pool.map(lambda job: self._safely(job, query, terms, num_results), jobs))
        return [result for batch in batches for result in batch]

    def _safely(self, job, query: str, terms: str, num_results: int) -> List[Dict]:
        try:
            results = job(query, terms, num_results)
            self.logger.info(f"{job.__name__}: {len(results)} candidates for '{terms}'")
            return results
        except (requests.RequestException, ValueError, KeyError) as e:
            self.logger.warning(f"{job.__name__} failed: {e}")
            return []

    def search_wikipedia(self, query: str, terms: str, num_results: int) -> List[Dict]:
        pages = self._wikipedia(terms, num_results * 2)
        # Every keyword is required by default; if that was too strict, also accept any of them
        if len(pages) < num_results and ' ' in terms:
            seen = {p['pageid'] for p in pages}
            pages += [p for p in self._wikipedia(' OR '.join(terms.split()), num_results * 2) if p['pageid'] not in seen]
        return [
            _source(p['title'], p['fullurl'], p['extract'].strip(), 'web', 'Wikipedia')
            for p in pages
            if len((p.get('extract') or '').strip()) >= 80  # stubs and disambiguation pages say nothing useful
        ]

    def _wikipedia(self, terms: str, limit: int) -> List[Dict]:
        """One call: search hits with their plain-text intro and canonical URL, in relevance order."""
        response = self.session.get(WIKIPEDIA_URL, timeout=8, params={
            'action': 'query', 'format': 'json', 'formatversion': 2,
            'generator': 'search', 'gsrsearch': terms, 'gsrlimit': limit,
            'prop': 'extracts|info', 'exintro': 1, 'explaintext': 1, 'exlimit': limit, 'inprop': 'url',
        })
        response.raise_for_status()
        return sorted(response.json().get('query', {}).get('pages', []), key=lambda p: p.get('index', 0))

    def search_papers(self, query: str, terms: str, num_results: int) -> List[Dict]:
        params = {
            'search': terms,
            'per_page': num_results * 2,
            # ponytail: a citation floor filters junk uploads but also brand-new papers; swap for a venue filter if that bites
            'filter': 'has_abstract:true,cited_by_count:>2',
            'select': 'id,doi,title,publication_year,abstract_inverted_index,primary_location,authorships',
        }
        if self.openalex_api_key:
            params['api_key'] = self.openalex_api_key
        response = self.session.get(OPENALEX_URL, params=params, timeout=8)
        response.raise_for_status()

        results, seen = [], set()
        for work in response.json().get('results', []):
            title = (work.get('title') or '').strip()
            abstract = abstract_text(work.get('abstract_inverted_index'))
            if not title or len(abstract) < 80 or title.lower() in seen:
                continue
            seen.add(title.lower())
            location = work.get('primary_location') or {}
            authors = [a['author']['display_name'] for a in work.get('authorships') or [] if a.get('author')]
            meta = ' · '.join(filter(None, [
                f"{authors[0]}{' et al.' if len(authors) > 1 else ''}" if authors else None,
                str(work.get('publication_year') or ''),
                (location.get('source') or {}).get('display_name'),
            ]))
            url = work.get('doi') or location.get('landing_page_url') or work['id']
            results.append(_source(title, url, abstract, 'paper', meta))
        return results

    def search_tavily(self, query: str, terms: str, num_results: int) -> List[Dict]:
        response = self.session.post(
            TAVILY_URL, timeout=10,
            headers={'Authorization': f'Bearer {self.tavily_api_key}'},
            json={'query': query, 'max_results': num_results},
        )
        response.raise_for_status()
        return [
            _source(r['title'], r['url'], r.get('content') or '', 'web', '')
            for r in response.json().get('results', [])
            if len(r.get('content') or '') >= 80
        ]
