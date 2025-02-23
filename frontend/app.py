import streamlit as st
import requests
import pandas as pd
from datetime import datetime  # Add datetime import

API_URL = "http://127.0.0.1:8000"

def save_updated_invoice(updated_invoice):
    response = requests.put(
        f"{API_URL}/api/invoices/{updated_invoice['invoice_number']}",
        json=updated_invoice
    )
    if response.status_code == 200:
        st.success("Invoice updated successfully!")
    else:
        st.error(f"Failed to update invoice: {response.text}")

# Set page config for a custom theme
st.set_page_config(page_title="Brim Invoice Processing", layout="wide")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload", "Invoices", "Review", "Metrics"])

if page == "Upload":
    st.header("Upload Invoice")
    uploaded_file = st.file_uploader("Choose a PDF invoice", type="pdf")
    
    # New: Process All Invoices button
    if st.button("Process All Invoices"):
        try:
            response = requests.get(f"{API_URL}/api/process_all_invoices")
            response.raise_for_status()
            st.success("Processed all invoices!")
        except requests.RequestException as e:
            st.error(f"Failed to process all invoices: {str(e)}")
    
    if uploaded_file:
        with st.spinner("Processing invoice..."):
            try:
                response = requests.post(f"{API_URL}/api/upload_invoice", files={"file": uploaded_file})
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                st.error("Failed to connect to the server. Please check if the backend is running.")
            except Exception as e:
                if "ValidationError" in str(e):
                    st.error("The uploaded document is missing required invoice fields. It has been flagged for manual review.")
                elif "KeyError" in str(e) and "confidence" in str(e):
                    st.error("The document could not be processed due to missing data. It has been flagged for manual review.")
                else:
                    st.error("An unexpected error occurred while processing the document. Please try again or contact support.")
            else:
                st.success("Invoice processed successfully!")
                result = response.json()
                st.json(result)  # Show full response
                # Display timings in a user-friendly way
                st.write("**Processing Times:**")
                st.write(f"- Extraction: {result.get('extraction_time', 0):.2f}s")
                st.write(f"- Validation: {result.get('validation_time', 0):.2f}s")
                st.write(f"- Matching: {result.get('matching_time', 0):.2f}s")
                st.write(f"- Review: {result.get('review_time', 0):.2f}s")
                st.write(f"- Total: {result.get('total_time', 0):.2f}s")

elif page == "Invoices":
    st.header("Processed Invoices")
    if st.button("Refresh"):
        with st.spinner("Loading invoices..."):
            response = requests.get(f"{API_URL}/api/invoices")
            if response.status_code == 200:
                invoices = response.json()
                if invoices:
                    df = pd.DataFrame(invoices)
                    # Add £ symbol to total_amount column if it exists
                    if 'total_amount' in df.columns:
                        df['total_amount'] = '£' + df['total_amount'].astype(str)
                    # Updated display columns to include invoice_date
                    display_cols = ["vendor_name", "invoice_number", "invoice_date", "total_amount", "confidence", "total_time"]
                    available_cols = [col for col in display_cols if col in df.columns]
                    styled_df = df[available_cols].style.applymap(
                        lambda x: 'color: green' if float(x) > 0.9 else 'color: red', subset=['confidence']
                    ).format({"total_time": "{:.2f}"})
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.info("No invoices processed yet.")
            else:
                st.error(f"Error: {response.text}")

