# /agents/human_review_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from datetime import datetime  # Add datetime import
from config.logging_config import logger  # Import singleton logger
from agents.base_agent import BaseAgent
from models.invoice import InvoiceData
from models.validation_schema import ValidationResult

class HumanReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    async def run(self, invoice_data: InvoiceData, validation_result: ValidationResult) -> dict:
        logger.info(f"Reviewing invoice: {invoice_data.invoice_number}")
        logger.debug(f"Invoice data: {invoice_data.model_dump()}, Validation: {validation_result.model_dump()}")
        
        # Determine if review is needed based on multiple factors
        needs_review = False
        review_reasons = []

        # Check confidence threshold - using standardized 0.9 threshold
        if invoice_data.confidence < 0.9:
            needs_review = True
            review_reasons.append(f"Low confidence score: {invoice_data.confidence}")
            logger.debug(f"Invoice {invoice_data.invoice_number}: Flagged for low confidence {invoice_data.confidence}")
        
        # Check validation status
        if validation_result.status != "valid":
            needs_review = True
            errors_str = ", ".join(validation_result.errors.keys())
            review_reasons.append(f"Validation failed: {errors_str}")
            logger.debug(f"Invoice {invoice_data.invoice_number}: Failed validation with errors in: {errors_str}")
            
        # Check for anomalies
        if "anomalies" in validation_result.errors:
            needs_review = True
            anomalies = validation_result.errors["anomalies"]
            review_reasons.append(f"Anomalies detected: {', '.join(anomalies.keys())}")
            logger.debug(f"Invoice {invoice_data.invoice_number}: Anomalies detected: {anomalies}")
        
        # Check for special case indicators
        if invoice_data.vendor_name in ["Unknown", "Error"]:
            needs_review = True
            review_reasons.append("Invalid vendor name")
            logger.debug(f"Invoice {invoice_data.invoice_number}: Invalid vendor name: {invoice_data.vendor_name}")
            
        if invoice_data.invoice_number in ["INVALID", "ERROR", "FAILED", "UNREADABLE"]:
            needs_review = True
            review_reasons.append("Invalid invoice number")
            logger.debug(f"Invoice {invoice_data.invoice_number}: Special case invoice number detected")
        
        if needs_review:
            logger.debug(f"Invoice {invoice_data.invoice_number}: Flagged for review due to: {review_reasons}")
            review_task = {
                "status": "needs_review",
                "invoice_data": invoice_data.model_dump(),
                "validation_errors": validation_result.errors,
                "review_reasons": review_reasons,
                "review_priority": "high" if len(review_reasons) > 2 else "medium" if len(review_reasons) > 1 else "low"
            }
        else:
            logger.debug(f"Invoice {invoice_data.invoice_number}: Approved - all checks passed")
            review_task = {
                "status": "approved", 
                "invoice_data": invoice_data.model_dump(),
                "review_date": datetime.now().isoformat()
            }
        
        logger.info(f"Review completed for {invoice_data.invoice_number} with status: {review_task['status']}")
        if needs_review:
            logger.info(f"Review reasons for {invoice_data.invoice_number}: {review_reasons}")
        
        return review_task

if __name__ == "__main__":
    async def main():
        sample_data = InvoiceData(
            vendor_name="ABC Corp Ltd.",
            invoice_number="INV-2024-001",
            invoice_date="2024-02-18",
            total_amount="7595.00",
            confidence=0.955
        )
        validation_result = ValidationResult(status="valid", errors={})
        agent = HumanReviewAgent()
        result = await agent.run(sample_data, validation_result)
        print(result)
    asyncio.run(main())