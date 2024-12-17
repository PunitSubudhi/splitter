from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet
from page_functions import *

st.set_page_config(page_title="Split the Bill", page_icon=":money_with_wings:", layout="wide")


# Check if all required Splitwise parameters are present in query params
required_params = {
    "ck": "CONSUMER_KEY",
    "cs": "CONSUMER_SECRET", 
    "ak": "SPLITWISE_API_KEY",
    "gid": "GROUP_ID"
}

# Get all params or None if any are missing
params = {key: st.query_params.get(param) for param, key in required_params.items()}
if all(params.values()):
    # Store credentials and initialize Splitwise client
    for key, value in params.items():
        st.session_state[key] = value
            
    # Initialize Splitwise client and store in session state
    splitwise_client = Splitwise(
        st.session_state["CONSUMER_KEY"], 
        st.session_state["CONSUMER_SECRET"], 
        api_key=st.session_state["SPLITWISE_API_KEY"]
    )
    splitwise_client.getCurrentUser()  # Verify credentials work
    st.session_state["sObj"] = splitwise_client
    
if st.session_state.get("file_uploaded") is None:
    st.title("Uplaod Sainsburys Trolley Page or Upload CSV with items to continue")
    with st.form("splitter"):
        file = st.file_uploader("Upload File from Sainsburys Trolley Page", type=["html"])
        submitted = st.form_submit_button("Uplaod and View")

    # Load and parse the HTML file
    if submitted and file is not None:
        
        if extract_trolley_items(file):
            st.toast("Extraction successful")
        else:
            st.error("Extraction failed")
        df = get_df()
        st.dataframe(df)
        st.session_state.file_uploaded = True
        if st.button("continue"):
            st.rerun()
    elif submitted and file is None:
        st.warning("Please upload the file to proceed")
        
        
elif st.session_state.get("file_uploaded") and not st.session_state.get("friends_uploaded"):
    df = get_df()
    with st.expander("View/Download Data"):
        st.dataframe(df)
        st.markdown("### Download Data")
        download_csv()
    # take input of names of friends to be split
    with st.form("friends"):
        if st.session_state.get("sObj") is not None:
            st.session_state["splitwise_members"] = {}
            sObj = st.session_state["sObj"]
            group = sObj.getGroup(GROUP_ID)
            members = group.getMembers()
            for friend in members:
                fid =f"{friend.getId()}"
                st.session_state["splitwise_members"][friend.getFirstName()] = {
                    "name": friend.getFirstName(),
                    "email" : friend.getEmail(),
                    "id": fid
                }
            friends = [friend.getFirstName() for friend in group.getMembers()]
            friends = ",".join(friends)
        else:
            friends = ""    
            
        friends = st.text_input("Enter names of friends to split the bill with (separated by commas)",value=friends)
        
        if st.form_submit_button("Submit"):
            friends = friends.split(",")
            # Trim Whitesapce
            friends = [friend.strip() for friend in friends]
            st.session_state.friends_list = friends
            st.session_state["friends_uploaded"] = True
            st.rerun()
            
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
        if st.session_state.get("sObj") is not None:
            paid_by = st.selectbox("Select who paid", options=st.session_state.friends_list)
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
                    "Amount": f'{edited_df[f"{friend}_portion"].sum():.2f}'
                })
            st.dataframe(friend_due)
            st.session_state["friend_due"] = friend_due
            if st.session_state.get("sObj") is not None:
                st.session_state["paid_by"] = paid_by
   
if st.session_state.get("new_df") is not None:
    cols = st.columns(3)
    
    with cols[0]:
        st.markdown("### Download Splited Bill")
        get_final_csv_downlaod()
    with cols[1]:
        st.markdown("### Download Extracted Item Bill")
        download_csv()
        
if st.session_state.get("GROUP_ID") is not None and st.session_state.get("new_df") is not None:
    with st.expander("Push to Splitwise"):
        if st.session_state.get("sObj") is not None:
            sObj = st.session_state["sObj"]
            if st.button("Push to Splitwise"):
                push_expense(sObj)
        else:
            st.error("Please upload the file and add friends to split the bill with")