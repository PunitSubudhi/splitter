import random
import re
from bs4 import BeautifulSoup
import string
import streamlit as st
import pandas as pd
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from decimal import Decimal
import requests
import io
import boto3

def extract_trolley_items(file) -> bool:
    try:
        soup = BeautifulSoup(file.read(), "html.parser")

        # Locate the trolley summary items by data-testid attribute
        trolley_items = soup.find_all("div", {"data-testid": "order-item"})

        # Extract details for each item in the trolley
        extracted_items = []
        for item in trolley_items:
            # Extract item name
            name = item.find("button", {"role": "link"})
            item_name = name["aria-label"] if name else "N/A"
            
            # Extract quantity
            quantity_span = item.find("div", class_="order-details__trolley-summary-quantity")
            quantity_text = float(quantity_span.get_text(strip=True).replace("Quantity: ", "") if quantity_span else "N/A")
            
            # Extract price
            price_span = item.find("span", class_="ln-u-button")
            price_text = price_span.get_text(strip=True) if price_span else "N/A"
            price_currency = price_text[:1]
            price_price = float(price_text.removeprefix(price_currency))
            # Append to results
            extracted_items.append({
                "name": item_name,
                "rate": price_price / quantity_text if quantity_text != 0 else 0,
                "quantity": quantity_text,
                "price_text": price_text,
                "price": price_price,
                "price_currency": price_currency
            })
        st.session_state.extracted_items = extracted_items
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True


def create_sobj(params):
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
    # st.toast(f"Connected to Splitwise for {splitwise_client.getCurrentUser().getFirstName()} {splitwise_client.getCurrentUser().getLastName()}")
    # st.toast(f"Ready to Post to Group : {splitwise_client.getGroup(st.session_state['GROUP_ID']).getName()}")

def get_df() -> pd.DataFrame:
    """ 
    Get the DataFrame from the session state
    """
    if st.session_state.get("extracted_items") is None and st.session_state.get("df") is None:
        st.error("No data available. Please upload a file.")
    # If extracted items are available, create a DataFrame
    elif st.session_state.get("df") is None and st.session_state.get("extracted_items") is not None:
        df = pd.DataFrame(st.session_state.extracted_items)
        save_df(df)
    df_to_return = pd.DataFrame(st.session_state["df"])
    # if price_text and price_currency columns are present, remove them
    if "price_text" in df_to_return.columns and "price_currency" in df_to_return.columns:
        df_to_return.drop(columns=["price_text","price_currency"], inplace=True)
    df_to_return.index = range(1, len(df_to_return) + 1)
    return df_to_return

def nav_to(url) -> None:
    """ 
    Redirect to a new URL
    """
    nav_script = """
        <meta http-equiv="refresh" content="0; url="%s"">
    """ % (url)
    st.write(nav_script, unsafe_allow_html=True)

def download_csv() -> None:
    """
    Download the extracted items as a CSV file 
    """
    df = get_df()
    csv = df.to_csv(index=False)
    st.download_button(label="Download Extracted Items", data=csv, file_name="trolley_items.csv", mime="text/csv")

def save_df(df) -> bool:
    """ 
    Save the DataFrame to the session state
    """
    try:
        df_dict = df.to_dict().copy()
        st.session_state["df"] = df_dict
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True

def save_new_df(df) -> bool:
    """ 
    Save the new DataFrame to the session state
    """
    try:
        st.session_state["new_df"] = df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True

def get_new_df() -> pd.DataFrame:
    """ 
    Get the new DataFrame from the session state
    """
    if st.session_state.get("new_df") is None:
        st.error("No data available. Please upload a file.")
    df = pd.DataFrame(st.session_state["new_df"])
    return df

def get_final_csv_string() -> str:
    """
    Get the final CSV string to download
    """
    df = get_new_df()
    csv = df.to_csv(index=False)
    friend_due = st.session_state.get("friend_due")
    if friend_due is not None:
        friend_due_df = pd.DataFrame(friend_due)
        csv_return = ""
        friend_due_df = friend_due_df.T
        friend_due_df.columns = friend_due_df.iloc[0]
        friend_due_df = friend_due_df[1:]
        csv_return += friend_due_df.to_csv(index=False)
        csv_return += "\n\n"
        csv_return += csv
    return csv_return

def get_final_csv_downlaod() -> None:
    """
    Download the final CSV file
    """
    csv_return = get_final_csv_string()
    file_name = st.text_input("Enter the file name", value="trolley_items_final") + ".csv"
    st.download_button(label="Download Split", data=csv_return, file_name=file_name, mime="text/csv",key="split")

        
