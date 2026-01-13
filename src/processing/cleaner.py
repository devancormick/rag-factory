"""Text cleaning and extraction from HTML."""

import html2text
from bs4 import BeautifulSoup
from typing import Optional


class TextCleaner:
    """Cleans and extracts text from HTML content."""
    
    def __init__(self):
        """Initialize text cleaner."""
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0  # Don't wrap lines
        
    def clean_html(self, html_content: str) -> str:
        """Clean HTML and extract text.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        # Parse HTML to preserve structure
        soup = BeautifulSoup(html_content, "lxml")
        
        # Remove script and style elements
        for element in soup(["script", "style", "meta", "link"]):
            element.decompose()
        
        # Convert to text preserving structure
        text = self.html_converter.handle(str(soup))
        
        # Clean up whitespace
        lines = []
        for line in text.split("\n"):
            cleaned_line = line.strip()
            if cleaned_line:
                lines.append(cleaned_line)
        
        return "\n".join(lines)
    
    def extract_metadata(self, html_content: str, url: str) -> dict:
        """Extract metadata from HTML.
        
        Args:
            html_content: Raw HTML content
            url: Source URL
            
        Returns:
            Dictionary of metadata
        """
        soup = BeautifulSoup(html_content, "lxml")
        metadata = {
            "url": url,
            "title": "",
            "description": ""
        }
        
        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Extract meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            metadata["description"] = meta_desc.get("content", "").strip()
        
        return metadata
