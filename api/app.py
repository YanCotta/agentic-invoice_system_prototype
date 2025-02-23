print("Starting api/app.py")
import sys
print("sys imported")
import os
print("os imported")
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

logger = logging.getLogger("InvoiceProcessing")

app = FastAPI(title="Brim Invoice Processing API")
print("App created")
workflow = InvoiceProcessingWorkflow()
print("Workflow instance created")

OUTPUT_FILE = Path("data/processed/structured_invoices.json")

def save_invoice(invoice_entry, output_file="data/processed/structured_invoices.json"):
    import os, json
    os.makedirs("data/processed", exist_ok=True)
    try:
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                all_invoices = json.load(f)
        else:
            all_invoices = []
    except json.JSONDecodeError:
        all_invoices = []
    all_invoices.append(invoice_entry)
    with open(output_file, 'w') as f:
        json.dump(all_invoices, f, indent=4)

@app.post("/api/upload_invoice")
async def upload_invoice(file: UploadFile = File(...)):
    """Process an uploaded invoice PDF and save it."""
    try:
        temp_path = Path(f"data/temp/{uuid.uuid4()}.pdf")
        temp_path.parent.mkdir(exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(await file.read())
        result = await workflow.process_invoice(str(temp_path))
        invoice_number = result["extracted_data"].get("invoice_number")
        if invoice_number:
            pdf_path = Path(f"data/processed/{invoice_number}.pdf")
            pdf_path.parent.mkdir(exist_ok=True)
            shutil.copy2(temp_path, pdf_path)  # Copy instead of move to preserve original
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
        for i, inv in enumerate(invoices):
            if inv.get("invoice_number") == invoice_number:
                invoices[i].update(update_data)
                with open(OUTPUT_FILE, "w") as f:
                    json.dump(invoices, f, indent=4)
                logger.info(f"Updated invoice {invoice_number}")
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
                invoice_number = result["extracted_data"].get("invoice_number")
                if invoice_number:
                    pdf_path = Path(f"data/processed/{invoice_number}.pdf")
                    pdf_path.parent.mkdir(exist_ok=True)
                    shutil.copy2(file, pdf_path)  # Copy instead of move to preserve original
                    logger.info(f"Saved PDF for invoice {invoice_number}")
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
    pdf_path = Path(f"data/processed/{invoice_number}.pdf")
    if pdf_path.exists():
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{invoice_number}.pdf")
    raise HTTPException(status_code=404, detail="PDF not found")