# 📊 Brim Invoice Processing System

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Latest-FF4B4B.svg)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.16-33CC33.svg)](https://langchain.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT4-412991.svg)](https://openai.com/)

*An intelligent invoice prototype/small scale processing system leveraging LangChain's multi-agent workflow*

[Overview](#-overview) •
[Features](#-key-features) •
[Development Journey](#-development-journey) •
[Architecture](#-architecture) •
[Setup Guide](#-setup-guide) •
[Usage](#-usage-guide) •
[Progress](#-project-progress)

</div>

## Overview

This sophisticated invoice processing system, initially developed as a prototype for Brim’s Agentic AI Engineer technical challenge, leverages LangChain’s multi-agent workflow to automate extraction, validation, and purchase order (PO) matching. Designed to reduce manual processing time by over 75%, it ensures high accuracy through intelligent error handling and human-in-the-loop review processes. A standout feature is the implementation of Retrieval-Augmented Classification (RAC)—an adaptation of RAG—using FAISS with data/raw/test_samples/ (5 faulty PDFs) to minimize human intervention by classifying and resolving common errors autonomously.
The project evolved in phases:
Prototype (Streamlit Version): A lightweight, Streamlit-based solution for small-scale local enterprises, relying on local JSON storage (structured_invoices.json) for quick deployment and testing.

Next.js Version: A robust iteration with a modern Next.js frontend, enhancing the UI with real-time WebSocket updates and maintaining JSON storage for simplicity.

Scalable Version (feature/database-integration Branch): The current, production-ready state, integrating SQLite (invoices.db) for efficient metadata management and AWS S3 for scalable PDF storage. While PostgreSQL was considered for larger-scale needs (e.g., 5,000+ invoices/month), SQLite was chosen as sufficient for the target volume of 5,000 invoices/month.

This staged approach—starting small, iterating to a functional Next.js system, and scaling with cloud and database technologies—demonstrates a practical path from prototype to enterprise-ready solution.


## 📋 Key Features

- **Intelligent Processing Pipeline**
  - Processes PDFs from:
    - `data/raw/invoices/` (35 invoices)
  - Multi-agent system for extraction, validation, and matching
  - RAG-based error handling with FAISS `data/raw/test_samples/` -> (5 faulty PDFs examples to reduce the need for human review)
  - Asynchronous processing with robust error management

- **User-Friendly Interface**
  - Streamlit-powered dashboard
  - Real-time processing updates
  - Interactive invoice review system
  - Performance metrics visualization (one problem encountered and not solved mentioned below)

- **Enterprise-Ready Architecture**
  - FastAPI backend infrastructure
  - Structured logging and monitoring
  - Comprehensive test coverage (CI/CD)
  - Deployment-ready configuration
  - Dockerized and with images ready in DockerHub

## 🏗️ Architecture

### Project Structure

```plaintext
brim_invoice_streamlit/
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
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
│   
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
│       
├── frontend/
│   └── app.py
├── models/
│   ├── __init__.py
│   ├── invoice.py
│   ├── validation_schema.py
│   
└── workflows/
    ├── __init__.py
    ├── orchestrator.py
    

```

### Architecture Diagram - This diagram represents the Streamlit version’s architecture (shared backend with the Next.js variant, differing only in frontend)

```plaintext
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
    - others..

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

#### Day 6: More Project Refinement and Stabilization

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

#### Day 7: Comprehensive Testing & Documentation Refinement

- 🎯 **Objectives Achieved**
  - Comprehensive manual tests
  - CI/CDing
  - Refinement of documentations
  - Creation of demo video

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
   ```

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
   - Frontend: <http://localhost:8501>
   - API Endpoint: <http://localhost:8000>

6. **Optional: Use pre-built Docker images:**

Pull the images from Docker Hub:

```bash
docker pull yancotta/brim_invoice_streamlit_backend:latest
docker pull yancotta/brim_invoice_streamlit_streamlit:latest
```

Edit docker-compose.yml to use these images instead of building locally (replace the build sections with image: yancotta/brim_invoice_streamlit_backend:latest, etc.).

## 🚀 Usage Guide

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

## Known Issue: Processing Times Displaying as 0.00 Seconds

**Problem Encountered**: During testing on February 25, 2025, I noticed that all processing times (extraction, validation, matching, review, and total time) displayed as 0.00 seconds on both the Invoices and Metrics pages of the Streamlit frontend. This persisted across multiple invoices, despite other functionalities—such as invoice extraction, validation, matching, review, and confidence scoring—working correctly.

**Troubleshooting Efforts**: I investigated the timing capture logic in `workflows/orchestrator.py` and `config/monitoring.py`. Initially, the `Monitoring.timer` context manager yielded no value, causing timing variables (e.g., `extraction_time`) to remain `None` and default to 0.0. I introduced a `TimerContext` class to capture durations via `__exit__`, and updated `process_invoice` to use `timer.duration`. However, this didn’t resolve the issue because the assignments were incorrectly placed inside the `with` blocks, capturing `0.0` before the duration was set.

A subsequent fix moved these assignments outside the `with` blocks to capture the actual durations post-execution. While this approach was sound in theory, applying it inadvertently broke the system due to an indentation error: the `process_invoice` method was not properly nested under the `InvoiceProcessingWorkflow` class. This led to `AttributeError` exceptions when the backend attempted to call `workflow.process_invoice`, resulting in 500 Internal Server Errors and a non-functional system.

**Current Status**: Despite multiple attempts to correct the timing capture—including verifying the `TimerContext` implementation and adjusting indentation—the system ceased functioning after the latest fix. Logs indicate successful agent initialization and test sample processing, but the frontend reports "Failed to connect to the server," and invoice uploads fail. Due to time constraints within the 10-day technical challenge, I’ve decided to revert to the previous working version, where all core functionalities operate correctly except for the timing metrics.

**Resolution**: For now, the processing times remain broken, displaying 0.00 seconds. This does not impact the system’s primary invoice processing capabilities, but it limits performance monitoring accuracy. A future fix would involve correctly indenting the `process_invoice` method under the class, ensuring atomic file writes to prevent JSON corruption (noted in logs as "JSON decode error"), and re-testing the timing capture logic. Given the project timeline, I’ve prioritized a fully functional system over perfecting this metric.

**Next Steps**: Post-submission, I’d address this by isolating the timing logic in a separate test harness, ensuring proper class method scoping, and implementing robust file handling to avoid concurrency issues.

---

<div align="center">

**Built with ❤️ for Brim's Technical Challenge**

</div>
