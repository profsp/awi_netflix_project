from dataclasses import replace
import numpy as np
import pytest

from feedlab.catalog import CATALOG, POSTS, PROFILES
from feedlab.synthetic import Settings, generate, transactions, dataset_id
from feedlab.model import train, recommend


def test_reproducibility_and_full_rows():
    settings = Settings()
    a, b = generate(settings), generate(settings)
    assert a == b and dataset_id(a) == dataset_id(b)
    assert dataset_id(a) != dataset_id(generate(replace(settings, seed=43)))
    assert len(a["users"]) == 300
    for user in a["users"]:
        assert -1 <= user["position"] <= 1
        assert set(user["probabilities"]) == set(CATALOG)
        assert all(0 < p < 1 for p in user["probabilities"].values())
        assert len(user["likes"]) == len(set(user["likes"]))


def test_direction_activity_and_homophily_controls():
    left = generate(Settings(tendency=-90))
    right = generate(Settings(tendency=90))
    assert np.mean([u["position"] for u in left["users"]]) < -.6
    assert np.mean([u["position"] for u in right["users"]]) > .6
    assert transactions(generate(Settings(similarity=0, tendency=-100))) == transactions(generate(Settings(similarity=0, tendency=100)))
    low, high = generate(Settings(activity=0)), generate(Settings(activity=100))
    assert sum(map(len, transactions(high))) > sum(map(len, transactions(low)))
    assert all(set(a).issubset(b) for a, b in zip(transactions(low), transactions(high)))
    left_ids = {p["id"] for p in POSTS if p["position"] < 0}
    right_ids = {p["id"] for p in POSTS if p["position"] > 0}
    assert sum(len(set(row) & left_ids) for row in transactions(left)) > sum(len(set(row) & right_ids) for row in transactions(left))
    assert sum(len(set(row) & right_ids) for row in transactions(right)) > sum(len(set(row) & left_ids) for row in transactions(right))


def test_polarization_and_default_learning():
    united = generate(Settings(polarization=0))
    split = generate(Settings(polarization=100))
    assert np.std([u["position"] for u in split["users"]]) > np.std([u["position"] for u in united["users"]])
    rules = train(transactions(generate(Settings())), .08, .55)
    assert rules and any(len(r["source"]) > 1 for r in rules)
    for likes in PROFILES.values():
        assert recommend(likes, rules)


@pytest.mark.parametrize("settings", [Settings(users=1), Settings(seed=-1), Settings(similarity=101), Settings(tendency=200)])
def test_invalid_generator_settings(settings):
    with pytest.raises(ValueError):
        generate(settings)
