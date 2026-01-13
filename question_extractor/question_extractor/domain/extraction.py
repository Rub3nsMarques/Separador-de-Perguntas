import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from question_extractor.ooxml.reader import DocxReader, NAMESPACES
from question_extractor.ooxml.scanner import REGEX_QUESTION_START, REGEX_ALTERNATIVE_START
from question_extractor.ooxml.segmenter import DocxSegmenter
from question_extractor.infra.files import file_manager
from lxml import etree

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self, doc_path: Path):
        self.doc_path = doc_path
        self.segmenter = DocxSegmenter(doc_path)

    def extract_all(self, doc_source_id: str) -> Dict[str, Any]:
        """
        Parses the document, segments questions, and writes outputs.
        Returns a report dict.
        """
        report = {
            "doc_source_id": doc_source_id,
            "questions": [],
            "stats": {"total": 0, "extracted": 0, "error": 0}
        }
        
        try:
            with DocxReader(self.doc_path) as reader:

                # Use body blocks (paragraphs AND tables) to preserve order
                blocks = reader.get_body_blocks()
                
                # Naive grouping:
                # - Find start of Q1 (must be a paragraph with text matching regex)
                # - Find start of Q2
                # - elements between Q1 and Q2 -> Q1 Block
                
                q_indices = []
                for i, elem in enumerate(blocks):
                    # Only check text if it is a paragraph
                    if elem.tag.endswith('p'):
                         text = reader.extract_text(elem).strip()
                         if REGEX_QUESTION_START.match(text):
                             q_indices.append(i)
                
                # Add end sentinel
                q_indices.append(len(blocks))
                
                logger.info(f"Found {len(q_indices)-1} potential questions.")
                
                for k in range(len(q_indices) - 1):
                    start_idx = q_indices[k]
                    end_idx = q_indices[k+1]
                    
                    # Create a Question ID
                    # Try to extract number from text
                    start_elem = blocks[start_idx]
                    if start_elem.tag.endswith('p'):
                         text_start = reader.extract_text(start_elem).strip()
                         # e.g. "QUESTÃO 01" -> "q_01" (logic can be added here)
                    
                    # Just use index for safety if regex fails or logic is complex
                    q_id = f"q_{k+1:04d}"
                    
                    # Block elements
                    block_elements = blocks[start_idx:end_idx]
                    
                    # Process this block for alternatives
                    result = self.process_question_block(doc_source_id, q_id, block_elements)
                    report["questions"].append(result)
                    
                    if result["status"] == "extracted":
                        report["stats"]["extracted"] += 1
                    else:
                        report["stats"]["error"] += 1
                    report["stats"]["total"] += 1
                    
        except Exception as e:
            logger.error("Extraction failed at document level", error=str(e))
            raise
            
        return report

    def process_question_block(self, doc_source_id: str, q_id: str, elements: List[etree._Element]) -> Dict[str, Any]:
        """
        Splits a question block into Question vs Alternatives.
        Writes respective files.
        """
        output_dir = file_manager.get_output_dir(doc_source_id, q_id)
        
        # 1. Split into Body (Question) and Options
        # Strategy: Iterate and switch mode when first Alternative is found
        
        question_elems = []
        options = {} # "A": [elems], "B": [elems]
        current_option = None
        
        # We need a text extractor helper or just use simplistic check
        # Reuse regex
        
        for elem in elements:
            # Check if this element starts a new alternative
            # Only paragraphs can start an alternative (tables probably belong to previous content)
            
            is_paragraph = elem.tag.endswith('p')
            match = None
            
            if is_paragraph:
                text = "".join(elem.itertext()).strip()
                match = REGEX_ALTERNATIVE_START.match(text)
            
            if match:
                # Found new alternative start (e.g. "A)")
                marker = match.group(1).upper()
                current_option = marker
                options[current_option] = []
                options[current_option].append(elem)
            else:
                # Continue previous option or add to question
                if current_option:
                    options[current_option].append(elem)
                else:
                    question_elems.append(elem)
        
        # 2. Write Files
        res = {
            "question_id": q_id,
            "status": "extracted",
            "confidence": 100,
            "files": {}
        }
        
        # Write Question
        q_path = output_dir / "pergunta.docx"
        try:
            self.segmenter.create_subdocument(q_path, question_elems)
            res["files"]["question"] = str(q_path)
            
            # Write Options
            for opt_key, opt_elems in options.items():
                opt_path = output_dir / f"{opt_key}.docx"
                self.segmenter.create_subdocument(opt_path, opt_elems)
                res["files"][opt_key] = str(opt_path)
                
        except Exception as e:
            logger.error(f"Failed to write segment for {q_id}", error=str(e))
            res["status"] = "error"
            res["confidence"] = 0
            res["error"] = str(e)
            
        return res
