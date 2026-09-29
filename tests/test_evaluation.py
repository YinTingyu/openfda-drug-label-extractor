from extractor.evaluation import Counts, count_field


def test_perfect_match_ignores_case():
    c = count_field(["acne", "boils"], ["Acne", "BOILS"])
    assert (c.tp, c.fp, c.fn) == (2, 0, 0)
    assert c.f1 == 1.0


def test_both_empty_is_perfect_and_contributes_nothing():
    c = count_field([], [])
    assert (c.tp, c.fp, c.fn) == (0, 0, 0)
    assert c.f1 == 1.0


def test_predicted_nothing_when_gold_has_items():
    c = count_field([], ["acne"])
    assert c.recall == 0.0
    assert c.f1 == 0.0


def test_extra_prediction_lowers_precision_only():
    c = count_field(["acne", "boils", "junk"], ["acne", "boils"])
    assert c.recall == 1.0
    assert c.precision == 2 / 3


def test_counts_add_for_micro_averaging():
    total = count_field(["a"], ["a"]) + count_field([], ["b"])
    assert (total.tp, total.fp, total.fn) == (1, 0, 1)
    assert total.recall == 0.5