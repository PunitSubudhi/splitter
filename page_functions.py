from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet


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
            print(price_currency)
            print(price_price)
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
    st.download_button(label="Download CSV", data=csv, file_name="trolley_items.csv", mime="text/csv")

def save_df(df):
    try:
        df_dict = df.to_dict().copy()
        st.session_state["df"] = df_dict
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True

def launch_mito():
    dic, code = spreadsheet(get_df())
    st.code(code)
    st.session_state["mito_code"]=code