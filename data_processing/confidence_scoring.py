from typing import Dict, Any
import logging
from config.logging_config import setup_logging

logger = setup_logging()

def compute_confidence_score(extracted_data: Dict[str, Any]) -> float:
    """Compute an overall confidence score for extracted invoice data."""
    try:
        # If data is already processed (has top-level confidence)
        if isinstance(extracted_data, dict) and "confidence" in extracted_data:
            return float(extracted_data["confidence"])
        
        # Handle the case where fields have individual confidence scores
        confidences = []
        
        # Weight factors for different fields
        field_weights = {
            "invoice_number": 2.0,  # Critical field
            "total_amount": 2.0,    # Critical field
            "vendor_name": 1.5,     # Important field
            "invoice_date": 1.5,    # Important field
            "po_number": 1.0,       # Standard field
            "tax_amount": 1.0       # Standard field
        }
        
        total_weight = 0
        weighted_sum = 0
        
        for field, value in extracted_data.items():
            if isinstance(value, dict) and "confidence" in value:
                weight = field_weights.get(field, 1.0)
                total_weight += weight
                weighted_sum += float(value["confidence"]) * weight
                confidences.append(float(value["confidence"]))
        
        if total_weight > 0:
            # Use weighted average if weights were applied
            avg_confidence = weighted_sum / total_weight
        elif confidences:
            # Fallback to simple average if no weights but have confidence scores
            avg_confidence = sum(confidences) / len(confidences)
        else:
            # No confidence scores found, return low confidence
            logger.warning("No confidence scores found in extracted data")
            return 0.1
        
        # Apply penalties for missing critical fields
        if "invoice_number" not in extracted_data or not extracted_data.get("invoice_number"):
            avg_confidence *= 0.5
        if "total_amount" not in extracted_data or not extracted_data.get("total_amount"):
            avg_confidence *= 0.5
        
        logger.info(f"Computed confidence score: {avg_confidence:.2f}")
        return min(max(avg_confidence, 0.0), 1.0)  # Ensure result is between 0 and 1
        
    except Exception as e:
        logger.error(f"Error computing confidence score: {str(e)}", exc_info=True)
        return 0.1  # Return low confidence on error