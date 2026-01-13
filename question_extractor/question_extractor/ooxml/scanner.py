import re
import logging
from lxml import etree
from .reader import DocxReader, NAMESPACES
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Regex Patterns
REGEX_QUESTION_START = re.compile(r'^\s*(QUEST[ÃA]O|Q\.|[0-9]{1,3}[ \)\.-])', re.IGNORECASE)
REGEX_ALTERNATIVE_START = re.compile(r'^\s*([A-Ea-e])[\)\.\-]\s*', re.IGNORECASE)

class DocxScanner:
    def __init__(self, reader: DocxReader):
        self.reader = reader
        self.stats = {
            "questions_detected": 0,
            "alternatives_detected": 0,
            "patterns": {}
        }

    def scan(self) -> Dict[str, Any]:
        """
        Scans the document for patterns.
        """
        paragraphs = self.reader.get_paragraphs()
        
        for p in paragraphs:
            text = self.reader.extract_text(p).strip()
            if not text:
                continue
            
            # Check Question Pattern
            q_match = REGEX_QUESTION_START.match(text)
            if q_match:
                marker = q_match.group(0).strip()
                self.stats["questions_detected"] += 1
                self.record_pattern("question_marker", marker)

            # Check Alternative Pattern
            # Only if it looks like a single alternative line "A) Text"
            a_match = REGEX_ALTERNATIVE_START.match(text)
            if a_match:
                marker = a_match.group(0).strip()
                self.stats["alternatives_detected"] += 1
                self.record_pattern("alternative_marker", marker)
        
        return self.stats

    def record_pattern(self, category: str, marker: str):
        if category not in self.stats["patterns"]:
            self.stats["patterns"][category] = {}
        
        if marker not in self.stats["patterns"][category]:
            self.stats["patterns"][category][marker] = 0
        self.stats["patterns"][category][marker] += 1
