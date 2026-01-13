"""Fact extraction for TV-ready output."""

import re
from typing import List, Dict, Any


class FactExtractor:
    """Extracts facts from text for TV-ready output."""
    
    def extract_facts(self, text: str, max_facts: int = 10) -> List[Dict[str, Any]]:
        """Extract facts from text.
        
        This is a simple extraction - extracts sentences that look like facts.
        In production, this could use more sophisticated NLP.
        
        Args:
            text: Text to extract facts from
            max_facts: Maximum number of facts to extract
            
        Returns:
            List of fact dictionaries
        """
        facts = []
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 20:
                continue
            
            # Simple heuristic: facts are often declarative sentences
            # Skip questions, commands, etc.
            if sentence.lower().startswith(('what', 'how', 'why', 'when', 'where', 'who')):
                continue
            if sentence.endswith('?'):
                continue
            
            # Extract as fact
            fact = {
                "text": sentence,
                "type": "statement"  # Could be more sophisticated
            }
            facts.append(fact)
            
            if len(facts) >= max_facts:
                break
        
        return facts
    
    def create_fact_cards(self, facts: List[Dict[str, Any]], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create structured fact cards.
        
        Args:
            facts: List of extracted facts
            metadata: Metadata to attach (URL, title, etc.)
            
        Returns:
            List of fact card dictionaries
        """
        cards = []
        for fact in facts:
            card = {
                "fact": fact["text"],
                "source": metadata.get("url", ""),
                "title": metadata.get("title", ""),
                "type": fact.get("type", "statement")
            }
            cards.append(card)
        
        return cards
