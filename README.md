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
│   ├── validator_agent.py
│   └── __pycache__/
├── api/
│   ├── __init__.py
│   ├── app.py
│   ├── human_review_api.py
│   ├── review_api.py
│   └── __pycache__/
│       └── … (compiled files)
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
│   │   └── test_invoice.txt
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
├── tests/
│   ├── __init__.py
│   ├── load_tests.py
│   ├── test_agents.py
│   ├── test_endpoints.py
│   ├── test_frontend.js
│   ├── test_utils.py
│   └── test_workflows.py
└── workflows/
    ├── __init__.py
    ├── orchestrator.py
    ├── pipeline.py
    └── __pycache__/
        └── … (compiled files)

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

1. **Backend APIs**
   ```bash
   # Terminal 1: Main API
   python -m uvicorn api.app:app --reload --port 8000

   # Terminal 2: Review API
   python -m uvicorn api.human_review_api:app --reload --port 8001
   ```

2. **Frontend Application**
   ```bash
   # Terminal 3: Streamlit Interface
   streamlit run frontend/app.py
   ```

### System Access

- **Main Interface**: http://localhost:8501
- **API Endpoints**:
  - Main API: http://localhost:8000
  - Review API: http://localhost:8001

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

### Completed (Days 1-5)
- ✅ Multi-agent system implementation
- ✅ Streamlit frontend development
- ✅ OpenAI API integration
- ✅ RAG-based error handling
- ✅ System optimizations

### Remaining Tasks (Days 6-7)
- 📋 Day 6: Documentation & Testing
  - Expand documentation
  - Enhance test coverage
  - Refactor codebase

- 📋 Day 7: Finalization
  - End-to-end testing
  - Performance optimization
  - Submission preparation

### Recent Improvements
- 🆕 Enhanced file management
- 🆕 Improved error handling
- 🆕 Standardized currency handling
- 🆕 Optimized processing pipeline
- 🆕 Fixed metrics display issues

### Known Issues
- ⚠️ Metrics Page
  - Issue: TypeError in DataFrame display
  - Status: Fix in progress
  - Workaround: Default to 0.0 for null values

---

<div align="center">

**Built with ❤️ for the Technical Challenge**

</div>

