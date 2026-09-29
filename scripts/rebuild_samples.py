# scripts/rebuild_samples.py
"""Rebuild samples.json from a saved raw-label snapshot.

No network access: input_text is a pure function of the raw label and the
current RELEVANT_FIELDS, so changing the whitelist only requires rebuilding.
"""
import json
from datetime import date
from pathlib import Path

from extractor.parsing import label_to_text, get_drug_name, FIELDS

RAW = Path("data/raw_labels_2026-09-28.json") 
OUT = Path("data/samples.json")


def main():
    labels = json.loads(RAW.read_text())

    samples = []
    for i, label in enumerate(labels):
        text = label_to_text(label)
        samples.append({
            "index": i,
            "id": label.get("id"),
            "set_id": label.get("set_id"),
            "drug_name": get_drug_name(label),
            "input_text": text,
            "input_chars": len(text),
        })

    OUT.write_text(json.dumps({
        "created_at": date.today().isoformat(),
        "built_from": RAW.name,          # 可追溯：这份是从哪个快照来的
        "fields": FIELDS,       # 记下当时的白名单
        "samples": samples,
    }, indent=2))

    print(f"rebuilt {len(samples)} samples from {RAW.name} -> {OUT}")


if __name__ == "__main__":
    main()