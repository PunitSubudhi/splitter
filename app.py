from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
from mitosheet.streamlit.v1 import spreadsheet

with st.form("splitter"):
    file = st.file_uploader("Upload File from Sainsburys Trolley Page")17
    submitted = st.form_submit_button("Uplaod")

# Load and parse the HTML file
if submitted:
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
            quantity_text = quantity_span.get_text(strip=True).replace("Quantity: ", "") if quantity_span else "N/A"
            
            # Extract price
            price_span = item.find("span", class_="ln-u-button")
            price_text = price_span.get_text(strip=True) if price_span else "N/A"

            # Append to results
            extracted_items.append({
                "name": item_name,
                "quantity": quantity_text,
                "price": price_text
            })

        # Print out the extracted trolley items in a structured format
        df = pd.DataFrame(extracted_items)
        df["price"] = df.price.str.replace("£", "").astype(float)
        df["quantity"] = df.quantity.astype(int)
        df["rate"] = df.price / df.quantity
        # Change the order of columns to be name rate quantity price
        df = df[["name", "rate", "quantity", "price"]]
        df.columns = ["Item", "Rate", "Quantity", "Price"]
        st.dataframe(df)
        csv = df.to_csv(index=False)
        st.download_button(label="Download CSV", data=csv, file_name="trolley_items.csv", mime="text/csv")
        for item in extracted_items:
            print(f"Item: {item['name']}\nQuantity: {item['quantity']}\nPrice: {item['price']}\n{'-'*20}")
    except Exception as e:
        st.error(f"An error occurred: {e}")