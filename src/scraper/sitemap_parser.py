"""Sitemap parser for extracting URLs from sitemaps."""

import requests
import xml.etree.ElementTree as ET
from typing import List, Set
from urllib.parse import urljoin, urlparse


class SitemapParser:
    """Parses sitemaps to extract URLs."""
    
    def __init__(self, timeout: int = 30):
        """Initialize sitemap parser.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        
    def parse_sitemap(self, sitemap_url: str) -> Set[str]:
        """Parse a sitemap and extract all URLs.
        
        Args:
            sitemap_url: URL of the sitemap
            
        Returns:
            Set of URLs found in the sitemap
        """
        urls = set()
        
        try:
            response = requests.get(sitemap_url, timeout=self.timeout)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            
            # Handle sitemap index
            if root.tag.endswith("sitemapindex"):
                sitemap_urls = []
                for sitemap in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
                    loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc is not None and loc.text:
                        sitemap_urls.append(loc.text)
                
                # Recursively parse nested sitemaps
                for nested_sitemap_url in sitemap_urls:
                    urls.update(self.parse_sitemap(nested_sitemap_url))
            
            # Handle regular sitemap
            elif root.tag.endswith("urlset"):
                for url_elem in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
                    loc = url_elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                    if loc is not None and loc.text:
                        urls.add(loc.text)
            
        except Exception as e:
            raise Exception(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return urls
    
    def filter_same_domain(self, urls: Set[str], base_url: str) -> Set[str]:
        """Filter URLs to only include same domain.
        
        Args:
            urls: Set of URLs to filter
            base_url: Base URL to compare domains against
            
        Returns:
            Filtered set of URLs
        """
        base_domain = urlparse(base_url).netloc
        filtered = set()
        
        for url in urls:
            parsed = urlparse(url)
            if parsed.netloc == base_domain:
                filtered.add(url)
        
        return filtered
