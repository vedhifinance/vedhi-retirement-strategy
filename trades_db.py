import json
import base64
import requests
import streamlit as st
from datetime import datetime

TRADES_FILE = "trades.json"

def _headers():
    token = st.secrets["GITHUB_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

def _api_url():
    repo = st.secrets["GITHUB_REPO"]
    return f"https://api.github.com/repos/{repo}/contents/{TRADES_FILE}"

def load_trades():
    """Load trades from GitHub JSON file."""
    try:
        r = requests.get(_api_url(), headers=_headers(), timeout=10)
        if r.status_code == 404:
            return []
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content)
    except:
        return []

def save_trades(trades):
    """Save trades to GitHub JSON file."""
    try:
        content = base64.b64encode(
            json.dumps(trades, indent=2, default=str).encode("utf-8")
        ).decode("utf-8")

        # Get current SHA (needed for update)
        r = requests.get(_api_url(), headers=_headers(), timeout=10)
        sha = r.json().get("sha") if r.status_code == 200 else None

        payload = {
            "message": f"Update trades {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content,
        }
        if sha:
            payload["sha"] = sha

        requests.put(_api_url(), headers=_headers(),
                     json=payload, timeout=10)
        return True
    except:
        return False
