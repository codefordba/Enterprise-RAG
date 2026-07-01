# src/processing/layout_parser.py
import logging
import pdfplumber
from typing import List, Dict, Any

logger = logging.getLogger("LayoutParser")

class LayoutAwareParser:
    @staticmethod
    def extract_elements(file_path: str) -> List[Dict[str, Any]]:
        """Deconstructs high-density PDFs into isolated text paragraphs and stringified tables."""
        extracted_elements = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_idx, page in enumerate(pdf.pages, start=1):
                    # 1. Isolate and parse embedded table matrices
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            clean_table = [[str(cell or "").strip() for cell in row] for row in table]
                            table_markdown = "\n".join([" | ".join(row) for row in clean_table])
                            extracted_elements.append({
                                "content": f"[Table Layout Structure]:\n{table_markdown}",
                                "type": "table",
                                "page": page_idx
                            })
                    
                    # 2. Extract standard running text
                    prose_text = page.extract_text()
                    if prose_text:
                        extracted_elements.append({
                            "content": prose_text,
                            "type": "prose",
                            "page": page_idx
                        })
            return extracted_elements
        except Exception as e:
            logger.error(f"Error parsing layout elements at file path '{file_path}': {str(e)}")
            raise e