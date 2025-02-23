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

# Add requirements for OpenAI
try:
    import openai
except ImportError:
    logger.error("Required packages not found. Please run: pip install openai python-dotenv")
    raise

load_dotenv()  # Load environment variables from .env

# Check for required environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.error("OPENAI_API_KEY not found in environment variables. Please ensure it is set in .env file")
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)

class InvoiceExtractionTool:
    """A simple tool to extract structured invoice data as a fallback."""
    name = "invoice_extraction_tool"
    description = "Extracts structured invoice data from text with confidence scores."

    def _run(self, invoice_text: str) -> Dict:
        logger.debug(f"Starting invoice text extraction with tool for text length: {len(invoice_text)}")
        try:
            extracted_data = self._extract_fields(invoice_text)
            # Use the proper confidence scoring function
            confidence = compute_confidence_score(extracted_data)
            logger.info(f"Extraction completed with confidence: {confidence}")
            logger.debug(f"Extracted fields: {extracted_data}")
            return {"data": extracted_data, "confidence": confidence}
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return {"error": str(e), "confidence": 0.0}

    def _extract_fields(self, text: str) -> Dict:
        """Extracts fields with individual confidence scores."""
        # Define regex patterns for key fields
        patterns = {
            "vendor_name": r"(?i)(?:vendor|supplier|from):\s*([A-Za-z0-9\s.,&-]+)",
            "invoice_number": r"(?i)(?:invoice\s*(?:#|no|number)):\s*([A-Za-z0-9-]+)",
            "invoice_date": r"(?i)(?:date|issued):\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
            "total_amount": r"(?i)(?:total|amount|sum):\s*[£$]?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
            "po_number": r"(?i)(?:po|purchase\s*order)\s*(?:#|no|number)?:\s*([A-Za-z0-9-]+)"
        }

        results = {}
        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                # Set confidence based on match quality and field importance
                if field in ["invoice_number", "total_amount"]:
                    confidence = 0.9  # Critical fields with good match
                elif field in ["vendor_name", "invoice_date"]:
                    confidence = 0.85  # Important fields with good match
                else:
                    confidence = 0.8  # Standard fields with good match
            else:
                # No match found
                if field in ["invoice_number", "total_amount"]:
                    confidence = 0.1  # Missing critical fields
                else:
                    confidence = 0.5  # Missing non-critical fields

            value = match.group(1).strip() if match else ""
            results[field] = {
                "value": value,
                "confidence": confidence
            }

        # Always set GBP as currency with high confidence
        results["currency"] = {
            "value": "GBP",
            "confidence": 1.0
        }

        return results

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
                    confidence=0.1,  # Low confidence for unreadable files
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
                    confidence=0.1,  # Low confidence for non-invoice documents
                    review_status="needs_review",
                    error_message="Document does not appear to be an invoice"
                )

            # Check RAG for similar invoices
            rag_result = self.rag_index.classify_invoice(invoice_text)
            rag_confidence_penalty = 0.2 if rag_result['status'] == 'similar_error' else 0.0
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
                
                # Create structured data with confidence scores for each field
                extracted_data = {
                    "vendor_name": {"value": json_data.get("vendor_name", ""), "confidence": 0.95},
                    "invoice_number": {"value": json_data.get("invoice_number", ""), "confidence": 0.95},
                    "invoice_date": {"value": json_data.get("invoice_date", ""), "confidence": 0.95},
                    "total_amount": {"value": json_data.get("total_amount", ""), "confidence": 0.95},
                    "currency": {"value": "GBP", "confidence": 1.0}
                }

                # Clean total amount
                if extracted_data["total_amount"]["value"]:
                    cleaned_total_amount = re.sub(r'[^\d.]', '', extracted_data["total_amount"]["value"])
                    extracted_data["total_amount"]["value"] = cleaned_total_amount
                    # If amount needed cleaning, reduce its confidence
                    if cleaned_total_amount != extracted_data["total_amount"]["value"]:
                        extracted_data["total_amount"]["confidence"] = 0.85

                # Compute confidence score based on field presence and quality
                confidence = compute_confidence_score(extracted_data)
                
                # Apply RAG penalty if similar to problematic invoices
                if rag_confidence_penalty:
                    confidence = max(0.1, confidence - rag_confidence_penalty)
                    logger.info(f"Applied RAG confidence penalty. Original: {confidence + rag_confidence_penalty}, Final: {confidence}")

                # Determine review status based on confidence and field presence
                if (not extracted_data["invoice_number"]["value"] or 
                    not extracted_data["total_amount"]["value"] or 
                    confidence < 0.9):
                    review_status = "needs_review"
                    error_message = "Missing required fields or low confidence extraction"
                else:
                    review_status = "pending"
                    error_message = None

            except Exception as e:
                logger.warning(f"Extraction failed: {str(e)}. Using fallback values.")
                extracted_data = {
                    "vendor_name": {"value": "Unknown", "confidence": 0.1},
                    "invoice_number": {"value": "FAILED", "confidence": 0.1},
                    "invoice_date": {"value": datetime.now().date().isoformat(), "confidence": 0.1},
                    "total_amount": {"value": "0.00", "confidence": 0.1},
                    "currency": {"value": "GBP", "confidence": 1.0}
                }
                confidence = 0.1  # Low confidence for failed extractions
                review_status = "needs_review"
                error_message = f"Extraction failed: {str(e)}"

            # Create InvoiceData instance with computed values
            invoice_data = InvoiceData(
                vendor_name=extracted_data["vendor_name"]["value"],
                invoice_number=extracted_data["invoice_number"]["value"],
                invoice_date=extracted_data["invoice_date"]["value"],
                total_amount=Decimal(str(extracted_data["total_amount"]["value"] or "0.00")),
                confidence=confidence,
                review_status=review_status,
                error_message=error_message,
                currency="GBP"
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