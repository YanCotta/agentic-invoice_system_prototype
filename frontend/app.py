import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

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
            response = requests.post(f"{API_URL}/api/upload_invoice", files={"file": uploaded_file})
            if response.status_code == 200:
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
            else:
                st.error(f"Error: {response.text}")

elif page == "Invoices":
    st.header("Processed Invoices")
    if st.button("Refresh"):
        with st.spinner("Loading invoices..."):
            response = requests.get(f"{API_URL}/api/invoices")
            if response.status_code == 200:
                invoices = response.json()
                if invoices:
                    df = pd.DataFrame(invoices)
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
        flagged = [inv for inv in invoices if float(inv.get("confidence", 1.0)) < 0.9 or inv.get("validation_status") != "valid"]
        for i, inv in enumerate(flagged):
            with st.expander(f"Invoice {inv['invoice_number']} (Confidence: {inv['confidence']:.2f})"):
                vendor_key = f"vendor_{inv['invoice_number']}_{i}"
                total_key = f"total_{inv['invoice_number']}_{i}"
                vendor = st.text_input("Vendor Name", inv["vendor_name"], key=vendor_key)
                total = st.number_input("Total Amount", float(inv["total_amount"]), key=total_key)
                if st.button("Save Corrections", key=f"save_{inv['invoice_number']}_{i}"):
                    # Add your save logic here, e.g., send updated data to the API
                    st.success(f"Corrections saved for {inv['invoice_number']}")
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