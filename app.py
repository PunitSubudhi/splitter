from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
from page_functions import *



if st.session_state.get("file_uploaded") is None:
    with st.form("splitter"):
        file = st.file_uploader("Upload File from Sainsburys Trolley Page")
        submitted = st.form_submit_button("Uplaod and View")

    # Load and parse the HTML file
    if submitted:
        if extract_trolley_items(file):
            st.toast("Extraction successful")
        else:
            st.error("Extraction failed")
        df = get_df()
        st.dataframe(df)
        st.session_state.file_uploaded = True
        with st.sidebar:
            st.markdown("### Download Data")
            download_csv()
        
        
elif st.session_state.get("file_uploaded") and not st.session_state.get("friends_uploaded"):
    df = get_df()
    with st.expander("View Data"):
        st.dataframe(df)
    st.dataframe(df)
    st.markdown("### Download Data")
    if st.button("Download as CSV"):
        download_csv()
    # take input of names of friends to be split
    with st.form("friends"):
        friends = st.text_input("Enter names of friends to split the bill with (separated by commas)")
        if st.form_submit_button("Submit"):
            friends = friends.split(",")
            st.session_state.friends_list = friends
            st.session_state["friends_uploaded"] = True
elif st.session_state.get("friends_uploaded"):
    df = get_df()
    with st.expander("View Data"):
        st.dataframe(df)
    friends = st.session_state.friends_list
    st.write(f"Friends to split the bill with: {friends}")
    # Add new columns for each friend to split the bill with
    for friend in friends:
        df[friend] = 0
    save_df(df)
    
    # Display the updated DataFrame
    df = get_df()
    st.dataframe(df)