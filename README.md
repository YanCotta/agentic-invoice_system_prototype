# 📊 Brim Invoice Processing System

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-FF4B4B.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.16-33CC33.svg)](https://langchain.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT4-412991.svg)](https://openai.com/)

*An intelligent invoice processing system leveraging LangChain's multi-agent workflow*

[Overview](#-overview) •
[Features](#-key-features) •
[Development Journey](#-development-journey) •
[Architecture](#-architecture) •
[Setup Guide](#-setup-guide) •
[Usage](#-usage-guide) •
[Progress](#-project-progress)

</div>

## 🎯 Overview

A sophisticated invoice processing system that leverages LangChain's multi-agent workflow to automate extraction, validation, and purchase order (PO) matching. Built as a technical challenge response, this solution aims to reduce manual processing time by 75% while maintaining high accuracy through intelligent error handling and human-in-the-loop review processes.

## 📋 Key Features

- **Intelligent Processing Pipeline**
  - Processes PDFs from:
    - `data/raw/invoices/` (35 invoices)
    - `data/raw/test_samples/` (3 PDFs)
  - Multi-agent system for extraction, validation, and matching
  - RAG-based error handling with FAISS
  - Asynchronous processing with robust error management

- **User-Friendly Interface**
  - Streamlit-powered dashboard
  - Real-time processing updates
  - Interactive invoice review system
  - Performance metrics visualization

- **Enterprise-Ready Architecture**
  - FastAPI backend infrastructure
  - Structured logging and monitoring
  - Comprehensive test coverage
  - Deployment-ready configuration

## 🏗️ Architecture

### Project Structure
```
brim_invoice_streamlit/
├── Dockerfile
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
├── agents/
│   ├── __init__.py
│   ├── base_agent.py
│   ├── extractor_agent.py
│   ├── fallback_agent.py
│   ├── human_review_agent.py
│   ├── matching_agent.py
│   └── validator_agent.py
├── api/
│   ├── __init__.py
│   ├── app.py
│   └── review_api.py
├── config/
│   ├── __init__.py
│   ├── logging_config.py
│   ├── monitoring.py
│   ├── settings.py
│   └── __pycache__/
│       └── … (compiled files)
├── data/
│   ├── processed/
│   │   └── anomalies.json
│   │   └── structured_invoices.json
│   ├── raw/
│   │   └── invoices/ *pdfs
│   │   └── vendor_data.csv
│   ├── temp/
│   │   └── … (temporary files)
│   └── test_samples/
│       └── … (sample faulty invoices for rag_helper.py)
├── data_processing/
│   ├── __init__.py
│   ├── anomaly_detection.py
│   ├── confidence_scoring.py
│   ├── document_parser.py
│   ├── ocr_helper.py
│   ├── po_matcher.py
│   ├── rag_helper.py
│   └── __pycache__/
│       └── … (compiled files)
├── frontend/
│   └── app.py
├── models/
│   ├── __init__.py
│   ├── invoice.py
│   ├── validation_schema.py
│   └── __pycache__/
│       └── … (compiled files)
└── workflows/
    ├── __init__.py
    ├── orchestrator.py
    └── __pycache__/
        └── … (compiled files)

```

### Architecture Diagram
```
+-------------------+       +-------------------+
|   Streamlit UI    |       |    Next.js UI     |
| (Python-based)    |       | (Production-ready)|
| - Streamlit       |       | - React, Next.js  |
|   Dashboard       |       | - Tailwind CSS    |
+-------------------+       +-------------------+
           |                         |
           +-----------+-------------+
                       |
                +------+------+
                | FastAPI     |
                | Backend     |
                | - WebSocket |
                |   Support   |
                +------+------+
                       |
           +-----------+-------------+
           |                         |
+-------------------+       +-------------------+
|   Extraction      |       |   Validation      |
|   Agent           |       |   Agent           |
| - gpt-4o-mini     |       | - Pydantic Models |
| - pdfplumber      |       |                   |
| - pytesseract     |       +-------------------+
+-------------------+                |
           |                         |
           +-----------+-------------+
                       |
                +------+------+
                | PO Matching |
                |    Agent    |
                | - Fuzzy      |
                |   Matching   |
                +------+------+
                       |
                +------+------+
                | Human Review|
                |    Agent    |
                | - Confidence|
                |   < 0.9     |
                +------+------+
                       |
                +------+------+
                | Fallback    |
                |    Agent    |
                | - FAISS RAG  |
                +------+------+
                       |
                +------+------+
                | Data Storage|
                | - structured|
                |   _invoices |
                | - anomalies  |
                +------+------+
```

```mermaid
flowchart TD
    subgraph "Streamlit Frontend [Port: 8501]"
        A1[Upload PDF<br>Single or Batch] --> A2[Real-Time Progress<br>via WebSockets]
        A2 --> A3[Invoices Table<br>Vendor, Date, Total]
        A3 --> A4[Review Panel<br>Edit Flagged Data]
        A4 --> A5[Metrics Dashboard<br>Times, Error Rates]
    end

    subgraph "FastAPI Backend [Port: 8000]"
        B1[API Endpoints<br>/upload, /invoices, /update] --> B2[WebSocket<br>/ws/process_progress]
        B2 --> B3[Orchestrator<br>Coordinates Agents]
    end

    subgraph "Multi-Agent Workflow [LangChain]"
        C1[Extraction Agent<br>gpt-4o-mini, pdfplumber] --> C2[Validation Agent<br>Pydantic, Anomalies]
        C2 --> C3[PO Matching Agent<br>Fuzzy Matching, FAISS]
        C3 --> C4{Human Review<br>Confidence < 0.9?}
        C4 -->|Yes| C5[Human Review Agent<br>Manual Correction]
        C4 -->|No| C6[Processed Output]
        C5 --> C6
    end

    subgraph "Data Processing & Storage"
        D1[RAG Helper<br>Error Classification] --> C3
        D2[Raw PDFs<br>data/raw/invoices/] --> C1
        C6 --> D3[Structured JSON<br>structured_invoices.json]
        C3 --> D4[Vendor Data<br>vendor_data.csv]
        C6 --> D5[Logs & Metrics<br>monitoring.py]
    end

    %% Connections
    A1 --> B1
    A2 --> B2
    A3 --> B1
    A4 --> B1
    A5 --> B1
    B3 --> C1
    D1 --> C5
    D5 --> A5

    %% Styling
    classDef frontend fill:#FF4B4B33,stroke:#FF4B4B;
    classDef backend fill:#00968833,stroke:#009688;
    classDef agents fill:#33CC3333,stroke:#33CC33;
    classDef data fill:#41299133,stroke:#412991;
    class A1,A2,A3,A4,A5 frontend;
    class B1,B2,B3 backend;
    class C1,C2,C3,C4,C5,C6 agents;
    class D1,D2,D3,D4,D5 data;
```

## 📅 Development Journey

### Week 1: Core Development

#### Day 1: Project Foundation
- 🎯 **Objectives Achieved**
  - Created detailed 10-day roadmap
  - Analyzed technical requirements
  - Established project structure
  
- 🔧 **Technical Setup**
  - Initialized repository
  - Installed core dependencies:
    - LangChain (0.2.16)
    - PDF processing tools
    - OCR capabilities

  - Reserved AI tools:
    - GPT-o3-mini
    - Claude 3.5 Sonnet / 3.7 Sonnet Thinking
    - GitHub Copilot
    - Grok3

#### Day 2: Extraction & Validation
- 🎯 **Objectives Achieved**
  - Built extraction pipeline
  - Implemented validation system
  
- 🛠️ **Components Developed**
  1. **PDF Processing Pipeline**
     - Document parsing with pdfplumber
     - OCR processing with pytesseract
     - Data model implementation
  
  2. **Extraction Agent**
     - LangChain 0.2.16 integration
     - Mistral 7B implementation
     - JSON output formatting
  
  3. **Validation System**
     - Field validation
     - Anomaly detection
     - Format consistency checks

#### Day 3: Advanced Features
- 🎯 **Objectives Achieved**
  - Enhanced error handling
  - Improved extraction accuracy
  
- 🔨 **Technical Implementation**
  - Integrated FAISS-based RAG
  - Added performance monitoring
  - Implemented fallback mechanisms
  - Enhanced logging system

#### Day 4: System Integration
- 🎯 **Objectives Achieved**
  - Completed core functionality
  - Implemented frontend
  
- 🛠️ **Features Added**
  - PO matching system
  - Human review interface
  - Processing pipeline
  - Streamlit dashboard

#### Day 5: System Refinement
- 🎯 **Objectives Achieved**
  - Fixed critical issues
  - Enhanced reliability
  - Achieved fully functional state
  
- 🔧 **Technical Fixes**
  1. **Pipeline Timing**
     - Issue: Inaccurate processing times
     - Solution: Enhanced monitoring system
  
  2. **Confidence Scoring**
     - Issue: Incorrect confidence calculations
     - Solution: Improved scoring algorithm
  
  3. **File Management**
     - Issue: PDF handling inefficiencies
     - Solution: Optimized storage system
  
  4. **Data Formatting**
     - Issue: Inconsistent data formats
     - Solution: Standardized processing

#### Day 6: Project Refinement and Stabilization
- 🎯 **Objectives Achieved**
  - Streamlined codebase by removing redundant files
  - Fixed backend startup issues
- Enhanced API reliability
  
- 🔧 **Technical Improvements**
  1. **Backend Optimization**
    - Merged review functionality into unified API
    - Updated uvicorn startup configuration
    - Simplified routing structure
  
  2. **Code Cleanup**
    - Removed redundant `api/human_review_api.py`
    - Consolidated workflow logic in `orchestrator.py`
    - Updated all API references to use port 8000

- 🎯 **Dockerization Complete**
  - Fully Dockerized the Streamlit version with a multi-service setup (FastAPI backend and Streamlit frontend)
  - Utilized a single `Dockerfile` for both services, orchestrated with `docker-compose.yml`
  - Fixed healthcheck issue by adding `curl` to the `Dockerfile` for the `/api/invoices` endpoint check
  - Confirmed all core features (single/batch invoice processing, review, metrics) work in the Dockerized environment
  
- 🔧 **Technical Implementation**
  - Created `Dockerfile` with `python:3.12-slim`, `tesseract-ocr`, and `curl`
  - Set up `docker-compose.yml` with separate `backend` and `streamlit` services
  - Added healthcheck with 30s `start_period` to ensure backend readiness
  - Successfully tested all functionalities in a containerized setup

  
- 🚨 **Problems Encountered**
  - The 'View PDF' button may return 404 errors for batch-processed invoices due to filename mismatches in `data/raw/invoices/`
  - Status: Workaround implemented using metadata from JSON files

## 🔧 Setup Guide (Dockerized)

### Prerequisites
- Docker
- Docker Compose
- Git
- OpenAI API key
- Sample data files

### Setup Guide (Dockerized)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/brim_invoice_streamlit.git
   cd brim_invoice_streamlit

2. **Create Environment File**
   ```bash
   echo "OPENAI_API_KEY=your_api_key_here" > .env
   ```

3. **Verify Sample Data**
   - Confirm presence of:
    - PDFs in `data/raw/invoices/` (e.g., sample invoices)
    - Test files in `data/raw/test_samples/` (e.g., faulty invoices for RAG)
    - `data/raw/vendor_data.csv`
   - If missing, add sample PDFs and CSV as needed.

4. **Build and Run**
   ```bash
   docker compose up --build -d
   ```
   Note: curl is required in the container for the healthcheck to function.

5. **System Access**
   - Frontend: http://localhost:8501
   - API Endpoint: http://localhost:8000

6. **Optional: Use pre-built Docker images:**
Pull the images from Docker Hub:
```bash
docker pull yancotta/brim_invoice_streamlit_backend:latest
docker pull yancotta/brim_invoice_streamlit_streamlit:latest
```
Edit docker-compose.yml to use these images instead of building locally (replace the build sections with image: yancotta/brim_invoice_streamlit_backend:latest, etc.).

## 🚀 Usage Guide

### Core Workflows

1. **Invoice Processing**
   - Upload PDFs through the Streamlit interface
   - Monitor processing status
   - View extraction results

2. **Results Management**
   - View processed invoices on the "Invoices" page
   - Review flagged items on the "Review" page
   - Track performance metrics on the "Metrics" page

3. **Review Process**
   - Edit flagged invoices
   - Submit corrections
   - Verify changes

### Processing Logic
- **Duplicate Detection**: Automatic flagging by invoice_number
- **Confidence Thresholds**: ≥0.9 for auto-processing, <0.9 requires human review
- **Processing Mode**: Asynchronous execution
- **Data Persistence**: Full metrics and logging

### Core Workflows

1. **Invoice Processing**
   - Upload PDFs through Streamlit interface
   - Monitor processing status
   - View extraction results

2. **Results Management**
   - View processed invoices
   - Review flagged items
   - Track performance metrics

3. **Review Process**
   - Edit flagged invoices
   - Submit corrections
   - Verify changes


## 📈 Project Progress

### Completed (Days 1-7)
- ✅ Multi-agent system implementation
- ✅ Streamlit frontend development
- ✅ OpenAI API integration
- ✅ RAG-based error handling
- ✅ System optimizations
- ✅ Backend stabilization and cleanup
- ✅ Final stabilization and frontend improvements
- ✅ Dockerized and implemented CI/CD
- ✅ Finished documentation and testing

## 🔮 Future Enhancement: Database-Backed Invoice Management

### Context
The current Streamlit system uses a file-based approach (`data/raw/invoices/`) for simplicity within the 10-day challenge. However, with 5,000 monthly invoices, a scalable database solution was considered to improve manageability and usability.

### Proposed Solution

#### Architecture Components
1. **Database Layer**
   - PostgreSQL for structured metadata storage
     - Invoice numbers, vendors, dates, totals
     - Processing status and validation results
     - File references and timestamps
   - Alternative: MongoDB for flexible document storage

2. **Object Storage**
   - AWS S3 or local file server for PDF storage
   - Secure, scalable document management
   - Built-in versioning and backup capabilities

#### Implementation Steps
1. **Database Setup** (2 days)
   ```sql
   CREATE TABLE invoices (
       id SERIAL PRIMARY KEY,
       invoice_number VARCHAR(50) UNIQUE,
       vendor_name VARCHAR(100),
       issue_date DATE,
       total_amount DECIMAL(10,2),
       status VARCHAR(20),
       confidence_score FLOAT,
       pdf_url VARCHAR(255),
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

2. **Storage Configuration** (1 day)
   - S3 bucket setup with appropriate permissions
   - Folder structure for invoice PDFs
   - Backup and retention policies

3. **Application Updates** (1-2 days)
   - Modify `app.py` for database operations
   - Implement PDF storage and retrieval
   - Update processing pipeline for new architecture

4. **Frontend Enhancements**
   - Add advanced search capabilities
   - Implement filtering and sorting
   - Enable bulk operations
   - Improve PDF preview and download

### Benefits
- 📈 Scalability for thousands of invoices
- 🔍 Enhanced search and filtering
- 🔒 Improved security and access control
- 📊 Better reporting capabilities
- 🔄 Reliable backup and recovery

### Why Not Implemented
Time constraints within the 10-day challenge prioritized delivering a functional system. The modular design allows future database integration without significant refactoring.

### Implementation Roadmap
1. **Phase 1**: Database Integration
   - Set up PostgreSQL
   - Migrate existing data
   - Update core processing logic

2. **Phase 2**: Storage Migration
   - Configure S3 storage
   - Move PDFs to new storage
   - Update file handling logic

3. **Phase 3**: Frontend Enhancement
   - Add database-driven features
   - Implement advanced search
   - Enhance user experience

Estimated Timeline: 4-5 days for full implementation

### Remaining Tasks
#### Day 7-10
- Refine Documentation and Video Demo
- Delivery

### Recent Improvements
- 🆕 Enhanced file management
- 🆕 Improved error handling
- 🆕 Standardized currency handling
- 🆕 Optimized processing pipeline
- 🆕 Fixed backend startup by updating uvicorn configuration
- 🆕 Streamlined API structure

### Known Issues
- ⚠️ Metrics Page
  - Issue: TypeError in DataFrame display
  - Status: Fix in progress
  - Workaround: Default to 0.0 for null values

---

<div align="center">

**Built with ❤️ for the Technical Challenge**

</div>