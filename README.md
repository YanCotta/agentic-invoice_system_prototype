# 📊 Brim Invoice Processing System

## 🎯 Overview
An intelligent invoice processing system leveraging LangChain's multi-agent workflow to automate extraction, validation, and purchase order (PO) matching. Built for the "Technical Challenge: Intelligent Invoice Processing with LangChain Multi-Agent Workflow" to reduce manual processing time by 75% and minimize errors.

## 📋 Key Features
- Processes PDFs from:
  - `data/raw/invoices/` (35 invoices)
  - `data/raw/test_samples/` (3 PDFs)
- Integrates multiple agents for extraction, validation, matching, human review, and fallback procedures
- Implements RAG-based error handling and performance monitoring
- Utilizes async processing with robust error handling, structured logging, and retries

---

## 📅 Development Timeline

### Day 1: Project Planning and Setup
#### 🎯 Goal
Establish a solid foundation for the 10-day development process.

#### 🔨 Activities
- Organized a detailed 10-day workflow
- Analyzed "Technical Challenge" requirements
- Reserved AI tools:
  - GPT-o3-mini 
  - Claude 3.5 Sonnet
  - GitHub Copilot 
  - Grok3


- Defined project structure:

```python 
/brim_invoice_project
├── agents/
│   ├── base_agent.py             # Base agent class for shared functionality
│   ├── extractor_agent.py        # Extracts data from invoices using OpenAI GPT-4o-mini
│   ├── validator_agent.py        # Validates fields and detects anomalies
│   ├── matching_agent.py         # Matches POs using fuzzy logic
│   ├── human_review_agent.py     # Routes flagged invoices for manual review
│   └── fallback_agent.py         # Regex-based backup extraction
│
├── api/
│   ├── app.py                    # Main FastAPI backend with upload and invoice retrieval endpoints
│   ├── human_review_api.py       # FastAPI endpoints for human review (wrapper around review_api.py)
│   └── review_api.py             # Core review API logic for manual corrections
│
├── config/
│   ├── settings.py               # API keys, paths, configs
│   ├── logging_config.py         # Structured JSON logging setup
│   └── monitoring.py             # Performance tracking for agent workflows
│
├── data/
│   ├── raw/
│   │   ├── invoices/             # 35 raw invoice PDFs
│   │   ├── test_samples/         # 5 test-case PDFs for RAG (e.g., invoice_standard_example.pdf)
│   │   └── vendor_data.csv       # PO reference data
│   ├── processed/
│   │   ├── structured_invoices.json  # Processed invoice results
│   │   └── corrections.json      # Human review corrections
│   └── temp/                     # Temporary directory for uploaded PDFs
│
├── data_processing/
│   ├── document_parser.py        # PDF parsing logic
│   ├── ocr_helper.py             # Pytesseract wrapper for OCR
│   ├── anomaly_detection.py      # Flags outliers and duplicates
│   ├── confidence_scoring.py     # Computes extraction confidence
│   └── rag_helper.py             # FAISS-based RAG for error detection
│
├── models/
│   ├── invoice.py                # Pydantic model for invoice data
│   └── validation_schema.py      # Pydantic schema for data validation
│
├── workflows/
│   └── orchestrator.py           # Orchestrates the multi-agent pipeline
│
├── frontend/
│   └── app.py                    # Streamlit frontend for upload, table, and review
│
├── tests/
│   ├── test_agents.py            # Unit tests for agents
│   └── test_workflows.py         # Integration tests for workflows
│
├── requirements.txt              # Project dependencies
├── README.md                     # Project documentation
└── architecture_diagram.png      # System architecture diagram
```

#### 🏁 Outcome
- Initialized GitHub repository
- Installed dependencies:
  - `langchain==0.2.16`
  - `pdfplumber`
  - `pytesseract`
- Cloned dataset
- Prepared for extraction agent development

---

### Day 2: Invoice Extraction Agent
#### 🔧 Implementation Details
- **InvoiceExtractionAgent** (`agents/extractor_agent.py`):
  - Utilizes LangChain 0.2.16 with Mistral 7B (Ollama)
  - Extracts structured data from PDFs

