# /agents/validator_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from datetime import datetime
from config.logging_config import logger  # Import singleton logger
from agents.base_agent import BaseAgent
from models.invoice import InvoiceData
from models.validation_schema import ValidationResult
from data_processing.anomaly_detection import AnomalyDetector
from decimal import Decimal

class InvoiceValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.anomaly_detector = AnomalyDetector()

    async def run(self, invoice_data: InvoiceData) -> ValidationResult:
        logger.info(f"Validating invoice data: {invoice_data.invoice_number}")
        logger.debug(f"Starting validation for invoice: {invoice_data.model_dump()}")
        errors = {}

        logger.debug("Checking for missing required fields")
        if not invoice_data.vendor_name:
            errors["vendor_name"] = "Missing"
            logger.debug("Vendor name missing")
        if not invoice_data.invoice_number:
            errors["invoice_number"] = "Missing"
            logger.debug("Invoice number missing")
        if not invoice_data.invoice_date:
            errors["invoice_date"] = "Missing"
            logger.debug("Invoice date missing")
        if not invoice_data.total_amount:
            errors["total_amount"] = "Missing"
            logger.debug("Total amount missing")
        else:
            logger.debug(f"Validating total_amount: {invoice_data.total_amount}")
            try:
                total = float(invoice_data.total_amount)
                if total < 0:
                    errors["total_amount"] = "Negative value not allowed"
                    logger.debug("Total amount is negative")
            except ValueError:
                errors["total_amount"] = "Invalid numeric format"
                logger.debug("Total amount format invalid")

        if invoice_data.invoice_date:
            logger.debug(f"Validating invoice_date: {invoice_data.invoice_date}")
            try:
                datetime.strptime(str(invoice_data.invoice_date), "%Y-%m-%d")
            except ValueError:
                errors["invoice_date"] = "Invalid date format (expected YYYY-MM-DD)"
                logger.debug("Invoice date format invalid")

        logger.debug(f"Checking confidence: {invoice_data.confidence}")
        if invoice_data.confidence < 0.8:
            errors["confidence"] = f"Low confidence score: {invoice_data.confidence}"
            logger.debug("Confidence below threshold")

        # Add more validation rules
        if invoice_data.total_amount:
            if invoice_data.total_amount > Decimal('1000000'):
                errors["total_amount"] = "Amount exceeds maximum threshold"
                logger.debug("Total amount exceeds threshold")
            if invoice_data.tax_amount and invoice_data.tax_amount > invoice_data.total_amount:
                errors["tax_amount"] = "Tax amount greater than total amount"
                logger.debug("Invalid tax amount")

        # Currency validation
        if invoice_data.currency and len(invoice_data.currency) != 3:
            errors["currency"] = "Invalid currency code format"
            logger.debug("Invalid currency code")

        # Run anomaly detection with enhanced logging
        logger.debug("Running anomaly detection")
        try:
            anomaly_errors = await asyncio.to_thread(self.anomaly_detector.detect_anomalies, invoice_data)
            if anomaly_errors:
                logger.info(f"Anomalies detected for invoice {invoice_data.invoice_number}: {anomaly_errors}")
                errors.update(anomaly_errors)
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}", exc_info=True)
            errors["anomaly_detection"] = f"Failed: {str(e)}"

        validation_result = ValidationResult(
            status="failed" if errors else "valid",
            errors=errors
        )
        logger.info(f"Validation completed for {invoice_data.invoice_number}: {validation_result.status}")
        logger.debug(f"Validation result details: {validation_result.model_dump()}")
        return validation_result

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