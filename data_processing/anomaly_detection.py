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
from datetime import datetime

logger = setup_logging()

class AnomalyDetector:
    def __init__(self):
        self.anomalies_file = Path("data/processed/anomalies.json")
        self.anomalies_file.parent.mkdir(exist_ok=True)

    def detect_anomalies(self, invoice_data: InvoiceData) -> dict:
        """Detect anomalies in invoice data and save them."""
        logger.info(f"Starting anomaly detection for invoice {invoice_data.invoice_number}")
        anomalies = {}
        
        # Check for null or empty values
        if not invoice_data.vendor_name:
            anomalies["vendor_name"] = "Missing vendor name"
            logger.debug(f"Invoice {invoice_data.invoice_number}: Missing vendor name")
            
        if not invoice_data.invoice_number:
            anomalies["invoice_number"] = "Missing invoice number"
            logger.debug("Invoice number is missing")
        
        # Check for unreasonable values
        if invoice_data.total_amount <= Decimal('0'):
            anomalies["total_amount"] = f"Invalid amount: {invoice_data.total_amount}"
            logger.debug(f"Invoice {invoice_data.invoice_number}: Negative or zero amount")
        elif invoice_data.total_amount > Decimal('1000000'):
            anomalies["total_amount"] = f"Unusually high amount: {invoice_data.total_amount}"
            logger.debug(f"Invoice {invoice_data.invoice_number}: Amount exceeds 1M")
        
        # Check confidence scores - standardized to 0.9 threshold
        if invoice_data.confidence < 0.9:
            anomalies["confidence"] = f"Low confidence score: {invoice_data.confidence}"
            logger.debug(f"Invoice {invoice_data.invoice_number}: Low confidence {invoice_data.confidence}")
        
        # Date validation
        if invoice_data.invoice_date:
            today = datetime.now().date()
            if invoice_data.invoice_date > today:
                anomalies["invoice_date"] = f"Future date: {invoice_data.invoice_date}"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Future date detected")
            elif (today - invoice_data.invoice_date).days > 365:
                anomalies["invoice_date"] = f"Invoice older than 1 year: {invoice_data.invoice_date}"
                logger.debug(f"Invoice {invoice_data.invoice_number}: Invoice too old")
        
        # Tax amount validation
        if invoice_data.tax_amount:
            if invoice_data.tax_amount > invoice_data.total_amount:
                msg = f"Tax amount ({invoice_data.tax_amount}) greater than total amount ({invoice_data.total_amount})"
                anomalies["tax_amount"] = msg
                logger.debug(f"Invoice {invoice_data.invoice_number}: {msg}")
            elif invoice_data.tax_amount < Decimal('0'):
                msg = f"Negative tax amount: {invoice_data.tax_amount}"
                anomalies["tax_amount"] = msg
                logger.debug(f"Invoice {invoice_data.invoice_number}: {msg}")
        
        # If anomalies found, save them with detailed information
        if anomalies:
            self._save_anomaly({
                "invoice_number": invoice_data.invoice_number,
                "vendor_name": invoice_data.vendor_name,
                "anomalies": anomalies,
                "detection_time": datetime.now().isoformat(),
                "invoice_data": invoice_data.model_dump(),
                "severity": "high" if len(anomalies) > 2 else "medium" if len(anomalies) > 1 else "low",
                "status": "detected",
                "details": {
                    "total_amount": str(invoice_data.total_amount),
                    "confidence": invoice_data.confidence,
                    "date": str(invoice_data.invoice_date)
                }
            })
            logger.info(f"Detected {len(anomalies)} anomalies for invoice {invoice_data.invoice_number}")
            logger.debug(f"Anomaly details: {anomalies}")
        else:
            logger.info(f"No anomalies detected for invoice {invoice_data.invoice_number}")
        
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