#### 🛠️ Components
1. **PDF Parsing & OCR**
   - `data_processing/document_parser.py` (pdfplumber)
   - `data_processing/ocr_helper.py` (pytesseract)

2. **Data Models**
   - `InvoiceData` model built with Pydantic v2
   - Supports required and optional fields with Decimal precision

3. **Processing Features**
   - Confidence scoring
   - JSON logging
   - Error handling with fallback mechanisms

#### 📊 Sample Output
```json
{
  "vendor_name": "ABC Corp Ltd.",
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-02-18",
  "total_amount": "7595.00",
  "confidence": 0.955
}
```

#### Invoice Validation & Extraction Refinement
- **InvoiceValidationAgent** (`agents/validator_agent.py`):
  - Validates extracted data for missing fields and format inconsistencies
  - Adds anomaly detection for duplicates and outliers
  - Orchestrates extraction and validation workflows

**Improvements:**
- Enhanced error handling using try-except blocks
- Processed PDFs from multiple subdirectories
- Introduced Pydantic v2 validation models

#### 📊 Sample Output
```json
{
  "extracted_data": { ... },
  "validation_result": { "status": "valid", "errors": {} }
}
```

#### PO Matching & Multi-Agent Coordination
- **PurchaseOrderMatchingAgent**:
  - Implements fuzzy matching for purchase order validation
  - Integrates full pipeline orchestration
  - Resolves CSV column mismatches
  - Provides comprehensive logging

#### 📊 Sample Output
```json
{
  "extracted_data": { ... },
  "validation_result": { "status": "valid", "errors": {} },
  "matching_result": { "status": "unmatched", "po_number": null, "match_confidence": 0.0 }
}
```

#### Error Handling, Edge Cases & Human-in-the-Loop
- Added async processing with retry mechanisms
- **Human Review API** implemented in `api/review_api.py` using FastAPI to allow manual corrections via a “veteran reviewer” prompt
- Optimized logging configuration and enhanced async compatibility

**Improvements:**
- Fixed asyncio dependencies
- Adjusted extraction prompts
- Enhanced error handling

#### 📊 Sample Output
```json
{
  "extracted_data": {
    "vendor_name": "ABC Corp Ltd.",
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-02-18",
    "total_amount": "7595.00",
    "confidence": 0.955,
    "po_number": null,
    "tax_amount": null,
    "currency": null
  },
  "validation_result": {
    "status": "valid",
    "errors": {} 
  },
  "matching_result": {
    "status": "unmatched",
    "po_number": null,
    "match_confidence": 0.0
  },
  "review_result": {
    "status": "approved",
    "invoice_data": { ... }
  }
}
```

Additional Enhancements:
- Updated LLM prompt in `agents/extractor_agent.py` to enforce JSON-only output, improving parsing reliability
- Integrated FAISS-based RAG module in `data_processing/rag_helper.py` to store error invoices and classify new ones, reducing the need for human intervention
- Maintained verbose logging for effective debugging and performance tracking

---

### Day 3: Advanced Error Handling, RAG Integration, and Extraction Refinement

#### 🎯 Goals
- Enhance error handling using RAG to preemptively address edge cases
- Refine the extraction agent for consistent and reliable output
- Introduce performance monitoring to track pipeline efficiency

#### 🔨 Activities
- **Terminal Analysis:**
  - Ran `python workflows/orchestrator.py` and observed AgentExecutor processing
  - Noted narrative text in LLM JSON-like output causing parsing failures
  - Identified inconsistent formatting in `total_amount` (e.g., "1793.7" vs. "1793.70")

- **Extraction Agent Refinement:**
  - Updated prompt in `agents/extractor_agent.py` to enforce strict JSON-only response
  - Added post-processing with regex to clean any extraneous narrative text

- **Enhanced Error Handling with RAG:**
  - Integrated FAISS-based RAG in `data_processing/rag_helper.py` to classify invoices against known error cases
  - Updated extraction logic to log warnings if an invoice is similar to known error-prone cases

- **Fallback Mechanism:**
  - Added `agents/fallback_agent.py` implementing regex-based extraction as a backup

