"""Structure-aware chunking for documents."""

import re
import tiktoken
from typing import List, Dict, Any


class StructureAwareChunker:
    """Chunks text while preserving document structure."""
    
    def __init__(self, target_tokens: int = 500, min_tokens: int = 300, max_tokens: int = 800):
        """Initialize chunker.
        
        Args:
            target_tokens: Target chunk size in tokens
            min_tokens: Minimum chunk size
            max_tokens: Maximum chunk size
        """
        self.target_tokens = target_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.encoding = tiktoken.get_encoding("cl100k_base")  # For GPT models
        
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk text preserving structure.
        
        Args:
            text: Text to chunk
            metadata: Metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        # Split by major structural elements
        sections = self._split_by_structure(text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for section in sections:
            section_tokens = len(self.encoding.encode(section))
            
            # If section is too large, split it further
            if section_tokens > self.max_tokens:
                # Try to split large sections by paragraphs
                paragraphs = self._split_paragraphs(section)
                for para in paragraphs:
                    para_tokens = len(self.encoding.encode(para))
                    
                    if current_tokens + para_tokens > self.max_tokens and current_chunk:
                        # Finalize current chunk
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append(self._create_chunk(chunk_text, metadata))
                        current_chunk = [para]
                        current_tokens = para_tokens
                    else:
                        current_chunk.append(para)
                        current_tokens += para_tokens
            else:
                # Check if adding this section would exceed max
                if current_tokens + section_tokens > self.max_tokens and current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(self._create_chunk(chunk_text, metadata))
                    current_chunk = [section]
                    current_tokens = section_tokens
                else:
                    current_chunk.append(section)
                    current_tokens += section_tokens
                    
                    # If we've reached target size, finalize chunk
                    if current_tokens >= self.target_tokens:
                        chunk_text = "\n\n".join(current_chunk)
                        chunks.append(self._create_chunk(chunk_text, metadata))
                        current_chunk = []
                        current_tokens = 0
        
        # Add remaining content as final chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(self._create_chunk(chunk_text, metadata))
        
        return chunks
    
    def _split_by_structure(self, text: str) -> List[str]:
        """Split text by structural elements (headings, lists, tables).
        
        Args:
            text: Text to split
            
        Returns:
            List of text sections
        """
        sections = []
        lines = text.split("\n")
        
        current_section = []
        in_list = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect headings (markdown or HTML style)
            is_heading = (
                line_stripped.startswith("#") or
                re.match(r"^={3,}$", lines[i+1] if i+1 < len(lines) else "") or
                re.match(r"^-{3,}$", lines[i+1] if i+1 < len(lines) else "")
            )
            
            # Detect lists
            is_list_item = re.match(r"^[\*\-\+]|\d+\.", line_stripped) or re.match(r"^[a-z]\)", line_stripped)
            
            # Detect tables (markdown table syntax)
            is_table_row = "|" in line_stripped
            
            # If we hit a heading and have content, start new section
            if is_heading and current_section:
                sections.append("\n".join(current_section))
                current_section = [line]
            elif is_list_item:
                if not in_list and current_section:
                    # End previous section if not in list
                    sections.append("\n".join(current_section))
                    current_section = []
                in_list = True
                current_section.append(line)
            elif is_table_row:
                if current_section and not any("|" in l for l in current_section):
                    # Start new section for table
                    if current_section:
                        sections.append("\n".join(current_section))
                        current_section = []
                current_section.append(line)
            else:
                # End list context
                if in_list and not is_list_item:
                    in_list = False
                    if current_section:
                        sections.append("\n".join(current_section))
                        current_section = []
                
                current_section.append(line)
        
        # Add final section
        if current_section:
            sections.append("\n".join(current_section))
        
        return [s for s in sections if s.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _create_chunk(self, text: str, base_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chunk dictionary.
        
        Args:
            text: Chunk text
            base_metadata: Base metadata to include
            
        Returns:
            Chunk dictionary
        """
        chunk = {
            "text": text,
            **base_metadata
        }
        return chunk
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text.
        
        Args:
            text: Text to count
            
        Returns:
            Number of tokens
        """
        return len(self.encoding.encode(text))
