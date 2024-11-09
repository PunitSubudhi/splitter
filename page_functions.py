from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd


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
                "price": price_text,
                "price_price": price_price,
                "price_currency": price_currency
            })
        st.session_state.extracted_items = extracted_items
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False
    return True
