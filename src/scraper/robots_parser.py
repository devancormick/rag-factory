"""Robots.txt parser for respecting crawl rules."""

import requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional


class RobotsParser:
    """Parses and respects robots.txt rules."""
    
    def __init__(self, user_agent: str = "RAGFactoryBot/1.0", timeout: int = 10):
        """Initialize robots parser.
        
        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
        """
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache = {}
        
    def can_fetch(self, url: str, base_url: Optional[str] = None) -> bool:
        """Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            base_url: Base URL for robots.txt location (defaults to url's domain)
            
        Returns:
            True if URL can be fetched
        """
        if base_url is None:
            base_url = url
        
        parsed_base = urlparse(base_url)
        robots_url = f"{parsed_base.scheme}://{parsed_base.netloc}/robots.txt"
        
        # Get or create parser for this domain
        if robots_url not in self._cache:
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            try:
                parser.read()
            except Exception:
                # If robots.txt can't be read, allow crawling (permissive)
                pass
            
            self._cache[robots_url] = parser
        
        parser = self._cache[robots_url]
        return parser.can_fetch(self.user_agent, url)
