# /agents/human_review_agent.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
from config.logging_config import setup_logging
from agents.base_agent import BaseAgent
from models.invoice import InvoiceData
from models.validation_schema import ValidationResult

logger = setup_logging()

class HumanReviewAgent(BaseAgent):
    def __init__(self):
        super().__init__()

    async def run(self, invoice_data: InvoiceData, validation_result: ValidationResult) -> dict:
        logger.info(f"Reviewing invoice: {invoice_data.invoice_number}")
        if invoice_data.confidence < 0.8 or validation_result.status != "valid":
            review_task = {
                "status": "needs_review",
                "invoice_data": invoice_data.model_dump(),
                "validation_errors": validation_result.errors
            }
        else:
            review_task = {"status": "approved", "invoice_data": invoice_data.model_dump()}
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