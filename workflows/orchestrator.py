import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
import json
from pathlib import Path
import uuid
from config.logging_config import logger  # Import singleton logger
from config.monitoring import Monitoring  # Import Monitoring class
from agents.extractor_agent import InvoiceExtractionAgent
from agents.validator_agent import InvoiceValidationAgent
from agents.matching_agent import PurchaseOrderMatchingAgent
from agents.human_review_agent import HumanReviewAgent

class InvoiceProcessingWorkflow:
    def __init__(self):
        logger.debug("Initializing workflow agents")
        self.extraction_agent = InvoiceExtractionAgent()
        self.validation_agent = InvoiceValidationAgent()
        self.matching_agent = PurchaseOrderMatchingAgent()
        self.review_agent = HumanReviewAgent()

    async def _retry_with_backoff(self, func, max_retries=3, base_delay=1):
        logger.debug(f"Starting retry mechanism with max_retries={max_retries}, base_delay={base_delay}")
        for attempt in range(max_retries):
            try:
                result = await func()
                logger.debug(f"Retry attempt {attempt + 1} succeeded")
                return result
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} retries failed: {str(e)}")
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay}s...")
                await asyncio.sleep(delay)

    async def process_invoice(self, document_path: str) -> dict:
        logger.info(f"Starting invoice processing for: {document_path}")
        logger.debug(f"Processing pipeline initiated for document: {document_path}")

        monitoring = Monitoring()
        extraction_time = None
        validation_time = None
        matching_time = None
        review_time = None

        try:
            monitoring.start_timer("extraction")
            extracted_data = await self._retry_with_backoff(lambda: self.extraction_agent.run(document_path))
            extraction_time = monitoring.stop_timer("extraction")
            logger.info(f"Extraction completed: {extracted_data}")
            extracted_dict = {
                "vendor_name": extracted_data.vendor_name,
                "invoice_number": extracted_data.invoice_number,
                "invoice_date": extracted_data.invoice_date.strftime("%Y-%m-%d"),
                "total_amount": str(extracted_data.total_amount),
                "confidence": extracted_data.confidence,
                "po_number": extracted_data.po_number,
                "tax_amount": extracted_data.tax_amount,
                "currency": extracted_data.currency,
                "status": "extracted",  # Add status to track progress
                "extraction_time": extraction_time
            }
            # Save initial extraction data
            self._save_invoice_entry(extracted_dict)
        except Exception as e:
            logger.error(f"Extraction failed after retries: {str(e)}")
            extraction_time = monitoring.stop_timer("extraction")
            invoice_entry = {
                "status": "error",
                "message": str(e),
                "extraction_time": extraction_time,
                "validation_time": 0,
                "matching_time": 0,
                "review_time": 0,
                "total_time": extraction_time
            }
            self._save_invoice_entry(invoice_entry)
            return invoice_entry

        try:
            monitoring.start_timer("validation")
            validation_result = await self._retry_with_backoff(lambda: self.validation_agent.run(extracted_data))
            validation_time = monitoring.stop_timer("validation")
            logger.info(f"Validation result: {validation_result}, time: {validation_time:.2f}s")
            # Update and save after validation
            extracted_dict.update({
                "validation_status": validation_result.status,
                "validation_errors": validation_result.errors,
                "validation_time": validation_time,
                "status": "validated"
            })
            self._save_invoice_entry(extracted_dict)
        except Exception as e:
            logger.error(f"Validation failed after retries: {str(e)}")
            validation_time = monitoring.stop_timer("validation")
            invoice_entry = {
                **extracted_dict,
                "status": "error",
                "message": str(e),
                "extraction_time": extraction_time,
                "validation_time": validation_time,
                "matching_time": 0,
                "review_time": 0,
                "total_time": extraction_time + validation_time
            }
            self._save_invoice_entry(invoice_entry)
            return invoice_entry

        try:
            monitoring.start_timer("matching")
            matching_result = await self._retry_with_backoff(lambda: self.matching_agent.run(extracted_data))
            matching_time = monitoring.stop_timer("matching")
            logger.info(f"Matching result: {matching_result}, time: {matching_time:.2f}s")
            # Update and save after matching
            extracted_dict.update({
                "matching_status": matching_result["status"],
                "matching_time": matching_time,
                "status": "matched"
            })
            self._save_invoice_entry(extracted_dict)
        except Exception as e:
            logger.error(f"Matching failed after retries: {str(e)}")
            matching_time = monitoring.stop_timer("matching")
            invoice_entry = {
                **extracted_dict,
                "validation_status": validation_result.status,
                "matching_status": "error",
                "matching_error": str(e),
                "review_status": "skipped",
                "extraction_time": extraction_time,
                "validation_time": validation_time,
                "matching_time": matching_time,
                "review_time": 0,
                "total_time": extraction_time + validation_time + matching_time
            }
            self._save_invoice_entry(invoice_entry)
            return invoice_entry

        try:
            monitoring.start_timer("review")
            review_result = await self._retry_with_backoff(lambda: self.review_agent.run(extracted_data, validation_result))
            review_time = monitoring.stop_timer("review")
            logger.info(f"Review result: {review_result}, time: {review_time:.2f}s")
            # Update and save after review
            extracted_dict.update({
                "review_status": review_result.get("status", "unknown"),
                "review_time": review_time,
                "status": "completed",
                "total_time": extraction_time + validation_time + matching_time + review_time
            })
            self._save_invoice_entry(extracted_dict)
        except Exception as e:
            logger.error(f"Review failed after retries: {str(e)}")
            review_time = monitoring.stop_timer("review")
            invoice_entry = {
                **extracted_dict,
                "validation_status": validation_result.status,
                "matching_status": matching_result["status"],
                "review_status": "error",
                "review_error": str(e),
                "extraction_time": extraction_time,
                "validation_time": validation_time,
                "matching_time": matching_time,
                "review_time": review_time,
                "total_time": extraction_time + validation_time + matching_time + review_time
            }
            self._save_invoice_entry(invoice_entry)
            return invoice_entry

        total_time = extraction_time + validation_time + matching_time + review_time
        invoice_entry = {
            **extracted_dict,
            "validation_status": validation_result.status,
            "validation_errors": validation_result.errors,
            "matching_status": matching_result.get("status", "unknown"),
            "review_status": review_result.get("status", "unknown"),
            "extraction_time": extraction_time,
            "validation_time": validation_time,
            "matching_time": matching_time,
            "review_time": review_time,
            "total_time": total_time,
            "document_path": document_path  # Add document path for reference
        }
        self._save_invoice_entry(invoice_entry)

        result = {
            "extracted_data": extracted_dict,
            "validation_result": validation_result.model_dump(),
            "matching_result": matching_result,
            "review_result": review_result,
            "extraction_time": extraction_time,
            "validation_time": validation_time,
            "matching_time": matching_time,
            "review_time": review_time,
            "total_time": total_time
        }
        logger.info(f"Invoice processing completed: {document_path}")
        logger.debug(f"Final result: {result}")
        return result

    def _save_invoice_entry(self, invoice_entry, output_file="data/processed/structured_invoices.json"):
        try:
            os.makedirs("data/processed", exist_ok=True)
            try:
                if os.path.exists(output_file):
                    with open(output_file, "r") as f:
                        all_invoices = json.load(f)
                else:
                    all_invoices = []
            except (FileNotFoundError, json.JSONDecodeError):
                all_invoices = []
            
            # Update existing entry or add new one
            invoice_number = invoice_entry.get("invoice_number")
            if not invoice_number:
                logger.warning("Invoice entry missing invoice_number, generating temporary ID")
                invoice_number = f"TEMP_{uuid.uuid4()}"
                invoice_entry["invoice_number"] = invoice_number

            # Find and update existing entry or append new one
            updated = False
            for i, inv in enumerate(all_invoices):
                if inv.get("invoice_number") == invoice_number:
                    # Preserve certain fields from existing entry
                    preserve_fields = ["document_path"]
                    for field in preserve_fields:
                        if field in inv and field not in invoice_entry:
                            invoice_entry[field] = inv[field]
                    all_invoices[i] = invoice_entry
                    updated = True
                    logger.info(f"Updated existing invoice entry: {invoice_number}")
                    break
            
            if not updated:
                all_invoices.append(invoice_entry)
                logger.info(f"Added new invoice entry: {invoice_number}")
            
            # Write updated data back to file
            with open(output_file, "w") as f:
                json.dump(all_invoices, f, indent=4)
            logger.info(f"Successfully saved invoice data to {output_file}")
            
            # Save to anomalies.json if needs review or has validation errors
            anomalies_file = "data/processed/anomalies.json"
            if (invoice_entry.get("review_status") == "needs_review" or 
                invoice_entry.get("validation_status") == "failed" or
                invoice_entry.get("confidence", 1.0) < 0.8):
                
                try:
                    if os.path.exists(anomalies_file):
                        with open(anomalies_file, "r") as f:
                            anomalies = json.load(f)
                    else:
                        anomalies = []
                except (FileNotFoundError, json.JSONDecodeError):
                    anomalies = []
                
                # Check if this anomaly is already recorded
                anomaly_exists = any(
                    a.get("invoice_number") == invoice_entry.get("invoice_number")
                    for a in anomalies
                )
                
                if not anomaly_exists:
                    anomalies.append({
                        **invoice_entry,
                        "anomaly_reason": "Low confidence" if invoice_entry.get("confidence", 1.0) < 0.8
                                        else "Validation failed" if invoice_entry.get("validation_status") == "failed"
                                        else "Needs review"
                    })
                    with open(anomalies_file, "w") as f:
                        json.dump(anomalies, f, indent=4)
                    logger.info(f"Saved anomaly to {anomalies_file}")
                
        except Exception as e:
            logger.error(f"Failed to save invoice entry: {str(e)}", exc_info=True)

async def main():
    workflow = InvoiceProcessingWorkflow()
    invoice_dir = "data/raw/invoices/"
    for filename in os.listdir(invoice_dir):
        if filename.endswith(".pdf"):
            document_path = os.path.join(invoice_dir, filename)
            try:
                logger.info(f"Starting invoice processing for: {document_path}")
                result = await workflow.process_invoice(document_path)
                logger.info(f"Processed {filename}: {result}")
                print(f"Result for {filename}: {result}")
            except Exception as e:
                logger.error(f"Failed to process {filename}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())