# /data_processing/document_parser.py (Updated)

import pdfplumber
from typing import Optional
import logging
from pathlib import Path
from config.logging_config import setup_logging

logger = setup_logging()

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF with error handling for corrupted files."""
    logger.info(f"Extracting text from PDF: {pdf_path}")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                try:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"Failed to extract text from page: {str(e)}")
                    continue
            
            if not text.strip():
                logger.warning("No text extracted from PDF, might be scanned or corrupted")
                return ""
            
            logger.info(f"Successfully extracted {len(text)} characters")
            return text
    except Exception as e:
        logger.error(f"Failed to process PDF {pdf_path}: {str(e)}", exc_info=True)
        return ""