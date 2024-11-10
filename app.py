from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
from page_functions import *

st.set_page_config(page_title="Split the Bill", page_icon=":money_with_wings:", layout="wide")


if st.session_state.get("file_uploaded") is None:
    with st.form("splitter"):
        file = st.file_uploader("Upload File from Sainsburys Trolley Page",type=["html"])
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
        st.markdown("### Download Data")
        download_csv()
        
        
elif st.session_state.get("file_uploaded") and not st.session_state.get("friends_uploaded"):
    df = get_df()
    with st.expander("View Data"):
        st.dataframe(df)
    st.markdown("### Download Data")
    download_csv()
    # take input of names of friends to be split
    with st.form("friends"):
        friends = st.text_input("Enter names of friends to split the bill with (separated by commas)")
        if st.form_submit_button("Submit"):
            friends = friends.split(",")
            # Trim Whitesapce
            friends = [friend.strip() for friend in friends]
            st.session_state.friends_list = friends
            st.session_state["friends_uploaded"] = True
            
elif st.session_state.get("friends_uploaded"):
    df = get_df()
    friends = st.session_state.friends_list
    st.write(f"Friends to split the bill with: {friends}")
    # Add new columns for each friend to split the bill with
    for friend in friends:
        df[friend] = 0
    save_df(df)
    # Display the updated DataFrame
    df = get_df()
    #st.dataframe(df)
    
    with st.form("split portions"):
        edited_df = st.data_editor(df)
        if st.form_submit_button("Calculate portions"):
            edited_df["total_portions"] = edited_df[st.session_state.friends_list].sum(axis=1)
            edited_df["portion_price"] = edited_df["price"] / edited_df["total_portions"]
            for friend in st.session_state.friends_list:
                edited_df[f"{friend}_portion"] = edited_df[friend] * edited_df["portion_price"]
            with st.expander("View Split Bill"):
                st.dataframe(edited_df)
            save_new_df(edited_df)
            friend_due = []
            for friend in st.session_state.friends_list:
                friend_due.append({
                    "Friend": friend,
                    "Amount": edited_df[f"{friend}_portion"].sum()
                })
            st.dataframe(friend_due)
            st.session_state["friend_due"] = friend_due
   
if st.session_state.get("new_df") is not None:
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown("### Download Splited Bill")
        get_final_csv_downlaod()
    with cols[1]:
        st.markdown("### Download Extracted Item Bill")
        download_csv()