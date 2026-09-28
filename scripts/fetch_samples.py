# scripts/fetch_samples.py
"""Fetch raw openFDA labels and save them as a versioned snapshot."""
import json
from datetime import date
from pathlib import Path

from extractor.fetch import fetch_labels


def main():
    labels = fetch_labels(limit=5)

    out = Path("data") / f"raw_labels_{date.today():%Y-%m-%d}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(labels, indent=2))

    print(f"saved {len(labels)} labels to {out}")


if __name__ == "__main__":
    main()