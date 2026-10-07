"""Assoziationsregeln aus mlxtend für fiktive Post-Likes."""
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from feedlab.catalog import CATALOG


def encode(transactions, catalog=CATALOG):
    """Eine Zeile pro Antwort: 1 = ausgewählt, 0 = nicht ausgewählt."""
    return [{title: int(title in basket) for title in catalog} for basket in transactions]


def train(transactions, min_support=0.1, min_confidence=0.5):
    """Lerne [A, B, ...] → C mit Apriori und Assoziationsregeln aus mlxtend."""
    if not 0 <= min_support <= 1 or not 0 <= min_confidence <= 1:
        raise ValueError("Schwellenwerte müssen zwischen 0 und 1 liegen.")
    n = len(transactions)
    titles = sorted({title for basket in transactions for title in basket})
    if not n or not titles:
        return []
    matrix = pd.DataFrame(encode(transactions, titles), dtype=bool)
    # Bei Support 0 berücksichtigen wir jedes mindestens einmal beobachtete Set.
    # Feste Laufzeitgrenze für die Schul-Demo: bis zu drei Voraussetzungen + Ziel.
    itemsets = apriori(matrix, min_support=max(min_support, 1 / n),
                       use_colnames=True, max_len=4)
    if itemsets.empty:
        return []
    learned = association_rules(itemsets, num_itemsets=n, metric="confidence",
                                min_threshold=min_confidence,
                                return_metrics=["antecedent support", "support", "confidence", "lift"])
    # Für die Anzeige ein Zielpost pro Regel; links bleiben Kombinationen erlaubt.
    learned = learned[learned["consequents"].map(len) == 1]
    rules = [dict(source=sorted(row["antecedents"]), target=next(iter(row["consequents"])),
                  support=row["support"], confidence=row["confidence"], lift=row["lift"],
                  together=round(row["support"] * n),
                  source_count=round(row["antecedent support"] * n), total=n)
             for row in learned.to_dict("records")]
    return sorted(rules, key=lambda r: (-r["lift"], -r["confidence"], r["source"], r["target"]))


def antecedents(rule):
    """Alte Einzeltitel-Modelle bleiben lesbar; neue Modelle speichern Listen."""
    return [rule["source"]] if isinstance(rule["source"], str) else rule["source"]


def source_label(rule):
    return " UND ".join(antecedents(rule))


def matching_rules(likes, rules, min_lift=1.0):
    """UND-Abgleich; Rangfolge nach Konfidenz, Support und Lift, ohne Längenbonus."""
    chosen = set(likes)
    matches = [rule for rule in rules
               if set(antecedents(rule)).issubset(chosen)
               and rule["target"] not in chosen and rule["lift"] > 1
               and rule["lift"] >= min_lift]
    return sorted(matches, key=lambda r: (-r["confidence"], -r["support"], -r["lift"],
                                         len(antecedents(r)), r["target"], tuple(antecedents(r))))


def recommend(likes, rules, min_lift=1.0):
    """Pro Zielpost die bestplatzierte passende Regel, maximal sechs Vorschläge."""
    best = {}
    for rule in matching_rules(likes, rules, min_lift):
        best.setdefault(rule["target"], rule)
    return list(best.values())[:6]


def recommend_diverse(likes, rules, positions, limit=6, relevance_weight=0.7,
                      min_lift=1.0):
    """Greedy Neuordnung: Regelstärke plus Abstand zu bereits gewählten Positionen.

    Die Regeln und Kandidaten bleiben gleich. Nur die Rangfolge ändert sich.
    relevance_weight=0.7 ist eine transparente Produktentscheidung, kein Lernwert.
    """
    candidates = []
    seen_targets = set()
    for rule in matching_rules(likes, rules, min_lift):
        if rule["target"] not in seen_targets:
            candidates.append(rule)
            seen_targets.add(rule["target"])
    selected = []
    while candidates and len(selected) < limit:
        def score(rule):
            if not selected:
                return (rule["confidence"], rule["support"], rule["lift"])
            else:
                perspective_gain = min(
                    abs(positions[rule["target"]] - positions[item["target"]]) / 2
                    for item in selected
                )
            return (relevance_weight * rule["confidence"]
                    + (1 - relevance_weight) * perspective_gain,
                    rule["support"], rule["lift"])
        winner = max(candidates, key=score)
        selected.append(winner)
        candidates.remove(winner)
    return selected


def compose_feed(likes, rules, positions, recency, rule_share=0.7,
                 perspective_weight=0.3, min_lift=1.0, limit=6):
    """Mische Regel-Empfehlungen mit einer simulierten Chronik."""
    if not 0 <= rule_share <= 1 or not 0 <= perspective_weight <= 1:
        raise ValueError("Gewichte müssen zwischen 0 und 1 liegen.")
    ranked = recommend_diverse(
        likes, rules, positions, limit=limit,
        relevance_weight=1 - perspective_weight, min_lift=min_lift
    )
    wanted_rules = round(limit * rule_share)
    entries = [{"target": rule["target"], "origin": "Regel", "rule": rule}
               for rule in ranked[:wanted_rules]]
    excluded = set(likes) | {entry["target"] for entry in entries}
    chronological = sorted(
        (pid for pid in recency if pid not in excluded),
        key=lambda pid: (recency[pid], pid)
    )
    entries.extend({"target": pid, "origin": "Chronik", "rule": None}
                   for pid in chronological[:limit - len(entries)])
    return entries
