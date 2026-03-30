import streamlit as st
import base64
from helper_function import get_structured_data, get_structured_data_text
from prompt import Prompt_LC, Prompt_invoice, prompt_BiBiNi, Prompt_additional_condition, prompt_bol
from extract2 import LCData, InvoiceData, DocClassify, DocumentRequirements, bol_manual, BillOfLadingData, BatchResponse
from SendingPdf import classify_doc, process_all_document
import json
from compare import compare_lc_and_invoice, df_result
import pandas as pd
from Contact_database import engine, Contact
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()



# In your main.py Streamlit app
st.sidebar.header("Request Pilot Access")
with st.sidebar.form("contact_form"):
    name = st.text_input("Your Name / Company")
    phone = st.text_input("WhatsApp Number")
    message = st.text_area("What feature do you need?")
    submitted = st.form_submit_button("Submit")
    
    if submitted and phone:
        session = Session()
        new_contact = Contact(name=name, phone=phone, message=message)
        session.add(new_contact)
        session.commit()
        session.close()
        st.success("Thank you! We'll contact you on WhatsApp.")


st.write("# TradingDocs Validator")

# --- INITIALIZE SESSION STATE ---
# This acts as the "brain" so the app doesn't forget your results
if "result" not in st.session_state:
    st.session_state.result = None


st.title('Upload your Documents')
uploaded_files = st.file_uploader("Upload Important trade documents [LC, Invoice, BOL, PL, Bi. Bi. Ni]" , accept_multiple_files=True)

# --- ACTION BUTTON ---

batch_result = None

if st.button("Categorize Document"):
    with st.spinner("Identifying documents.. "):
        batch_result = process_all_document(uploaded_files, BatchResponse)

        for doc in batch_result.documents:
            if doc.doc_type == "LC":
                st.session_state.lc_data = doc.lc_data
            elif doc.doc_type == "Invoice":
                st.session_state.invoice_data = doc.invoice_data
    

        if st.session_state.lc_data and st.session_state.invoice_data:
                add_condition = get_structured_data_text(
                    prompt=Prompt_additional_condition, 
                    text=st.session_state.lc_data.additional_conditions, 
                    schema=DocumentRequirements
                )
    #             # Save the final result to memory
                st.session_state.result = compare_lc_and_invoice(st.session_state.lc_data, st.session_state.invoice_data, add_condition)
        else:
            st.error("Failed to extract structured data. Check document quality.")


st.write("---")

st.session_state.batch_result = batch_result

if st.session_state.batch_result:
    st.write("### Identified Documents:")
    col3, col4 = st.columns(2)

    col3.header('Filename')
    col4.header('Document Type')

    for i in range(len(batch_result.documents)):
        col3.text(batch_result.documents[i].filename)
        col4.text(batch_result.documents[i].doc_type)

if st.session_state.result:
    result = st.session_state.result
    st.write("---")
    st.write("### Discrepancy Report")

    if result.get("Discrepancy"):
        df = pd.DataFrame(result["Discrepancy"])
        # Insert at index 0 so it's the first thing users see
        if 'Ignore' not in df.columns:
            df.insert(len(df.columns), 'Ignore', False)

        # Using a unique key ensures the state is tracked correctly
        edited_df = st.data_editor(
            df,
            column_config={
                "Ignore": st.column_config.CheckboxColumn("Ignore?", default=False),
                "severity": st.column_config.TextColumn("Severity Level"),
            },
            disabled=["field", "severity", "message"],
            hide_index=True,
            key="discrepancy_table" 
        )

        # Calculate Ignored Logic
        ignored_count = edited_df[edited_df["Ignore"] == True].shape[0]
        if ignored_count > 0:
            st.info(f" You have ignored {ignored_count} discrepancy(ies).")

            active_discrepancies = edited_df[edited_df["Ignore"] == False]

            st.write('### Active Discrepancies')
            st.write(active_discrepancies)

            scor = df_result(active_discrepancies)
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Re-calculated Score", f"{scor['Score']}/100")
            with col2:
                status_color = "green" if scor['Status'].strip() == "PASS" else "red"

                st.markdown(f"**Status:** :{status_color}[{scor['Status']}]")
                
        else:
            # Final Summary Card
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Raw Score", f"{result['Score']}/100")
            with col2:
                status_color = "green" if result['Status'].strip() == "PASS" else "red"
                st.markdown(f"**Status:** :{status_color}[{result['Status']}]")

    else:
        st.success("No discrepancies found! Documents match perfectly.")