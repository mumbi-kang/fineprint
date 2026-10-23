from fineprint.baselines import always_empty, keyword
from fineprint.eval import LabeledContract, evaluate, overlaps

CLAUSES = ["Governing Law", "Renewal Term"]
TEXT = ("This Agreement shall be governed by the laws of the State of Georgia. "
        "The parties agree to cooperate.")
CONTRACTS = [
    LabeledContract("A", TEXT, {"Governing Law": ["governed by the laws of the State of Georgia"],
                                "Renewal Term": []}),
]


def test_overlap_ignores_spacing_and_case():
    assert overlaps("Governed  by the LAWS", "governed by the laws of Georgia")
    assert not overlaps("renews yearly", "governed by the laws of Georgia")


def test_perfect_predictor():
    def perfect(text):
        return {"Governing Law": ["governed by the laws of the State of Georgia"]}
    r = evaluate(perfect, CONTRACTS, CLAUSES)
    assert r.scores["Governing Law"].tp == 1
    assert r.scores["Renewal Term"].tn == 1
    assert r.fabrication_rate == 0


def test_doing_nothing_scores_zero_recall():
    r = evaluate(always_empty, CONTRACTS, CLAUSES)
    assert r.scores["Governing Law"].fn == 1
    assert r.scores["Governing Law"].recall == 0


def test_false_alarm_counts_as_fp():
    def alarmist(text):
        return {"Renewal Term": ["The parties agree to cooperate."]}
    r = evaluate(alarmist, CONTRACTS, CLAUSES)
    assert r.scores["Renewal Term"].fp == 1


def test_made_up_quote_is_caught_and_not_credited():
    def liar(text):
        return {"Governing Law": ["governed by the laws of Delaware"]}
    r = evaluate(liar, CONTRACTS, CLAUSES)
    assert r.quotes_fabricated == 1
    assert r.scores["Governing Law"].tp == 0
    assert r.scores["Governing Law"].fn == 1


def test_keyword_baseline_finds_governing_law():
    r = evaluate(keyword, CONTRACTS, CLAUSES)
    assert r.scores["Governing Law"].tp == 1
