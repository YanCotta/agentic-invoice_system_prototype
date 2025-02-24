from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv  # Added dotenv loading
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

load_dotenv()  # Load environment variables

app = FastAPI(title="Invoice Review API")

# Move data models to top for clarity
class ReviewRequest(BaseModel):
    invoice_id: str
    corrections: dict
    reviewer_notes: str

class ReviewResponse(BaseModel):
    status: str
    message: str
    updated_invoice: dict = None

class InvoiceUpdate(BaseModel):
    vendor_name: str
    invoice_number: str
    invoice_date: str
    total_amount: float
    po_number: Optional[str] = None
    review_status: str = Field(..., description="Status of the review: pending, approved, or rejected")
    review_notes: Optional[str] = None

PROCESSED_DIR = Path("data/processed")
INVOICES_FILE = PROCESSED_DIR / "structured_invoices.json"

def load_invoices():
    """Helper function to load invoices file"""
    if not INVOICES_FILE.exists():
        return []
    try:
        with INVOICES_FILE.open("r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_invoices(invoices: list):
    """Helper function to save invoices file"""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with INVOICES_FILE.open("w") as f:
        json.dump(invoices, f, indent=4)

@app.get("/review/{invoice_id}", response_model=ReviewResponse)
async def get_review(invoice_id: str):
    return ReviewResponse(
        status="pending",
        message=f"Review needed for invoice {invoice_id}",
        updated_invoice={}
    )

@app.post("/review", response_model=ReviewResponse)
async def submit_review(review: ReviewRequest):
    veteran_reviewer_prompt = (
        "You are a veteran invoice reviewer. Review the provided corrections and determine the final invoice data. "
        "Return only a JSON object with fields: status and updated_invoice, without any extra commentary."
    )
    return ReviewResponse(
        status="reviewed",
        message="Invoice reviewed successfully",
        updated_invoice=review.corrections
    )

@app.post("/submit_correction", response_model=ReviewResponse)
async def submit_correction(correction: ReviewRequest):
    try:
        # Save correction to a file (replace with database logic as needed)
        with open("data/processed/corrections.json", "a") as f:
            json.dump(correction.dict(), f)
            f.write("\n")
        return ReviewResponse(
            status="corrected",
            message=f"Correction submitted for invoice {correction.invoice_id}",
            updated_invoice=correction.corrections
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/invoices/{invoice_number}")
async def update_invoice(invoice_number: str, update_data: InvoiceUpdate):
    """Update an invoice with review information and perform necessary validations."""
    try:
        invoices = load_invoices()
        if not invoices:
            raise HTTPException(status_code=404, detail="No invoices found")

        # Find the invoice to update
        invoice_index = None
        for idx, invoice in enumerate(invoices):
            if invoice.get("invoice_number") == invoice_number:
                invoice_index = idx
                break

        if invoice_index is None:
            raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")

        # Preserve fields that shouldn't be overwritten
        preserved_fields = ["original_path", "extraction_time", "validation_time", "matching_time"]
        update_dict = update_data.dict(exclude_unset=True)
        for field in preserved_fields:
            if field in invoices[invoice_index] and field not in update_dict:
                update_dict[field] = invoices[invoice_index][field]

        # Add review metadata
        update_dict["review_date"] = datetime.now().isoformat()
        if update_dict.get("review_status") in ["approved", "rejected"]:
            update_dict["resolution_date"] = datetime.now().isoformat()
            if "review_notes" in update_dict:
                update_dict["resolution_notes"] = update_dict["review_notes"]

        # Update the invoice
        invoices[invoice_index].update(update_dict)
        save_invoices(invoices)

        return {
            "status": "success",
            "message": f"Invoice {invoice_number} updated successfully",
            "updated_invoice": invoices[invoice_index]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating invoice: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Confirmed port 8000