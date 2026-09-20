import pytest
from serieslab.model import encode, train, recommend, demo_data


def test_exact_metrics_and_direction():
    rules = train([["A", "B"], ["A", "B"], ["A"], ["C"]], 0, 0)
    ab = next(r for r in rules if r["source"] == ["A"])
    ba = next(r for r in rules if r["source"] == ["B"])
    assert ab["support"] == .5
    assert ab["confidence"] == pytest.approx(2/3)
    assert ab["lift"] == pytest.approx(4/3)
    assert ba["confidence"] == 1


def test_empty_duplicates_thresholds_and_encoding():
    assert train([]) == []
    assert train([[], []]) == []
    assert train([["A"], ["A"]]) == []
    assert train([["A"], ["B"]]) == []
    assert train([["A", "A", "B"], ["A"]], .6, 0) == []
    assert encode([["A"]], ["A", "B"]) == [{"A": 1, "B": 0}]
    with pytest.raises(ValueError):
        train([], 2)


def test_recommendations_exclude_known_and_nonpositive_rules():
    rules = train(demo_data())
    result = recommend(["Stranger Things"], rules)
    assert result
    assert all(r["target"] != "Stranger Things" and r["lift"] > 1 for r in result)
    assert len({r["target"] for r in result}) == len(result)
    assert recommend(["Unknown"], rules) == []
    assert recommend(["A"], train([["A", "B"], ["A", "B"]])) == []


def test_combination_metrics_and_all_antecedents_required():
    data = [["A", "B", "C"], ["A", "B", "C"], ["A", "B"], ["A"], ["B"], []]
    rule = next(r for r in train(data, 0, 0) if r["source"] == ["A", "B"] and r["target"] == "C")
    assert rule["support"] == pytest.approx(2/6)
    assert rule["confidence"] == pytest.approx(2/3)
    assert rule["lift"] == pytest.approx(2)
    assert recommend(["A"], [rule]) == []
    assert recommend(["B"], [rule]) == []
    assert recommend(["A", "B"], [rule]) == [rule]
    assert recommend(["A", "B", "C"], [rule]) == []
    assert any(len(r["source"]) == 3 for r in train([["A", "B", "C", "D"], []], 0, 0))
    assert recommend(["A"], [{**rule, "source": "A"}])


def test_catalog_and_demo_consistency():
    from serieslab.model import CATALOG
    assert len(CATALOG) == len(set(CATALOG)) == 20
    assert all(set(row).issubset(CATALOG) for row in demo_data())


def test_confidence_over_length_and_all_matching_rules_remain_visible():
    from serieslab.model import matching_rules
    single = dict(source=["A"], target="C", lift=4, confidence=.9, support=.3)
    pair = dict(source=["A", "B"], target="C", lift=2, confidence=.8, support=.2)
    triple = dict(source=["A", "B", "D"], target="C", lift=1.5, confidence=.7, support=.1)
    rules = [single, pair, triple]
    assert recommend(["A"], rules) == [single]
    assert recommend(["A", "B"], rules) == [single]
    assert recommend(["A", "B", "D", "Extra"], rules) == [single]
    assert matching_rules(["A", "B"], rules) == [single, pair]
    assert recommend(["A", "B", "C"], rules) == []
    # Eine bessere Kombinationsregel gewinnt unabhängig von ihrer Länge.
    other = dict(source=["A", "D"], target="C", lift=3, confidence=.95, support=.1)
    assert recommend(["A", "B", "D"], [single, pair, other]) == [other]


def test_support_tiebreak_deduplication_and_no_artificial_boost():
    single = dict(source=["A"], target="C", confidence=.8, support=.4, lift=2)
    rare = dict(source=["A", "B"], target="D", confidence=.8, support=.1, lift=8)
    assert recommend(["A", "B"], [rare, single, rare]) == [single, rare]
    equivalent = {**single, "source": ["A", "B"]}
    assert recommend(["A", "B"], [equivalent, single]) == [single]
