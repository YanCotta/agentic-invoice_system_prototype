import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Dict, Any
import asyncio
import re
import json
from openai import OpenAI
from dotenv import load_dotenv
from config.logging_config import logger
from agents.base_agent import BaseAgent
from data_processing.document_parser import extract_text_from_pdf
from data_processing.ocr_helper import ocr_process_image
from data_processing.confidence_scoring import compute_confidence_score
from data_processing.rag_helper import InvoiceRAGIndex
from models.invoice import InvoiceData
from decimal import Decimal
from datetime import datetime

# Add requirements for OpenAI and python-dotenv
try:
    import openai
    import python_dotenv
except ImportError:
    logger.error("Required packages not found. Please run: pip install openai python-dotenv")
    raise

load_dotenv()  # Load environment variables from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class InvoiceExtractionTool:
    """A simple tool to extract structured invoice data as a fallback."""
    name = "invoice_extraction_tool"
    description = "Extracts structured invoice data from text with confidence scores."

    def _run(self, invoice_text: str) -> Dict:
        logger.debug(f"Starting invoice text extraction with tool for text length: {len(invoice_text)}")
        try:
            extracted_data = self._extract_fields(invoice_text)
            confidence = compute_confidence_score(extracted_data)
            logger.info(f"Extraction completed with confidence: {confidence}")
            logger.debug(f"Extracted fields: {extracted_data}")
            return {"data": extracted_data, "confidence": confidence}
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {"error": str(e), "confidence": 0.0}

    def _extract_fields(self, text: str) -> Dict:
        logger.debug("Using placeholder extraction logic as fallback")
        return {
            "vendor_name": {"value": "ABC Corp Ltd.", "confidence": 0.95},
            "invoice_number": {"value": "INV-2024-001", "confidence": 0.98},
            "invoice_date": {"value": "2024-02-18", "confidence": 0.90},
            "total_amount": {"value": "7595.00", "confidence": 0.99},
            "currency": {"value": "GBP", "confidence": 1.0}
        }

class InvoiceExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [InvoiceExtractionTool()]
        self.rag_index = InvoiceRAGIndex()

    async def run(self, document_path: str) -> InvoiceData:
        logger.info(f"Processing document: {document_path}")
        try:
            # Extract text from document
            if document_path.lower().endswith(".pdf"):
                invoice_text = extract_text_from_pdf(document_path)
            else:
                invoice_text = ocr_process_image(document_path)

            # Handle empty or unreadable files
            if not invoice_text.strip():
                logger.warning(f"No text could be extracted from {document_path}")
                return InvoiceData(
                    vendor_name="Unknown",
                    invoice_number="UNREADABLE",
                    invoice_date=datetime.now().date(),
                    total_amount=Decimal("0.00"),
                    confidence=0.0,
                    review_status="needs_review",
                    error_message="Document is empty or unreadable"
                )

            # Initial check for invoice-like content
            invoice_indicators = ["invoice", "bill", "total", "amount", "date", "payment"]
            text_lower = invoice_text.lower()
            if not any(indicator in text_lower for indicator in invoice_indicators):
                logger.warning(f"Document {document_path} does not appear to be an invoice")
                return InvoiceData(
                    vendor_name="Unknown",
                    invoice_number="INVALID",
                    invoice_date=datetime.now().date(),
                    total_amount=Decimal("0.00"),
                    confidence=0.1,
                    review_status="needs_review",
                    error_message="Document does not appear to be an invoice"
                )

            # Check RAG for similar invoices
            rag_result = self.rag_index.classify_invoice(invoice_text)
            if rag_result['status'] == 'similar_error':
                logger.warning(f"Invoice similar to known error: {rag_result['matched_invoice_id']}")

            try:
                # Use OpenAI API to extract fields
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Extract the following fields from the invoice text and return them in JSON format: vendor_name, invoice_number, invoice_date, total_amount. Convert any amounts to GBP if not already in GBP. Ensure total_amount is a numeric string without currency symbols. Always set currency field to 'GBP'."},
                        {"role": "user", "content": invoice_text}
                    ],
                    response_format={"type": "json_object"}
                )
                json_data = json.loads(response.choices[0].message.content)
                extracted_data = {
                    "vendor_name": json_data.get("vendor_name", ""),
                    "invoice_number": json_data.get("invoice_number", ""),
                    "invoice_date": json_data.get("invoice_date", ""),
                    "total_amount": json_data.get("total_amount", ""),
                    "currency": "GBP"  # Always set to GBP
                }
                cleaned_total_amount = re.sub(r'[^\d.]', '', extracted_data["total_amount"])
                extracted_data["total_amount"] = cleaned_total_amount

                # Check for required fields and set confidence accordingly
                if not extracted_data.get("invoice_number") or not extracted_data.get("total_amount"):
                    logger.warning("Missing required fields in extracted data")
                    confidence = 0.1
                    review_status = "needs_review"
                    error_message = "Missing required invoice fields"
                else:
                    confidence = compute_confidence_score(extracted_data)
                    review_status = "pending"
                    error_message = None

            except Exception as e:
                logger.warning(f"Extraction failed: {str(e)}. Using fallback values.")
                extracted_data = {
                    "vendor_name": "Unknown",
                    "invoice_number": "FAILED",
                    "invoice_date": datetime.now().date().isoformat(),
                    "total_amount": "0.00"
                }
                confidence = 0.1
                review_status = "needs_review"
                error_message = f"Extraction failed: {str(e)}"

            invoice_data = InvoiceData(
                vendor_name=extracted_data.get("vendor_name", "Unknown"),
                invoice_number=extracted_data.get("invoice_number", "INVALID"),
                invoice_date=extracted_data.get("invoice_date", datetime.now().date().isoformat()),
                total_amount=Decimal(str(extracted_data.get("total_amount", "0.00"))),
                confidence=confidence,
                review_status=review_status,
                error_message=error_message
            )
            logger.info(f"Extraction completed with confidence {confidence}")
            return invoice_data

        except Exception as e:
            logger.error(f"Critical error during extraction: {str(e)}", exc_info=True)
            return InvoiceData(
                vendor_name="Error",
                invoice_number="ERROR",
                invoice_date=datetime.now().date(),
                total_amount=Decimal("0.00"),
                confidence=0.0,
                review_status="needs_review",
                error_message=f"Critical error: {str(e)}"
            )

if __name__ == "__main__":
    async def main():
        agent = InvoiceExtractionAgent()
        sample_pdf = "data/raw/invoices/invoice_0_missing_product_code.pdf"
        result = await agent.run(sample_pdf)
        print(result.model_dump_json(indent=2))
    asyncio.run(main())