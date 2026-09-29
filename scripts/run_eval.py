"""Score extraction output against gold. Writes a timestamped run record."""
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from extractor.evaluation import Counts, LIST_FIELDS, score_sample
from extractor.extract import extract_drug_label_info

GOLD = Path("data/gold.json")
SAMPLES = Path("data/samples.json")
OUT_DIR = Path("data/eval_runs")


def main():
    load_dotenv()
    gold_data = json.loads(GOLD.read_text())
    texts = {s["id"]: s["input_text"]
             for s in json.loads(SAMPLES.read_text())["samples"]}

    per_sample = []
    totals = {f: Counts() for f in LIST_FIELDS}
    dosage_correct = 0

    for s in gold_data["samples"]:
        result = extract_drug_label_info(texts[s["id"]])
        predicted = result.model_dump() if result else {}

        counts = score_sample(predicted, s["gold"])
        for f in LIST_FIELDS:
            totals[f] = totals[f] + counts[f]

        if predicted.get("dosage_form") == s["gold"].get("dosage_form"):
            dosage_correct += 1

        per_sample.append({
            "drug_name": s["drug_name"],
            "predicted": predicted,
            "counts": {f: vars(c) for f, c in counts.items()},
        })

    n = len(gold_data["samples"])
    print(f"{'field':<22} {'P':>6} {'R':>6} {'F1':>6} {'n_gold':>7}")
    for f in LIST_FIELDS:
        c = totals[f]
        print(f"{f:<22} {c.precision:>6.2f} {c.recall:>6.2f} "
              f"{c.f1:>6.2f} {c.n_gold:>7}")
    print(f"\ndosage_form accuracy: {dosage_correct}/{n}")
    print(f"labels: {n}  (micro-averaged; scores are a lower bound)")

    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    (OUT_DIR / f"{stamp}.json").write_text(json.dumps({
        "created_at": stamp,
        "gold": GOLD.name,
        "samples": SAMPLES.name,
        "matching": "exact after normalisation",
        "averaging": "micro",
        "totals": {f: vars(c) for f, c in totals.items()},
        "dosage_form_accuracy": f"{dosage_correct}/{n}",
        "per_sample": per_sample,
    }, indent=2))
    print(f"saved {OUT_DIR}/{stamp}.json")



if __name__ == "__main__":
    main()