elif page == "Review":
    st.header("Review Flagged Invoices")

    response = requests.get(f"{API_URL}/api/invoices")
    if response.status_code == 200:
        invoices = response.json()
        # Updated filter to only include invoices that need human review
        flagged = [inv for inv in invoices if inv.get("review_status") == "needs_review"]
        
        if not flagged:
            st.info("No invoices currently need review.")
        
        for index, inv in enumerate(flagged):
            with st.expander(f"Invoice {inv['invoice_number']} ({inv.get('error_message', 'Needs Review')})"):
                # Display error message if present
                if inv.get("error_message"):
                    st.error(inv["error_message"])
                
                # Display confidence score with color coding
                confidence = inv.get("confidence", 0.0)
                color = "red" if confidence < 0.5 else "orange" if confidence < 0.8 else "green"
                st.markdown(f"**Confidence Score:** <span style='color:{color}'>{confidence:.2%}</span>", unsafe_allow_html=True)
                
                # Show validation errors if present
                if inv.get("validation_errors"):
                    st.error("Validation Errors:")
                    for field, error in inv["validation_errors"].items():
                        st.write(f"- {field}: {error}")
                
                # PDF download button with unique key
                if inv.get("original_path"):
                    pdf_response = requests.get(f"{API_URL}/api/invoice_pdf/{inv['invoice_number']}")
                    if pdf_response.status_code == 200:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_response.content,
                            file_name=f"{inv['invoice_number']}.pdf",
                            mime="application/pdf",
                            key=f"download_btn_{inv['invoice_number']}_{index}"
                        )
                    else:
                        st.error("PDF not found in raw invoices directory")
                else:
                    st.warning("Original PDF path not recorded")
                
                # Edit form with unique key
                with st.form(key=f"form_{index}_{inv['invoice_number']}"):
                    vendor_name = st.text_input("Vendor Name", value=inv.get("vendor_name", ""))
                    invoice_number = st.text_input("Invoice Number", value=inv.get("invoice_number", ""))
                    invoice_date = st.date_input("Invoice Date", value=pd.to_datetime(inv.get("invoice_date")).date() if inv.get("invoice_date") else None)
                    total_amount = st.number_input("Total Amount", value=float(inv.get("total_amount", 0.0)))
                    po_number = st.text_input("PO Number", value=inv.get("po_number", ""))
                    
                    # Add review resolution options
                    resolution_status = st.selectbox(
                        "Resolution",
                        ["pending", "approved", "rejected"],
                        key=f"resolution_{index}_{inv['invoice_number']}"
                    )
                    
                    review_notes = st.text_area(
                        "Review Notes",
                        value=inv.get("review_notes", ""),
                        key=f"notes_{index}_{inv['invoice_number']}"
                    )
                    
                    submit = st.form_submit_button("Save Changes")
                    if submit:
                        updated_invoice = {
                            "vendor_name": vendor_name,
                            "invoice_number": invoice_number,
                            "invoice_date": str(invoice_date),
                            "total_amount": total_amount,
                            "po_number": po_number,
                            "review_status": resolution_status,
                            "review_notes": review_notes,
                            "review_date": datetime.now().isoformat()
                        }
                        save_updated_invoice(updated_invoice)
    else:
        st.error("Failed to fetch invoices from API")

elif page == "Metrics":
    st.header("📊 Performance Metrics")
    response = requests.get(f"{API_URL}/api/invoices")
    if response.status_code == 200:
        invoices = response.json()
        if invoices:
            df = pd.DataFrame(invoices)
            # Use .get() to provide defaults for missing fields
            avg_confidence = df.get("confidence", pd.Series([0])).mean()
            total_invoices = len(df)
            avg_time = df.get("total_time", pd.Series([0])).mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg. Confidence Score", f"{avg_confidence:.1%}")
            with col2:
                st.metric("Total Invoices", total_invoices)
            with col3:
                st.metric("Avg. Processing Time", f"{avg_time:.2f}s")
            
            # Confidence Distribution
            if "confidence" in df.columns:
                st.subheader("Confidence Score Distribution")
                st.bar_chart(df["confidence"].value_counts())
            
            # Processing Times
            st.subheader("Processing Times")
            times_df = pd.DataFrame([{
                "Invoice": inv.get("invoice_number", "Unknown"),
                "Extraction (s)": inv.get("extraction_time", 0),
                "Validation (s)": inv.get("validation_time", 0),
                "Matching (s)": inv.get("matching_time", 0),
                "Review (s)": inv.get("review_time", 0),
                "Total (s)": inv.get("total_time", 0)
            } for inv in invoices])
            st.table(times_df.style.format({
                "Extraction (s)": "{:.2f}",
                "Validation (s)": "{:.2f}",
                "Matching (s)": "{:.2f}",
                "Review (s)": "{:.2f}",
                "Total (s)": "{:.2f}"
            }))
        else:
            st.info("No invoices available yet.")
    else:
        st.error("Failed to fetch metrics from API")