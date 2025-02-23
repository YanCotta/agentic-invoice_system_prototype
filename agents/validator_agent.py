# /agents/validator_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from datetime import datetime
from decimal import Decimal, InvalidOperation
from config.logging_config import logger
from agents.base_agent import BaseAgent
from models.invoice import InvoiceData
from models.validation_schema import ValidationResult
from data_processing.anomaly_detection import AnomalyDetector

class InvoiceValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.anomaly_detector = AnomalyDetector()

    async def run(self, invoice_data: InvoiceData) -> ValidationResult:
        try:
            logger.info(f"Starting validation for invoice: {invoice_data.invoice_number}")
            logger.debug(f"Validation input data: {invoice_data.model_dump()}")
            errors = {}

            # Set review status as needs_review if confidence is too low
            if invoice_data.confidence < 0.9:  # Updated threshold to match anomaly detection
                invoice_data.review_status = "needs_review"
                errors["confidence"] = f"Low confidence score: {invoice_data.confidence}"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Confidence {invoice_data.confidence} below threshold (0.9)")

            # Check for missing or invalid required fields
            if not invoice_data.vendor_name or invoice_data.vendor_name in ["Unknown", "Error"]:
                errors["vendor_name"] = "Missing or invalid vendor name"
                invoice_data.review_status = "needs_review"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid vendor name: {invoice_data.vendor_name}")

            if not invoice_data.invoice_number or invoice_data.invoice_number in ["INVALID", "ERROR", "FAILED"]:
                errors["invoice_number"] = "Missing or invalid invoice number"
                invoice_data.review_status = "needs_review"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid invoice number")

            if not invoice_data.invoice_date:
                errors["invoice_date"] = "Missing invoice date"
                invoice_data.review_status = "needs_review"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Missing date")
            else:
                try:
                    datetime.strptime(str(invoice_data.invoice_date), "%Y-%m-%d")
                except ValueError:
                    errors["invoice_date"] = "Invalid date format (expected YYYY-MM-DD)"
                    invoice_data.review_status = "needs_review"
                    logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid date format")

            # Validate total amount for GBP
            if not invoice_data.total_amount:
                errors["total_amount"] = "Missing total amount"
                invoice_data.review_status = "needs_review"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Missing total amount")
            else:
                try:
                    if invoice_data.total_amount <= Decimal('0'):
                        errors["total_amount"] = "Amount must be greater than zero"
                        invoice_data.review_status = "needs_review"
                        logger.debug(f"Invoice {invoice_data.invoice_number}: Non-positive amount: {invoice_data.total_amount}")
                    elif invoice_data.total_amount > Decimal('1000000'):
                        errors["total_amount"] = "Amount exceeds maximum threshold (£1,000,000)"
                        invoice_data.review_status = "needs_review"
                        logger.debug(f"Invoice {invoice_data.invoice_number}: Amount exceeds limit: {invoice_data.total_amount}")
                except (ValueError, TypeError, InvalidOperation):
                    errors["total_amount"] = "Invalid amount format"
                    invoice_data.review_status = "needs_review"
                    logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid amount format")

            # Currency validation - ensure GBP
            if invoice_data.currency != "GBP":
                errors["currency"] = "Only GBP currency is supported"
                invoice_data.review_status = "needs_review"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid currency: {invoice_data.currency}")

            # Tax amount validation for GBP
            if invoice_data.tax_amount:
                try:
                    if invoice_data.tax_amount > invoice_data.total_amount:
                        errors["tax_amount"] = "Tax amount greater than total amount"
                        invoice_data.review_status = "needs_review"
                        logger.debug(f"Invoice {invoice_data.invoice_number}: Tax > Total: {invoice_data.tax_amount} > {invoice_data.total_amount}")
                    elif invoice_data.tax_amount < Decimal('0'):
                        errors["tax_amount"] = "Negative tax amount"
                        invoice_data.review_status = "needs_review"
                        logger.debug(f"Invoice {invoice_data.invoice_number}: Negative tax: {invoice_data.tax_amount}")
                except (ValueError, TypeError, InvalidOperation):
                    errors["tax_amount"] = "Invalid tax amount format"
                    invoice_data.review_status = "needs_review"
                    logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid tax amount format")

            # Run anomaly detection with proper async handling
            try:
                logger.debug(f"Starting anomaly detection for invoice {invoice_data.invoice_number}")
                # Create a loop or get the current one
                loop = asyncio.get_event_loop()
                # Run the CPU-bound anomaly detection in a thread pool
                anomaly_errors = await loop.run_in_executor(
                    None, 
                    self.anomaly_detector.detect_anomalies,
                    invoice_data
                )
                if anomaly_errors:
                    logger.info(f"Anomalies detected for invoice {invoice_data.invoice_number}: {anomaly_errors}")
                    errors["anomalies"] = anomaly_errors
                    invoice_data.review_status = "needs_review"
            except Exception as e:
                logger.error(f"Anomaly detection failed for invoice {invoice_data.invoice_number}: {str(e)}", exc_info=True)
                errors["anomaly_detection"] = f"Failed: {str(e)}"
                invoice_data.review_status = "needs_review"

            # Set final review status if not already set to needs_review
            if not invoice_data.review_status:
                invoice_data.review_status = "needs_review" if errors else "approved"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Final review status: {invoice_data.review_status}")

            validation_result = ValidationResult(
                status="failed" if errors else "valid",
                errors=errors
            )
            
            logger.info(f"Validation completed for {invoice_data.invoice_number}: {validation_result.status}")
            if errors:
                logger.debug(f"Validation errors for {invoice_data.invoice_number}: {errors}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Unexpected error during validation: {str(e)}", exc_info=True)
            return ValidationResult(
                status="failed",
                errors={"critical_error": str(e)}
            )

if __name__ == "__main__":
    async def main():
        agent = InvoiceValidationAgent()
        sample_data = InvoiceData(
            vendor_name="ABC Corp Ltd.",
            invoice_number="INV-2024-001",
            invoice_date="2024-02-18",
            total_amount="7595.00",
            confidence=0.955
        )
        result = await agent.run(sample_data)
        print(result.model_dump_json(indent=2))
    
    asyncio.run(main())