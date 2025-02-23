# Detects invoice anomalies

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import logging
from typing import List, Dict
from config.logging_config import setup_logging
from models.invoice import InvoiceData
from decimal import Decimal
import json
from pathlib import Path

logger = setup_logging()

class AnomalyDetector:
    def __init__(self):
        self.anomalies_file = Path("data/processed/anomalies.json")
        self.anomalies_file.parent.mkdir(exist_ok=True)

    def detect_anomalies(self, invoice_data: InvoiceData) -> dict:
        """Detect anomalies in invoice data and save them."""
        anomalies = {}
        
        # Check for null or empty values
        if not invoice_data.vendor_name:
            anomalies["vendor_name"] = "Missing vendor name"
        if not invoice_data.invoice_number:
            anomalies["invoice_number"] = "Missing invoice number"
        
        # Check for unreasonable values
        if invoice_data.total_amount <= Decimal('0'):
            anomalies["total_amount"] = f"Invalid amount: {invoice_data.total_amount}"
        if invoice_data.confidence < 0.8:
            anomalies["confidence"] = f"Low confidence score: {invoice_data.confidence}"
        
        # If anomalies found, save them
        if anomalies:
            self._save_anomaly({
                "invoice_number": invoice_data.invoice_number,
                "vendor_name": invoice_data.vendor_name,
                "anomalies": anomalies,
                "invoice_data": invoice_data.model_dump()
            })
            logger.info(f"Detected anomalies for invoice {invoice_data.invoice_number}: {anomalies}")
        
        return anomalies

    def _save_anomaly(self, anomaly_data: dict) -> None:
        """Save anomaly to anomalies.json file."""
        try:
            # Load existing anomalies or create empty list
            try:
                if self.anomalies_file.exists():
                    with self.anomalies_file.open('r') as f:
                        anomalies = json.load(f)
                else:
                    anomalies = []
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in {self.anomalies_file}, starting fresh")
                anomalies = []

            # Check if this invoice already has anomalies recorded
            invoice_number = anomaly_data.get("invoice_number")
            existing_index = next(
                (i for i, a in enumerate(anomalies) 
                if a.get("invoice_number") == invoice_number), 
                None
            )

            if existing_index is not None:
                # Update existing entry
                anomalies[existing_index] = anomaly_data
                logger.info(f"Updated existing anomaly for invoice {invoice_number}")
            else:
                # Add new entry
                anomalies.append(anomaly_data)
                logger.info(f"Added new anomaly for invoice {invoice_number}")

            # Save updated anomalies
            with self.anomalies_file.open('w') as f:
                json.dump(anomalies, f, indent=4)
                logger.info(f"Saved anomaly to {self.anomalies_file}")

        except Exception as e:
            logger.error(f"Failed to save anomaly: {str(e)}", exc_info=True)

if __name__ == "__main__":
    detector = AnomalyDetector()
    sample_data = InvoiceData(
        vendor_name="ABC Corp Ltd.",
        invoice_number="INV-2024-001",
        invoice_date="2024-02-18",
        total_amount="7595.00",
        confidence=0.955
    )
    past_invoices = [
        InvoiceData(vendor_name="XYZ Inc.", invoice_number="INV-2024-002", invoice_date="2024-02-17", total_amount="1000.00", confidence=0.9)
    ]
    result = detector.detect_anomalies(sample_data)
    print(result)