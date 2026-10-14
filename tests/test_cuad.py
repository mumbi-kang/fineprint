import json

import pytest

from fineprint.cuad import category_of, coverage, load_cuad, make_split, verify_spans

CLAUSES = ["Renewal Term", "Governing Law"]


def fake_contract(title, text, answers_by_clause):
    qas = []
    for clause in ["Renewal Term", "Governing Law", "Parties"]:
        answers = answers_by_clause.get(clause, [])
        qas.append({
            "id": f"{title}__{clause}",
            "question": f'Highlight the parts (if any) of this contract related to "{clause}"',
            "answers": [{"text": t, "answer_start": text.index(t)} for t in answers],
            "is_impossible": not answers,
        })
    return {"title": title, "paragraphs": [{"context": text, "qas": qas}]}


@pytest.fixture
def cuad_file(tmp_path):
    text_a = "This Agreement renews for one year. It is governed by Delaware law."
    text_b = "No renewal here. Governed by Georgia law."
    data = {"data": [
        fake_contract("A", text_a, {"Renewal Term": ["renews for one year"],
                                    "Governing Law": ["governed by Delaware law"]}),
        fake_contract("B", text_b, {"Governing Law": ["Governed by Georgia law"]}),
    ]}
    path = tmp_path / "cuad.json"
    path.write_text(json.dumps(data))
    return path


def test_category_parsing():
    assert category_of({"id": "X__Cap On Liability"}) == "cap on liability"
    assert category_of({"id": "", "question": 'related to "Governing Law" that'}) == "governing law"


def test_load_and_coverage(cuad_file):
    contracts = load_cuad(cuad_file, CLAUSES)
    assert len(contracts) == 2
    assert coverage(contracts, CLAUSES) == {"Governing Law": 2, "Renewal Term": 1}
    assert verify_spans(contracts) == []


def test_unknown_clause_raises(cuad_file):
    with pytest.raises(ValueError, match="not found"):
        load_cuad(cuad_file, ["Made Up Clause"])


def test_split_is_reproducible_and_disjoint(cuad_file):
    contracts = load_cuad(cuad_file, CLAUSES)
    first = make_split(contracts, CLAUSES, test_size=1, seed=42, min_per_clause=1)
    second = make_split(contracts, CLAUSES, test_size=1, seed=42, min_per_clause=1)
    assert first == second
    test, dev = first
    assert not set(test) & set(dev)
    assert test == ["A"]  # rarest clause (Renewal Term) only exists in A
