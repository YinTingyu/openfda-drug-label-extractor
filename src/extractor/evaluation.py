"""Set-based scoring of extraction output against hand-labelled gold.

Exact match after normalisation only — semantically equivalent rewordings
count as errors, so these scores are a lower bound on true quality.
"""
from dataclasses import dataclass

from extractor.cleaning import normalize_for_comparison

SAFETY_FIELDS = ["contraindications", "cautions", "general_warnings",
                 "adverse_reactions", "stop_use_conditions"]
LIST_FIELDS = ["indications"] + SAFETY_FIELDS


@dataclass
class Counts:
    tp: int = 0
    fp: int = 0
    fn: int = 0

    def __add__(self, other: "Counts") -> "Counts":
        return Counts(self.tp + other.tp, self.fp + other.fp, self.fn + other.fn)

    @property
    def n_gold(self) -> int:
        return self.tp + self.fn

    @property
    def precision(self) -> float:
        # 什么都没预测 = 没有误报，记 1.0
        denom = self.tp + self.fp
        return self.tp / denom if denom else 1.0

    @property
    def recall(self) -> float:
        # gold 为空 = 没有可漏的，记 1.0
        return self.tp / self.n_gold if self.n_gold else 1.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0


def count_field(predicted: list[str], gold: list[str]) -> Counts:
    p = {normalize_for_comparison(x) for x in predicted}
    g = {normalize_for_comparison(x) for x in gold}
    return Counts(tp=len(p & g), fp=len(p - g), fn=len(g - p))


def flatten(label: dict) -> dict[str, list[str]]:
    """Pull the six list fields out of a DrugLabel-shaped dict."""
    safety = label.get("safety") or {}
    return {"indications": label.get("indications") or [],
            **{f: safety.get(f) or [] for f in SAFETY_FIELDS}}


def score_sample(predicted: dict, gold: dict) -> dict[str, Counts]:
    p, g = flatten(predicted), flatten(gold)
    return {f: count_field(p[f], g[f]) for f in LIST_FIELDS}