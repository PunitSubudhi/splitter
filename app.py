
"""
This Streamlit application helps users split a bill by uploading a Sainsbury's Trolley Page HTML file or a CSV file with items. 
It integrates with Splitwise to manage group expenses.
Modules:
- BeautifulSoup: For parsing HTML files.
- streamlit: For creating the web application.
- pandas: For data manipulation.
- page_functions: Custom functions for handling file uploads and data extraction.
Functions:
- extract_trolley_items(file): Extracts items from the uploaded HTML file.
- get_df(): Retrieves the current DataFrame stored in session state.
- save_df(df): Saves the DataFrame to session state.
- save_new_df(df): Saves the updated DataFrame with split portions to session state.
- download_csv(): Provides a CSV download link for the extracted items.
- get_final_csv_downlaod(): Provides a CSV download link for the split bill.
- push_expense(sObj): Pushes the calculated expenses to Splitwise.
Workflow:
1. Check for required Splitwise parameters in the query params.
2. Initialize Splitwise client and store credentials in session state.
3. Prompt user to upload a Sainsbury's Trolley Page HTML file or a CSV file.
4. Extract items from the uploaded file and display them in a DataFrame.
5. Prompt user to enter names of friends to split the bill with.
6. Add columns for each friend in the DataFrame and allow user to edit portions.
7. Calculate portions and display the split bill.
8. Provide options to download the split bill and push expenses to Splitwise.
"""
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
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
    create_sobj(params)
    
if not st.experimental_user.is_logged_in:
    if st.sidebar.button("Login"):
        st.login()
else:
    with st.sidebar:
        st.write(f"Hello {st.experimental_user.get('given_name')} 👋")
        st.write(st.experimental_user)
        st.image(st.experimental_user.get("picture"))
        
        if st.button("Logout"):
            st.logout()
            
        if st.secrets.get(st.experimental_user.get("email")):
            if st.secrets[st.experimental_user.get("email")].get("SPLITWISE_API_KEY") is not None:
                st.write(st.secrets[st.experimental_user.get("email")])
                params = {
                    "SPLITWISE_API_KEY": st.secrets[st.experimental_user.get("email")].get("SPLITWISE_API_KEY"),
                    "GROUP_ID": st.secrets[st.experimental_user.get("email")].get("SPLITWISE_GID"),
                    "CONSUMER_KEY": st.secrets[st.experimental_user.get("email")].get("SPLITWISE_CONSUMER_KEY"),
                    "CONSUMER_SECRET": st.secrets[st.experimental_user.get("email")].get("SPLITWISE_CONSUMER_SECRET")
                }
                create_sobj(params)
        else:
            st.write("Splitwise API info not found, \n Please contact punitsbudhi@gmail.com")
        
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

if st.session_state.get("file_uploaded") is None:
    with st.expander("Input Data Manually"):
        input_method = st.radio("Select Input Method", ["CSV", "Manual"])
        if input_method == "CSV":
            csv_file = st.file_uploader("Upload CSV file", type=["csv"])
            input_df = pd.read_csv(csv_file) if csv_file is not None else None
        elif input_method == "Manual":
            st.markdown("### Enter data manually")
            input_df = pd.DataFrame({
                "name": ["item1", "item2"],
                "rate": [10.0, 20.0],
                "quantity": [1, 2],
            })
            # input_df,code = spreadsheet(input_df)¯
            # print(input_df)
            # input_df = input_df.get("df1")
            input_df = st.data_editor(input_df,num_rows="dynamic",use_container_width=True)
            
        if st.button("Save"):
            if input_method == "Manual":
                input_df["price"] = input_df["rate"] * input_df["quantity"]
            st.session_state.extracted_items = input_df.to_dict(orient="records")
            save_df(input_df)
            st.session_state.file_uploaded = True
            st.rerun()
        
elif st.session_state.get("file_uploaded") and not st.session_state.get("friends_uploaded"):
    df = get_df()
    with st.expander("View/Download Data"):
        st.dataframe(df)
        Total = df["price"].sum()
        st.write(f"Total: {Total}")
        st.markdown("### Download Data")
        download_csv()
    # take input of names of friends to be split
    with st.form("friends"):
        if st.session_state.get("sObj") is not None:
            st.session_state["splitwise_members"] = {}
            sObj = st.session_state["sObj"]
            group = sObj.getGroup(st.session_state["GROUP_ID"])
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
            try:
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
            except Exception as e:
                st.error(f"An error occurred: {e}")
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
            description= st.text_input("Enter a description for the expense", value=f"Sainsburys - {st.session_state.paid_by}")
            if st.button("Push to Splitwise"):
                push_expense(sObj,description)
        else:
            st.error("Please upload the file and add friends to split the bill with")