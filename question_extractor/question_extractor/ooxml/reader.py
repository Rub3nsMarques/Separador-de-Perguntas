import zipfile
from lxml import etree
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
}

class DocxReader:
    def __init__(self, path: Path):
        self.path = path
        self.zip_file: Optional[zipfile.ZipFile] = None
        self.document_xml: Optional[etree._Element] = None
        self.body: Optional[etree._Element] = None

    def __enter__(self):
        self.zip_file = zipfile.ZipFile(self.path, 'r')
        self.read_document_xml()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.zip_file:
            self.zip_file.close()

    def read_document_xml(self):
        if not self.zip_file:
            raise ValueError("ZipFile not open")
        
        try:
            xml_content = self.zip_file.read('word/document.xml')
            self.document_xml = etree.fromstring(xml_content)
            self.body = self.document_xml.find("w:body", NAMESPACES)
            if self.body is None:
                raise ValueError("Could not find w:body in document.xml")
        except KeyError:
            raise ValueError(f"File {self.path} does not contain word/document.xml")

    def get_paragraphs(self) -> List[etree._Element]:
        if self.body is None:
            return []
        return self.body.findall(".//w:p", NAMESPACES)

    def get_tables(self) -> List[etree._Element]:
        if self.body is None:
            return []
        return self.body.findall(".//w:tbl", NAMESPACES)

    def get_body_blocks(self) -> List[etree._Element]:
        """
        Returns direct children of body that are paragraphs or tables.
        This is crucial for preserving document order.
        """
        if self.body is None:
            return []
        
        blocks = []
        for child in list(self.body):
            local = etree.QName(child).localname
            if local in ("p", "tbl"):
                blocks.append(child)
        return blocks

    def extract_text(self, element: etree._Element) -> str:
        """
        Extracts plain text from a paragraph or run, stripping XML tags.
        """
        return "".join(element.itertext())
