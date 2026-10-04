"""
Live web search for RAG, via Wikipedia's search API.

Free, keyless and reliable from servers. The old approach (DuckDuckGo's instant-answer
API plus scraping Bing) returned nothing for normal questions and gets bot-checked on
datacenter IPs. Results come back in Wikipedia's order; the caller ranks them against
the question with the embedding model.
"""
import logging
import re
import time
from typing import Dict, List

import requests

API_URL = 'https://en.wikipedia.org/w/api.php'

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


class RealTimeWebSearcher:
    """Finds candidate Wikipedia articles (title, URL, plain-text intro) for a question."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        # Wikimedia asks API clients to identify themselves
        self.session.headers['User-Agent'] = 'RAGGenerator/2.0 (https://github.com/rajrathod-1/AI-Content-Generation)'

    def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """Up to 2 x num_results candidates; scores are left at 0 for the caller to fill in."""
        terms = keywords(query)
        try:
            pages = self._search(terms, num_results * 2)
            # Every keyword is required by default; if that was too strict, also accept any of them
            if len(pages) < num_results and ' ' in terms:
                seen = {p['pageid'] for p in pages}
                pages += [p for p in self._search(' OR '.join(terms.split()), num_results * 2) if p['pageid'] not in seen]
        except (requests.RequestException, ValueError) as e:
            self.logger.warning(f"Wikipedia search failed: {e}")
            return []

        results = []
        for page in pages:
            extract = (page.get('extract') or '').strip()
            if len(extract) < 80:  # stubs and disambiguation pages say nothing useful
                continue
            results.append({
                'title': page['title'],
                'url': page['fullurl'],
                'snippet': extract[:200],
                'content': extract[:2000],
                'score': 0.0,
                'timestamp': time.time(),
            })
        self.logger.info(f"Wikipedia: {len(results)} candidates for '{terms}'")
        return results

    def _search(self, terms: str, limit: int) -> List[Dict]:
        """One API call: search hits with their intro text and canonical URL, in relevance order."""
        response = self.session.get(API_URL, timeout=8, params={
            'action': 'query',
            'format': 'json',
            'formatversion': 2,
            'generator': 'search',
            'gsrsearch': terms,
            'gsrlimit': limit,
            'prop': 'extracts|info',
            'exintro': 1,
            'explaintext': 1,
            'exlimit': limit,
            'inprop': 'url',
        })
        response.raise_for_status()
        pages = response.json().get('query', {}).get('pages', [])
        return sorted(pages, key=lambda p: p.get('index', 0))
