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

logger = logging.getLogger("InvoiceProcessing")

app = FastAPI(title="Brim Invoice Processing API")
print("App created")
workflow = InvoiceProcessingWorkflow()
print("Workflow instance created")

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
        # Removing PDF copy to data/processed, only save extracted data
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing invoice: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()  # Clean up temp file

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

@app.put("/api/invoices/{invoice_number}")
async def update_invoice(invoice_number: str, update_data: dict):
    try:
        if not OUTPUT_FILE.exists():
            raise HTTPException(status_code=404, detail="No invoices found")
        
        with open(OUTPUT_FILE, "r") as f:
            invoices = json.load(f)
        
        # Find and update the invoice
        for i, inv in enumerate(invoices):
            if inv.get("invoice_number") == invoice_number:
                # Preserve certain fields that shouldn't be overwritten
                preserved_fields = ["original_path", "extraction_time", "validation_time", "matching_time"]
                for field in preserved_fields:
                    if field in inv and field not in update_data:
                        update_data[field] = inv[field]
                
                # Update resolution fields
                if update_data.get("review_status") in ["approved", "rejected"]:
                    update_data["resolution_date"] = datetime.now().isoformat()
                    if "review_notes" in update_data:
                        update_data["resolution_notes"] = update_data["review_notes"]
                
                # Update the invoice
                invoices[i].update(update_data)
                
                # Write back to file
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(invoices, f, indent=4)
                
                logger.info(f"Updated invoice {invoice_number} with review status: {update_data.get('review_status')}")
                return {"message": "Updated successfully"}
        
        raise HTTPException(status_code=404, detail="Invoice not found")
    except Exception as e:
        logger.error(f"Error updating invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

# Clean up temp directory on application exit
def cleanup_temp_directory():
    temp_dir = Path("data/temp")
    if (temp_dir.exists()):
        shutil.rmtree(temp_dir)
        logger.info("Cleaned up temporary files directory")

atexit.register(cleanup_temp_directory)