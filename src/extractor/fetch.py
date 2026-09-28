# src/extractor/fetch.py
import requests # HTTP library, used to call the openFDA API


FDA_LABEL_URL = "https://api.fda.gov/drug/label.json"

def fetch_labels(limit: int = 5) -> list[dict]:
    """Fetch raw drug labels from the openFDA API."""
    resp = requests.get(FDA_LABEL_URL, params={"limit": limit}, timeout=30)
    resp.raise_for_status()
    return resp.json()["results"]