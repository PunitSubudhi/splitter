from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
from page_functions import *

with st.form("splitter"):
    file = st.file_uploader("Upload File from Sainsburys Trolley Page")
    launch_mito = st.checkbox("Launch Mito")
    submitted = st.form_submit_button("Uplaod")

# Load and parse the HTML file
if submitted:
    if extract_trolley_items(file):
        df = pd.DataFrame(st.session_state.extracted_items)
    df.drop(columns=["price","price_currency"], inplace=True)
    # Change the order of columns to be name rate quantity price
    st.dataframe(df)
    st.session_state.df = df
    st.session_state.uploaded = True
    csv = df.to_csv(index=False)
    st.download_button(label="Download CSV", data=csv, file_name="trolley_items.csv", mime="text/csv")
    # Print out the extracted trolley items in a structured format if the extraction was successful
if launch_mito and "uploaded" in st.session_state:
    dic, code = spreadsheet(st.session_state.df)
    st.code(code)
    