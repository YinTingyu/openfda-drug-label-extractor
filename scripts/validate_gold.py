# scripts/validate_gold.py
"""Gold answers must satisfy the same schema as model output."""
import json
from pathlib import Path
from extractor.schema import DrugLabel

def main():
    data = json.loads(Path("data/gold.json").read_text())
    errors = 0
    for s in data["samples"]:
        try:
            DrugLabel(**s["gold"])
        except Exception as e:
            print(f"[{s['drug_name']}] {e}\n")
            errors += 1
    print("gold is valid" if not errors else f"{errors} invalid entries")

if __name__ == "__main__":
    main()