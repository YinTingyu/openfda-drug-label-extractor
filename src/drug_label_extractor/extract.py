import requests

drug = requests.get("https://api.fda.gov/drug/label.json", params={"limit": 5})

data = drug.json()

labels = data["results"]

labels[0].keys()