- **Monitoring:**
  - Developed `config/monitoring.py` to log execution times and integrate performance tracking in `workflows/orchestrator.py`
- **Data Persistence:**
  - Saved processed results in `data/processed/structured_invoices.json` for further analysis

#### 🛠️ Challenges and Solutions
- **LLM Narrative Output:**
  - Challenge: LLM output wrapping JSON in narrative text
  - Solution: Enforce JSON-only output and apply regex cleaning, with fallback extraction if necessary

- **Inconsistent Formatting:**
  - Challenge: Variations in `total_amount` formatting
  - Solution: Standardize post-processing to ensure two decimal places

#### 📊 Expected Sample Output
```json
{
  "vendor_name": "Solis Inc",
  "invoice_number": "IN_3515484",
  "invoice_date": "2025-01-30",
  "total_amount": "1793.70",
  "currency": "GBP",
  "confidence": 0.95
}
```

## Model Transition and Backend Updates

- **Initial Challenge**: We started with a local Mistral 7B model for invoice extraction but encountered inconsistent JSON output, leading to persistent parsing errors that stalled progress.
- **Switch to OpenAI API**: On Day 3, we replaced the 7B model with OpenAI’s gpt-4o-mini API using an API key (purchased $5 credits), improving reliability and eliminating local hosting needs.
- **Extractor Agent Fixes**: Updated `agents/extractor_agent.py` to use OpenAI API calls, set a default confidence score of 0.95 for successful extractions, and removed unnecessary LangChain dependencies originally used with Mistral.
- **Confidence Scoring Adjustments**: Modified `data_processing/confidence_scoring.py` to handle OpenAI’s flat JSON output, ensuring accurate confidence scores instead of defaulting to 0.0.
- **Orchestrator Enhancements**: Fixed `workflows/orchestrator.py` to serialize InvoiceData correctly (converting datetime.date and Decimal to strings), resolved indentation errors that prevented `process_invoice` execution, and ensured all invoices are processed and saved to `data/processed/structured_invoices.json`.
- **Serialization Success**: Overcame "Object of type date is not JSON serializable" errors by using an extracted_dict with string conversions, validated by successful JSON output.
- **Impact**: These changes resulted in a robust backend pipeline—extraction, validation, PO matching, and review now run end-to-end, processing multiple invoices with high accuracy and saving structured data reliably.

---

