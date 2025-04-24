import requests
import pandas as pd

BACKEND_URL = "http://dg-backend:8003"

def fetch_table_data(table_name: str):
    try:
        res = requests.get(f"{BACKEND_URL}/table/{table_name}")
        res.raise_for_status()
        return pd.DataFrame(res.json().get("rows", []))
    except Exception as e:
        return pd.DataFrame({"error": [str(e)]})
