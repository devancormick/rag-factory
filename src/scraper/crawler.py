"""Web crawler with rate limiting and retry logic."""

import requests
import hashlib
import time
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse
from .robots_parser import RobotsParser
from .sitemap_parser import SitemapParser


class Crawler:
    """Web crawler with robots.txt support and rate limiting."""
    
    def __init__(
        self,
        base_url: str,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        timeout: int = 30,
        user_agent: str = "RAGFactoryBot/1.0"
    ):
        """Initialize crawler.
        
        Args:
            base_url: Base URL to crawl (for same-domain filtering)
            rate_limit_delay: Delay between requests in seconds
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
            user_agent: User agent string
        """
        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agent = user_agent
        
        self.robots_parser = RobotsParser(user_agent=user_agent, timeout=timeout)
        self.sitemap_parser = SitemapParser(timeout=timeout)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        
        self.last_request_time = 0.0
        
    def fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL with retries.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        # Check robots.txt
        if not self.robots_parser.can_fetch(url, self.base_url):
            return None
        
        # Rate limiting
        self._apply_rate_limit()
        
        # Fetch with retries
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" not in content_type:
                    return None
                
                return response.text
                
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def crawl_from_sitemap(self, sitemap_url: str) -> Set[str]:
        """Crawl URLs from a sitemap.
        
        Args:
            sitemap_url: URL of the sitemap
            
        Returns:
            Set of URLs to crawl
        """
        urls = self.sitemap_parser.parse_sitemap(sitemap_url)
        return self.sitemap_parser.filter_same_domain(urls, self.base_url)
    
    def crawl_from_urls(self, seed_urls: List[str]) -> Set[str]:
        """Filter seed URLs to same domain.
        
        Args:
            seed_urls: List of seed URLs
            
        Returns:
            Set of URLs on same domain
        """
        parsed_base = urlparse(self.base_url)
        same_domain_urls = set()
        
        for url in seed_urls:
            parsed = urlparse(url)
            if parsed.netloc == parsed_base.netloc:
                same_domain_urls.add(url)
        
        return same_domain_urls
    
    def get_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content.
        
        Args:
            content: Content to hash
            
        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        
        self.last_request_time = time.time()
