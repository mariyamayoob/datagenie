import streamlit as st
from streamlit_option_menu import option_menu 
import time
from pathlib import Path
import os 
from utils.api import fetch_table_data
import requests


# Page config
st.set_page_config(page_title="DataGenie", page_icon = "images/favicon.png", layout="wide")

# Sidebar menu using option_menu
with st.sidebar:
    st.image("images/favicon.png", width=125)
    st.title("DataGenie")
    selected_tab = option_menu(
        menu_title="Navigation",
        options=["Query Interface", "View Database"],
        icons=["search",  "bi bi-database-gear"],
        menu_icon="cast",
        default_index=0,
    )

# --- Screen 1: Query Interface ---
if selected_tab == "Query Interface":
    st.title("Ask your tables or the AI 🔍")

    
    with st.form("query_form"):
        query = st.text_input("Enter your question:", placeholder="e.g., Give me the count of cusotomers that has opened an consumer loan account within the last one year?")
        submitted = st.form_submit_button("Submit")

        if submitted and query:
            st.info("🚀 Sending your question to DataGenie...")

            try:
                response = requests.post("http://dg-backend:8003/generate", json={"prompt": query})
                result = response.json()

                if "data" in result:
                    st.success("Here's what I found 👇")
                    st.dataframe(result["data"], use_container_width=True)
                elif "response" in result:
                    st.success("Here's what I found 👇")
                    st.write(result["response"])
                else:
                    st.warning("No response received.")

            except Exception as e:
                st.error(f"Failed to connect to backend: {str(e)}")


# --- Screen 2: View Database ---
elif selected_tab == "View Database":
    st.title("📊 View Database Tables")

    table = st.selectbox("Choose a table", ["customers", "credit_transactions", "loan_transactions"])

    if st.button("Show Data"):
        data = fetch_table_data(table)
        if not data.empty:
            st.success(f"Showing data from `{table}`")
            st.dataframe(data, use_container_width=True)
        else:
            st.warning("No data found or failed to fetch.")