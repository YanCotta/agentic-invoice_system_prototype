# /agents/matching_agent.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
import asyncio
import pandas as pd
from fuzzywuzzy import fuzz
from config.logging_config import logger  # Import singleton logger
from agents.base_agent import BaseAgent
from models.invoice import InvoiceData

class PurchaseOrderMatchingAgent:
    def __init__(self):
        # Updated to fix the relative path for vendor_data.csv
        self.po_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'vendor_data.csv')
        try:
            self.po_data = self._load_po_data(self.po_file)
        except Exception as e:
            logger.error(f"Failed to initialize PO data: {str(e)}")
            self.po_data = pd.DataFrame(columns=["Vendor Name", "Approved PO List"])

    def _load_po_data(self, po_file: str) -> pd.DataFrame:
        logger.debug(f"Loading PO data from: {po_file}")
        try:
            if not os.path.exists(po_file):
                logger.error(f"PO file not found: {po_file}")
                return pd.DataFrame(columns=["Vendor Name", "Approved PO List"])
            
            df = pd.read_csv(po_file)
            required_columns = ["Vendor Name", "Approved PO List"]
            if not all(col in df.columns for col in required_columns):
                raise ValueError("PO CSV missing required columns: 'Vendor Name', 'Approved PO List'")
            logger.info(f"Loaded PO data from {po_file} with {len(df)} entries")
            logger.debug(f"PO data columns: {df.columns.tolist()}")
            return df
        except Exception as e:
            logger.error(f"Failed to load PO data: {str(e)}")
            raise

    async def run(self, invoice_data: InvoiceData) -> dict:
        try:
            logger.info(f"Starting matching process for invoice: {invoice_data.invoice_number}")
            logger.debug(f"Invoice data for matching: {invoice_data.model_dump()}")
            
            if self.po_data.empty:
                logger.warning("No PO data available for matching")
                return {
                    "status": "error",
                    "message": "No PO data available",
                    "po_number": None,
                    "match_confidence": 0.0
                }

            matches = []
            for _, po in self.po_data.iterrows():
                try:
                    logger.debug(f"Comparing with PO: {po['Approved PO List']}")
                    vendor_similarity = fuzz.token_sort_ratio(
                        str(invoice_data.vendor_name).lower(),
                        str(po["Vendor Name"]).lower()
                    )
                    match_confidence = vendor_similarity / 100
                    logger.debug(f"Vendor similarity score: {vendor_similarity} (confidence: {match_confidence})")
                    if match_confidence > 0.85:
                        matches.append({
                            "po_number": po["Approved PO List"],
                            "match_confidence": match_confidence
                        })
                except Exception as e:
                    logger.error(f"Error comparing vendor names: {str(e)}")
                    continue

            if matches:
                best_match = max(matches, key=lambda x: x["match_confidence"])
                result = {
                    "status": "matched",
                    "po_number": best_match["po_number"],
                    "match_confidence": best_match["match_confidence"]
                }
                logger.info(f"Best match found for invoice {invoice_data.invoice_number}: {best_match}")
            else:
                result = {
                    "status": "unmatched",
                    "po_number": None,
                    "match_confidence": 0.0
                }
                logger.info(f"No matches found for invoice {invoice_data.invoice_number}")

            logger.debug(f"Matching result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error during matching process: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "po_number": None,
                "match_confidence": 0.0
            }

if __name__ == "__main__":
    async def main():
        agent = PurchaseOrderMatchingAgent()
        sample_data = InvoiceData(
            vendor_name="ABC Corp Ltd.",
            invoice_number="INV-2024-001",
            invoice_date="2024-02-18",
            total_amount="7595.00",
            confidence=0.955
        )
        result = await agent.run(sample_data)
        print(result)
    
    asyncio.run(main())