# Detects invoice anomalies

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from typing import Dict, Any
import json
from datetime import datetime
from decimal import Decimal
from models.invoice import InvoiceData
from config.logging_config import logger
from data_processing.confidence_scoring import compute_confidence_score

class AnomalyDetector:
    def __init__(self):
        self.anomaly_threshold = 0.9  # Increased from 0.8 to match new confidence scoring
        self.amount_threshold = Decimal('1000000')  # £1M threshold for large amounts
        self.historical_data_file = os.path.join('data', 'processed', 'structured_invoices.json')

    def detect_anomalies(self, invoice_data: InvoiceData) -> Dict[str, Any]:
        """Detect anomalies in invoice data using confidence scores and business rules."""
        anomalies = {}
        try:
            # Check confidence score
            if invoice_data.confidence < self.anomaly_threshold:
                anomalies["low_confidence"] = {
                    "score": invoice_data.confidence,
                    "threshold": self.anomaly_threshold,
                    "reason": f"Confidence score {invoice_data.confidence:.2f} below threshold {self.anomaly_threshold}"
                }

            # Check amount thresholds
            if invoice_data.total_amount > self.amount_threshold:
                anomalies["high_amount"] = {
                    "amount": str(invoice_data.total_amount),
                    "threshold": str(self.amount_threshold),
                    "reason": f"Amount £{invoice_data.total_amount} exceeds threshold £{self.amount_threshold}"
                }

            # Check for duplicates using historical data
            duplicate_check = self._check_duplicates(invoice_data)
            if duplicate_check:
                anomalies["duplicate"] = duplicate_check

            # Check for date anomalies
            date_check = self._validate_date(invoice_data.invoice_date)
            if date_check:
                anomalies["date_issue"] = date_check

            # Check for suspicious patterns
            if invoice_data.tax_amount and invoice_data.total_amount:
                if invoice_data.tax_amount > invoice_data.total_amount * Decimal('0.3'):
                    anomalies["suspicious_tax"] = {
                        "tax_amount": str(invoice_data.tax_amount),
                        "total_amount": str(invoice_data.total_amount),
                        "reason": "Tax amount unusually high relative to total"
                    }

            if anomalies:
                logger.warning(f"Anomalies detected for invoice {invoice_data.invoice_number}: {anomalies}")
            else:
                logger.info(f"No anomalies detected for invoice {invoice_data.invoice_number}")

            return anomalies

        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def _check_duplicates(self, invoice_data: InvoiceData) -> Dict[str, Any]:
        """Check for duplicate invoices in historical data."""
        try:
            if not os.path.exists(self.historical_data_file):
                return None

            with open(self.historical_data_file, 'r') as f:
                historical_invoices = json.load(f)

            for hist_inv in historical_invoices:
                if hist_inv.get("invoice_number") == invoice_data.invoice_number:
                    if hist_inv.get("vendor_name") != invoice_data.vendor_name:
                        continue  # Same number but different vendor, might be coincidence

                    return {
                        "original_date": hist_inv.get("invoice_date"),
                        "original_amount": hist_inv.get("total_amount"),
                        "reason": "Invoice number already exists in system"
                    }

            return None

        except Exception as e:
            logger.error(f"Error checking duplicates: {str(e)}")
            return None

    def _validate_date(self, invoice_date) -> Dict[str, Any]:
        """Check for date-related anomalies."""
        try:
            current_date = datetime.now().date()
            invoice_date = datetime.strptime(str(invoice_date), "%Y-%m-%d").date()

            # Future date check (allowing up to 7 days in future for processing lag)
            if invoice_date > current_date:
                return {
                    "date": str(invoice_date),
                    "current_date": str(current_date),
                    "reason": "Invoice date is in the future"
                }

            # Very old invoice check (over 1 year old)
            days_old = (current_date - invoice_date).days
            if days_old > 365:
                return {
                    "date": str(invoice_date),
                    "age_in_days": days_old,
                    "reason": "Invoice is over 1 year old"
                }

            return None

        except Exception as e:
            logger.error(f"Error validating date: {str(e)}")
            return {
                "error": str(e),
                "reason": "Invalid date format"
            }

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