## 🔍 Overall Project Structure
- **agents/**: Contains various agents for extraction (`extractor_agent.py`), validation (`validator_agent.py`), matching (`matching_agent.py`), and fallback (`fallback_agent.py`)
- **api/**: RESTful API endpoints (e.g., `review_api.py` for human-in-the-loop review)
- **config/**: Configuration files including monitoring and logging settings
- **data/**: Raw PDFs (`data/raw/invoices/`, `data/raw/test_samples/`) and processed outputs (`data/processed/structured_invoices.json`)
- **data_processing/**: Modules for document parsing, OCR, anomaly detection, and RAG integration (`document_parser.py`, `ocr_helper.py`, `rag_helper.py`)
- **models/**: Pydantic models such as `InvoiceData`
- **workflows/**: Orchestration of the processing pipeline (`orchestrator.py`)
- **tests/**: Testing suites and placeholder for future tests

---

## ✅ Completed (Days 1–4)
- **InvoiceExtractionAgent:** Integration with Mistral 7B, strict JSON parsing, RAG integration, and fallback mechanisms
- **InvoiceValidationAgent:** Field validation with anomaly detection
- **PurchaseOrderMatchingAgent:** Fuzzy matching with vendor data and CSV fixes
- **Human Review API:** FastAPI endpoints for manual invoice corrections
- **FAISS-based RAG:** Classification of error-prone invoices
- **Async Processing & Error Handling:** Retries, structured logging, and enhanced error capture
- **Monitoring:** Execution time tracking integrated into the pipeline
- **Frontend development:** Successfully implemented the Streamlit frontend for uploading invoices, viewing processed data, and reviewing flagged cases (due to time constrains, I picked this option
instead of react/next.js)
- Integrated the frontend with the FastAPI backend, allowing seamless communication between the UI and the invoice processing system.
- Resolved issues with module imports and file paths, ensuring the system runs smoothly.
- Tested the end-to-end functionality, including uploading a PDF invoice, processing it, and reviewing the results.

### Dependency Issues
- Resolved missing modules by installing:
  - `faiss-cpu` via `pip install faiss-cpu`
  - `python-multipart` via `pip install python-multipart`

### PDF Processing Changes
- Implemented logic to keep original PDFs intact (i.e., preventing them from moving to `data/processed/` after extraction)

### Non-Invoice PDF Handling
- Added flagging for non-invoice PDFs (e.g., resumes) to trigger human review and provide user-friendly error messages to avoid KeyErrors on missing invoice fields

### Anomaly Flagging
- Ensured anomalies (e.g., unusual amounts or formats) are flagged and clearly displayed on the review page

### Currency Adjustment
- Changed the default currency from USD to GBP in `models/invoice.py` (within the Config class’s `json_schema_extra`)
- Removed other hardcoded USD references throughout the project

### Import Errors Fixes
- In `agents/extractor_agent.py`: Added missing imports using `from openai import OpenAI` and `from dotenv import load_dotenv` after installing via `pip install openai python-dotenv`
- In `agents/fallback_agent.py`: Fixed undefined functions by importing `extract_text_from_pdf` from `data_processing/document_parser` and `ocr_process_image` from `data_processing/ocr_helper`
- In `frontend/app.py`: Resolved missing imports with `import streamlit as st`, `import requests`, and `import pandas as pd` after installing via `pip install streamlit requests pandas`
- In `models/invoice.py`: Addressed missing pydantic import with `from pydantic import BaseModel` (installed via `pip install pydantic`)

#### File Management and Storage
- Successfully implemented anomaly detection for non-invoice files (e.g., resumes), storing them in `data/processed/anomalies.json` with detailed reasons
- Fixed PDF handling to keep original files in `data/raw/invoices/` while storing structured data in `data/processed/structured_invoices.json`
- Enhanced file organization to prevent accidental file movements during processing

#### Frontend Improvements
- Implemented PDF download functionality in the review tab
- Added field editing capabilities with validation
- Enhanced save changes functionality with proper error handling
- Updated currency display to show £ symbol consistently across the UI
- Added user-friendly error messages for common issues:
  - Missing required fields
  - Non-invoice document uploads
  - Processing failures
  - Connection errors

#### Currency Standardization
- Updated currency handling throughout the project to use GBP:
  - Modified `models/invoice.py` Config class to use GBP as default
  - Updated validators to enforce GBP currency validation
  - Enhanced display formatting to show £ symbol in frontend tables and forms
  - Updated extraction agent to convert amounts to GBP during processing

#### Import and Dependency Fixes
- Resolved all import-related issues across the project:
  - Added proper OpenAI API integration with environment variable handling
  - Fixed dotenv configuration for secure API key management
  - Resolved Streamlit frontend dependencies
  - Added proper error handling for missing packages

### 🚨 Known Issues and Next Steps

#### Processing Pipeline Issues
1. **Timer Anomalies**
   - Validation and matching steps reporting 0.00s processing times
   - Potential execution flow issues in the pipeline
   - Need to investigate `workflows/orchestrator.py` timing logic
   - Monitoring class may not be properly tracking async operations
   - Timer start/stop calls might be missing in some error paths

2. **Confidence Scoring Problems**
   - All invoices being flagged for review with 0.1 confidence
   - Issues with confidence calculation in `data_processing/confidence_scoring.py`
   - RAG helper integration not properly affecting confidence scores
   - Confidence scoring fails to account for successful field extractions
   - Default fallback confidence (0.1) being used instead of calculated scores

#### Debugging Approach
1. **Pipeline Timing**
   - Add detailed logging for each processing step
   - Implement timing decorators for key functions
   - Track async operation durations separately
   - Monitor event loop execution times
   - Add checkpoints for timer verification

2. **Confidence Calculation**
   - Review field extraction success rate impact
   - Validate RAG similarity scores
   - Adjust confidence thresholds based on field importance
   - Implement weighted scoring for critical fields
   - Add confidence score auditing and logging

#### Action Items
- [ ] Debug validation and matching step timing issues
- [ ] Investigate and fix confidence scoring calculation
- [ ] Enhance RAG integration for better anomaly detection
- [ ] Implement proper confidence thresholds for review flagging
- [ ] Add unit tests for timing and confidence calculations
- [ ] Add timing decorators to track async operations
- [ ] Implement confidence score auditing
- [ ] Add detailed logging for score components
- [ ] Create monitoring dashboard for timing metrics
- [ ] Develop confidence score visualization tools

---

## 🚀 Remaining Workflow (Days 5–10)

### Day 5 – Deployment & Post-Processing Analytics
- Dockerize the application
- Set up CI/CD Pipeline with GitHub Actions
- Develop an analytics dashboard for trends, anomalies, and key performance metrics

### Day 6 – Documentation & Comprehensive Testing
- Finalize and expand documentation (README, architecture diagrams, performance reports)
- Enhance test coverage with unit, integration, and edge case tests
- Code refactoring and cleanup

### Day 7 – Finalization & Submission
- Conduct full end-to-end testing on diverse invoice samples
- Optimize performance (retry logic, FAISS indexing)
- Record a demo video showcasing system workflow and performance highlights
- Prepare final submission packaging (GitHub push, deliverables, submission email)

---

## 🔧 Setup and Usage Instructions

### 📦 Prerequisites
- Python 3.12 or higher
- Virtual environment (recommended)
- Git installed
- Sample invoice PDFs and vendor data (provided in repository)

### ⚙️ Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd brim_invoice_project
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate it
   # On Linux/Mac:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```
  3. **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    sudo apt-get install libblas-dev liblapack-dev
    ```

  4. **Create Environment File**
    ```bash
    # Create .env file in project root
    echo "OPENAI_API_KEY=your-api-key-here" > .env
    
    # Replace with your actual OpenAI API key
    # Important: Never commit this file to version control
    ```

  5. **Verify Data Structure**
    - Ensure sample PDFs exist in:
      - `data/raw/invoices/` (main invoice directory)
      - `data/test_samples/` (contains `invoice_standard_example.pdf`)
    - Verify `data/raw/vendor_data.csv` is present

  ### 🚀 Running the Application
  1. **Start the Backend Services**
   Open three separate terminals and run:

   ```bash
   # Terminal 1: Main API
   python -m uvicorn api.app:app --reload --port 8000

   # Terminal 2: Human Review API
   python -m uvicorn api.human_review_api:app --reload --port 8001

   # Terminal 3: Streamlit Frontend
   streamlit run frontend/app.py
   ```

2. **Access the Application**
   - Open your browser and navigate to `http://localhost:8501`
   - The main API will be available at `http://localhost:8000`
   - The review API will be available at `http://localhost:8001`

### 🧪 Testing the System

1. **Upload and Process Invoices**
   - Navigate to the "Upload" page
   - Upload a sample PDF (e.g., `data/test_samples/invoice_standard_example.pdf`)
   - Click "Submit" to process

2. **View Results**
   - "Invoices" page: Click "Refresh" to see processed invoices
   - "Review" page: Check flagged invoices (confidence < 0.9 or validation errors)
   - "Metrics" page: View performance data (extraction times, confidence scores)

3. **Review and Correct**
   - Review flagged invoices on the "Review" page
   - Submit corrections if needed
   - Monitor reprocessing status

4. **Note on Faulty Invoice Handling**
   - The system uses RAG (Retrieval-Augmented Generation) with a vector database to handle faulty invoices
   - During processing, each invoice is compared against stored 'poor quality' examples from `data/test_samples/`
   - This allows automatic identification and correction of common errors
   - Many faulty invoices are processed with high confidence (≥0.9) without manual intervention
   - Human review is only triggered for:
     - Invoices with confidence scores below 0.9
     - Significant validation errors not resolved by RAG

### 📝 Important Notes
- Extraction timing data is included in API responses and displayed in the metrics dashboard
- Duplicate invoices (same invoice_number) are automatically flagged
- Low confidence scores (< 0.9) trigger human review
- The system processes PDFs asynchronously, so there might be a brief delay before results appear
- All processing metrics and logs are stored for analysis