from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from splitwise import Splitwise
from splitwise.expense import Expense
from splitwise.user import ExpenseUser
from streamlit_oauth import OAuth2Component

def extract_trolley_items(file):
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


def get_df():
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
    return df_to_return
   
def download_csv():
    df = get_df()
    csv = df.to_csv(index=False)
    st.download_button(label="Download Extracted Items", data=csv, file_name="trolley_items.csv", mime="text/csv")

def save_df(df):
    try:
        df_dict = df.to_dict().copy()
        st.session_state["df"] = df_dict
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True

def save_new_df(df):
    try:
        st.session_state["new_df"] = df
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True

def get_new_df():
    if st.session_state.get("new_df") is None:
        st.error("No data available. Please upload a file.")
    df = pd.DataFrame(st.session_state["new_df"])
    return df

def get_final_csv_downlaod():
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
    st.download_button(label="Download Split", data=csv_return, file_name="trolley_items_final.csv", mime="text/csv",key="split")
    
def splitwise():
    sObj = Splitwise("fZYEdpSuM6gYXND5h097UmPgETZNNpEy6EEUppVm","poBh7c0Z4oAtvVPFmQiEElPnH6sbctjhUmb2gdNQ",api_key="j4I679pFrffR73HWz1L51fzgkqzNYM4pPEWwqVU7")
    current = sObj.getCurrentUser()
    
def oauth2(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL,REDIRECT_URI, SCOPE):
    oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_URL, TOKEN_URL, REFRESH_TOKEN_URL, REVOKE_TOKEN_URL)
    
    if 'token' not in st.session_state:
        # If not, show authorize button
        result = oauth2.authorize_button("Authorize", REDIRECT_URI, SCOPE)
        if result and 'token' in result:
            # If authorization successful, save token in session state
            st.session_state.token = result.get('token')
            st.rerun()
    else:
        # If token exists in session state, show the token
        token = st.session_state['token']
        st.json(token)
        if st.button("Refresh Token"):
            # If refresh token button is clicked, refresh the token
            token = oauth2.refresh_token(token)
            st.session_state.token = token
            st.rerun()