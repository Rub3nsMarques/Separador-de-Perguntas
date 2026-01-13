import shutil
import zipfile
import logging
from pathlib import Path
from lxml import etree
from io import BytesIO
from typing import List, Optional
from .reader import NAMESPACES
import copy

logger = logging.getLogger(__name__)

class DocxSegmenter:
    def __init__(self, original_path: Path):
        self.original_path = original_path

    def create_subdocument(self, output_path: Path, elements: List[etree._Element]) -> None:
        """
        Creates a new DOCX at output_path containing only the specified elements in the body.
        Preserves all other parts of the original DOCX.
        """
        # Create a buffer for the new zip
        buffer = BytesIO()
        
        with zipfile.ZipFile(self.original_path, 'r') as source_zip:
            with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as target_zip:
                # Copy all files except word/document.xml
                for item in source_zip.infolist():
                    if item.filename != 'word/document.xml':
                        target_zip.writestr(item, source_zip.read(item.filename))
                
                # Construct new document.xml
                # Read original to keep root structure
                orig_xml_content = source_zip.read('word/document.xml')
                root = etree.fromstring(orig_xml_content)
                body = root.find("w:body", NAMESPACES)
                
                if body is None:
                    raise ValueError("Target DOCX has no body")
                
                # Clear existing body children
                # We want to preserve sectPr if it exists at the end?
                # Usually sectPr is the last child of body.
                # Requirement: "garantir w:sectPr final para integridade"
                
                sect_pr = body.find("w:sectPr", NAMESPACES)
                
                # Clear body
                for child in list(body):
                    body.remove(child)
                
                # Append selected elements
                for elem in elements:
                    # We might need to handle deepcopy if we are modifying attributes?
                    # For now, just append check if it works (lxml moves it, so we should copy)
                    body.append(copy.deepcopy(elem))
                
                # Restore sectPr
                if sect_pr is not None:
                    body.append(copy.deepcopy(sect_pr))
                    
                # serialized
                new_xml = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
                target_zip.writestr('word/document.xml', new_xml)
        
        # Write buffer to disk
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())
        
        logger.info(f"Created subdocument: {output_path}")
