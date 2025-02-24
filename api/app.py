print("Starting api/app.py")
from dotenv import load_dotenv
import sys
import os
print("sys imported")
print("os imported")
load_dotenv()  # Load environment variables from .env
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
print("Path adjusted")
from fastapi import FastAPI, UploadFile, File, HTTPException
print("FastAPI imported")
from workflows.orchestrator import InvoiceProcessingWorkflow
print("Workflow imported")
import json
print("json imported")
from pathlib import Path
print("Path imported")
import uuid
print("uuid imported")
import logging
print("logging imported")
from glob import glob  # added for process_all_invoices endpoint
from fastapi.responses import FileResponse
import shutil
import atexit
from datetime import datetime  # Add datetime import
from api.review_api import router as review_router

logger = logging.getLogger("InvoiceProcessing")

app = FastAPI(title="Brim Invoice Processing API")
print("App created")
workflow = InvoiceProcessingWorkflow()
print("Workflow instance created")

@app.get("/")
async def root():
    return {"message": "Brim Invoice Processing API"}

OUTPUT_FILE = Path("data/processed/structured_invoices.json")

def save_invoice(invoice_entry, output_file="data/processed/structured_invoices.json"):
    """Save extracted invoice data to JSON, preserving existing entries."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                all_invoices = json.load(f)
        else:
            all_invoices = []
    except json.JSONDecodeError:
        logger.warning(f"Invalid JSON in {output_file}, starting fresh")
        all_invoices = []
    
    # Update existing entry or add new one
    invoice_number = invoice_entry.get("invoice_number")
    if invoice_number:
        # Look for existing entry to update
        for i, inv in enumerate(all_invoices):
            if inv.get("invoice_number") == invoice_number:
                all_invoices[i] = invoice_entry
                break
        else:
            # No existing entry found, append new one
            all_invoices.append(invoice_entry)
    else:
        # No invoice number, just append
        all_invoices.append(invoice_entry)
    
    # Write updated data
    with open(output_file, 'w') as f:
        json.dump(all_invoices, f, indent=4)
    logger.info(f"Saved invoice data to {output_file}")

@app.post("/api/upload_invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Process an uploaded invoice PDF and save it."""
    try:
        temp_path = Path(f"data/temp/{uuid.uuid4()}.pdf")
        temp_path.parent.mkdir(exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        result = await workflow.process_invoice(str(temp_path))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()

@app.get("/api/invoices")
async def get_invoices():
    """Fetch all processed invoices."""
    try:
        if not OUTPUT_FILE.exists():
            logger.info("Structured invoices file not found, returning empty list")
            return []
        with OUTPUT_FILE.open("r") as f:
            data = json.load(f)
            # Ensure timing fields exist and are non-zero if processing happened
            for invoice in data:
                for timing_field in ["extraction_time", "validation_time", "matching_time", "review_time", "total_time"]:
                    invoice[timing_field] = float(invoice.get(timing_field, 0.0) or 0.0)
            logger.info(f"Successfully loaded {len(data)} invoices")
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error fetching invoices: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch invoices: {str(e)}")

@app.get("/api/process_all_invoices")
async def process_all_invoices():
    """Process all invoice PDFs and save results."""
    try:
        invoice_files = glob("data/raw/invoices/*.pdf")
        results = []
        for file in invoice_files:
            try:
                result = await workflow.process_invoice(file)
                # Removed PDF copying to data/processed
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {file}: {str(e)}")
                continue
        
        if results:
            logger.info(f"Successfully processed {len(results)} invoices")
            return {"message": f"Processed {len(results)} invoices"}
        else:
            logger.warning("No invoices were processed successfully")
            return {"message": "No invoices were processed"}
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing invoices: {str(e)}")

@app.get("/api/invoice_pdf/{invoice_number}")
async def get_invoice_pdf(invoice_number: str):
    """Get the PDF file for a specific invoice from the raw invoices directory."""
    try:
        # First try to find the original path from structured_invoices.json
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, "r") as f:
                invoices = json.load(f)
                for inv in invoices:
                    if inv.get("invoice_number") == invoice_number:
                        original_path = inv.get("original_path")
                        if original_path and Path(original_path).exists():
                            return FileResponse(
                                original_path, 
                                media_type="application/pdf",
                                filename=f"{invoice_number}.pdf"
                            )
        
        # Fallback: search in raw/invoices directory
        raw_invoices_dir = Path("data/raw/invoices")
        matching_files = list(raw_invoices_dir.glob(f"*{invoice_number}*.pdf"))
        if matching_files:
            return FileResponse(
                matching_files[0],
                media_type="application/pdf",
                filename=f"{invoice_number}.pdf"
            )
        
        raise HTTPException(status_code=404, detail="PDF not found")
    except Exception as e:
        logger.error(f"Error retrieving PDF for invoice {invoice_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/invoices/{invoice_number}")
async def update_invoice(invoice_number: str, updated_data: dict):
    """Update an invoice in the structured_invoices.json file."""
    try:
        if not OUTPUT_FILE.exists():
            raise HTTPException(status_code=404, detail="No invoices found")
        
        with OUTPUT_FILE.open("r") as f:
            invoices = json.load(f)
        
        for invoice in invoices:
            if invoice["invoice_number"] == invoice_number:
                # Preserve metadata fields
                preserved_fields = ["original_path", "extraction_time", "validation_time", "matching_time"]
                for field in preserved_fields:
                    if field in invoice and field not in updated_data:
                        updated_data[field] = invoice[field]
                
                # Update timestamp
                updated_data["last_modified"] = datetime.now().isoformat()
                
                # Update the invoice
                invoice.update(updated_data)
                
                with OUTPUT_FILE.open("w") as f:
                    json.dump(invoices, f, indent=4)
                return {"status": "success", "message": f"Invoice {invoice_number} updated"}
        
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_number} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Return basic processing metrics."""
    try:
        if not OUTPUT_FILE.exists():
            return {
                "total_invoices": 0,
                "avg_confidence": 0,
                "avg_processing_time": 0
            }
        
        with OUTPUT_FILE.open("r") as f:
            invoices = json.load(f)
        
        total = len(invoices)
        avg_confidence = sum(float(inv.get("confidence", 0) or 0) for inv in invoices) / total if total > 0 else 0
        avg_time = sum(float(inv.get("total_time", 0) or 0) for inv in invoices) / total if total > 0 else 0
        
        return {
            "total_invoices": total,
            "avg_confidence": round(avg_confidence, 3),
            "avg_processing_time": round(avg_time, 2)
        }
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Clean up temp directory on application exit
def cleanup_temp_directory():
    temp_dir = Path("data/temp")
    if (temp_dir.exists()):
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary files directory")

atexit.register(cleanup_temp_directory)

# Include the review router
app.include_router(review_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.app:app", host="0.0.0.0", port=8000, reload=True)