def upload_csv_to_s3(csv_string, file_name):
    try:
        # Convert the CSV string to bytes
        csv_bytes = io.BytesIO(csv_string.encode('utf-8'))
        
        obj = boto3.client(
            "s3",
            aws_access_key_id=st.secrets["aws_access_key_id"],
            aws_secret_access_key=st.secrets["aws_secret_access_key"]
        )
        Bucket = "sainsburysitems"
        Key = file_name
        obj.upload_fileobj(
            Fileobj=csv_bytes,
            Bucket=Bucket,
            Key=Key,
            ExtraArgs={'ACL': 'public-read'}
        )
        # Generate the public URL
        public_url = f"https://{Bucket}.{st.secrets['aws_url']}/{Key}"
        st.session_state["s3_url"] = public_url
        return public_url
    except Exception as e:
        print(f"An error occurred: {e}")
        return csv_string


def upload_image_to_s3(image, file_name):
    try:
        obj = boto3.client(
            "s3",
            aws_access_key_id=st.secrets["aws_access_key_id"],
            aws_secret_access_key=st.secrets["aws_secret_access_key"]
        )
        Bucket = "sainsburysitems"
        Key = file_name
        obj.upload_fileobj(
            Fileobj=image,
            Bucket=Bucket,
            Key=Key,
            ExtraArgs={'ACL': 'public-read'}
        )
        # Generate the public URL
        public_url = f"https://{Bucket}.{st.secrets['aws_url']}/{Key}"
        return public_url
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    
def push_expense(sObj, description="Sainsburyssplitter",receipt=None) -> None:
    """ 
    Push the expense to Splitwise
    """
    Total_due = sum([Decimal(friend["Amount"]) for friend in st.session_state.friend_due])
    for friend in st.session_state.friend_due:
        st.session_state.splitwise_members[friend["Friend"]]["paid_share"] = "00.00" if friend["Friend"] != st.session_state.paid_by else f"{Total_due:.2f}"
        st.session_state.splitwise_members[friend["Friend"]]["owed_share"] = friend["Amount"]
    
    """ expense_users =
        {
            "id" : friend.get("id"),
            "paid_share" : friend["paid_share"],
            "owed_share" : friend["owed_share"]
        }"""
    expense_users = []    
    for friend in st.session_state.splitwise_members:
        expense_user = ExpenseUser()
        expense_user.setId(st.session_state.splitwise_members[friend]["id"])
        expense_user.setPaidShare(st.session_state.splitwise_members[friend]["paid_share"])
        expense_user.setOwedShare(st.session_state.splitwise_members[friend]["owed_share"])
        expense_users.append(expense_user)
    expense = Expense()
    expense.setCost(Total_due)
    expense.setDescription(description)
    expense.setUsers(expense_users)
    expense.setGroupId(st.session_state["GROUP_ID"])
    #expense.setDetails(upload_csv_to_gofile(get_final_csv_string(), st.secrets["gofile_token"]))
    unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    expense.setDetails(upload_csv_to_s3(get_final_csv_string(), f"trolley_items_final_{st.session_state.paid_by}_{unique_code}.csv"))
    
    if receipt is not None:
        try:
            st.write(receipt)
            receipt_content = receipt.read()
            # Save the receipt photo in as a file and then get the path to that file and then set it as receipt
            with open(f"temp/receipt_{unique_code}.jpg", "wb") as f:
                f.write(receipt_content)
            expense.setReceipt(f"temp/receipt_{unique_code}.jpg")
            
        except Exception as e:  
            st.error(f"An error occurred in setting Receipt: {e}")
    
    nExpense, errors = sObj.createExpense(expense)
    
    if nExpense is not None:
        st.success(f"Expense created successfully with id: {nExpense.getId()}")
    else:
        st.error(f"An error occurred: {errors.getErrors()}")
        
        base=errors.getErrors().get("base")
        if base:
            match = re.search(r"owed shares \((£\d+\.\d+)\) is different than the total cost \((£\d+\.\d+)\)", base[0])
            if match:
                owed_shares = match.group(1)
                total_cost = match.group(2)
                st.error(f"The total of everyone's owed shares ({owed_shares}) is different than the total cost ({total_cost})")
                if st.button("Fix the total cost"):
                    new_expense = Expense()
                    new_expense.setCost(owed_shares)
                    expense.setDescription(f"Sainsburys - {st.session_state.paid_by}")
                    expense.setUsers(expense_users)
                    expense.setGroupId(st.session_state["GROUP_ID"])
                    expense.setDetails(get_final_csv_string())
                    nExpense, errors = sObj.createExpense(expense)
                    
                    if nExpense is not None:
                        st.success("Expense created successfully!")
                    else:
                        st.error(f"An error occurred: {errors.getErrors()}")
