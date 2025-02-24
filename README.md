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
    - Claude 3.5 Sonnet
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

## 🔧 Setup Guide

### Prerequisites
- Python 3.12+
- Virtual environment tool
- Git
- Sample data files

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd brim_invoice_project
   ```

2. **Python Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # OR
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   sudo apt-get install libblas-dev liblapack-dev
   ```

4. **Environment Setup**
   ```bash
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```

5. **Data Verification**
   - Confirm presence of:
     - PDFs in `data/raw/invoices/`
     - Test files in `data/raw/test_samples/`
     - `data/raw/vendor_data.csv`

## 🚀 Usage Guide

### Starting Services

1. **Backend API**
   ```bash
   # Terminal 1: Main API
   python -m uvicorn api.app:app --reload --port 8000
   ```

2. **Frontend Application**
   ```bash
   # Terminal 2: Streamlit Interface
   streamlit run frontend/app.py
   ```

### System Access

- **Main Interface**: http://localhost:8501
- **API Endpoint**: http://localhost:8000

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

### Processing Logic

- **Duplicate Detection**: Automatic flagging by invoice_number
- **Confidence Thresholds**:
  - ≥0.9: Automatic processing
  - <0.9: Human review required
- **Processing Mode**: Asynchronous execution
- **Data Persistence**: Full metrics and logging

## 📈 Project Progress

### Completed (Days 1-6)
- ✅ Multi-agent system implementation
- ✅ Streamlit frontend development
- ✅ OpenAI API integration
- ✅ RAG-based error handling
- ✅ System optimizations
- ✅ Backend stabilization and cleanup
- ✅ Final stabilization and frontend improvements

#### Day 6: Final Stabilization and Frontend Fixes
- 🎯 **Objectives Achieved**
  - Enhanced batch processing stability
  - Improved frontend error handling
  - Streamlined PDF viewing functionality
  
- 🔧 **Technical Improvements**
  1. **Batch Processing**
     - Enhanced queue management for multiple files
     - Improved progress tracking and status updates
     - Added batch operation error recovery
  
  2. **Frontend Enhancements**
     - Implemented better error messaging
     - Added loading states for all operations
     - Enhanced user feedback mechanisms
  
- 🚨 **Problems Encountered**
  - The 'View PDF' button may return 404 errors for batch-processed invoices due to filename mismatches in `data/raw/invoices/`
  - Status: Workaround implemented using metadata from JSON files

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
- Dockerization
- CI/CD pipeline setup
- Documentation and Video Demo
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

