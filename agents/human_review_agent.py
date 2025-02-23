# /agents/human_review_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
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

        # Check confidence threshold
        if invoice_data.confidence < 0.8:
            needs_review = True
            review_reasons.append("Low confidence score")
        
        # Check validation status
        if validation_result.status != "valid":
            needs_review = True
            review_reasons.append("Validation failed")
            
        # Check for anomalies
        if "anomalies" in validation_result.errors:
            needs_review = True
            review_reasons.append("Anomalies detected")
        
        if needs_review:
            logger.debug(f"Flagging for review: {review_reasons}")
            review_task = {
                "status": "needs_review",
                "invoice_data": invoice_data.model_dump(),
                "validation_errors": validation_result.errors,
                "review_reasons": review_reasons
            }
        else:
            logger.debug("Approving invoice: all checks passed")
            review_task = {
                "status": "approved", 
                "invoice_data": invoice_data.model_dump()
            }
        
        logger.info(f"Review result: {review_task}")
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