from typing import Dict, Any
import logging
from config.logging_config import setup_logging
from decimal import Decimal, InvalidOperation

logger = setup_logging()

def compute_confidence_score(extracted_data: Dict[str, Any]) -> float:
    """
    Compute an overall confidence score for extracted invoice data.
    Uses weighted scoring for different fields and applies penalties for missing or invalid data.
    """
    try:
        # If data is already processed (has top-level confidence)
        if isinstance(extracted_data, dict) and "confidence" in extracted_data and not isinstance(extracted_data["confidence"], dict):
            return float(extracted_data["confidence"])
        
        # Field weights - critical fields have higher weights
        field_weights = {
            "invoice_number": 2.0,  # Critical field
            "total_amount": 2.0,    # Critical field
            "vendor_name": 1.5,     # Important field
            "invoice_date": 1.5,    # Important field
            "po_number": 1.0,       # Standard field
            "tax_amount": 1.0,      # Standard field
            "currency": 1.0         # Standard field
        }
        
        total_weight = 0
        weighted_sum = 0
        field_count = 0
        
        # Process each field
        for field, value in extracted_data.items():
            weight = field_weights.get(field, 1.0)
            
            # Handle nested confidence values
            if isinstance(value, dict) and "confidence" in value:
                field_confidence = float(value["confidence"])
                field_value = value.get("value")
            else:
                # Default confidence based on field presence and validity
                field_value = value
                field_confidence = 0.95 if value else 0.1
            
            # Additional validation checks
            if field == "total_amount":
                try:
                    amount = Decimal(str(field_value)) if field_value else Decimal('0')
                    if amount <= Decimal('0'):
                        field_confidence *= 0.5  # Penalty for non-positive amounts
                except (InvalidOperation, ValueError):
                    field_confidence *= 0.3  # Larger penalty for invalid amounts
            
            elif field == "invoice_date":
                if not field_value or not isinstance(field_value, (str, bytes)) or len(field_value) < 8:
                    field_confidence *= 0.5  # Penalty for missing/invalid dates
            
            # Apply weights and accumulate
            total_weight += weight
            weighted_sum += field_confidence * weight
            field_count += 1
            
            logger.debug(f"Field: {field}, Value: {field_value}, Confidence: {field_confidence}, Weight: {weight}")
        
        # Calculate final score
        if total_weight > 0:
            avg_confidence = weighted_sum / total_weight
        elif field_count > 0:
            avg_confidence = weighted_sum / field_count
        else:
            logger.warning("No valid fields found for confidence calculation")
            return 0.1
        
        # Additional penalties for critical field issues
        if "invoice_number" not in extracted_data or not extracted_data.get("invoice_number"):
            avg_confidence *= 0.5
        if "total_amount" not in extracted_data or not extracted_data.get("total_amount"):
            avg_confidence *= 0.5
        
        final_confidence = min(max(avg_confidence, 0.0), 1.0)  # Ensure result is between 0 and 1
        logger.info(f"Computed confidence score: {final_confidence:.2f}")
        
        return final_confidence
        
    except Exception as e:
        logger.error(f"Error computing confidence score: {str(e)}", exc_info=True)
        return 0.1  # Return low confidence on error