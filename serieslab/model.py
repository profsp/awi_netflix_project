"""Verständliche Assoziationsanalyse mit bis zu drei Serien als Voraussetzung."""
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

LEGACY_CATALOG = [
    "Stranger Things", "Wednesday", "One Piece", "Avatar – Der Herr der Elemente",
    "Heartstopper", "Anne with an E", "Der Babysitter-Club", "Julie and the Phantoms",
    "Cobra Kai", "Eine Reihe betrüblicher Ereignisse", "Unser Planet", "Pokémon",
]

# Kuratierte Young-Adult-Auswahl, Recherche 18.09.2026; Quellen in README.md.
CATALOG = [
    "Stranger Things", "Wednesday", "One Piece", "Outer Banks",
    "Ginny & Georgia", "My Life with the Walter Boys", "Heartstopper",
    "XO, Kitty", "Never Have I Ever", "Sex Education", "Young Royals",
    "A Good Girl’s Guide to Murder", "Forever", "Finding Her Edge",
    "Squid Game", "Alice in Borderland", "Bridgerton", "Cobra Kai",
    "Avatar – Der Herr der Elemente", "Arcane",
]


def demo_data():
    """24 synthetische Antworten; keine echten Schülerdaten."""
    groups = [
        ["Stranger Things", "Wednesday", "Cobra Kai"],
        ["Stranger Things", "Wednesday"],
        ["Heartstopper", "Young Royals", "Sex Education"],
        ["Heartstopper", "Young Royals"],
        ["One Piece", "Avatar – Der Herr der Elemente", "Arcane"],
        ["One Piece", "Avatar – Der Herr der Elemente"],
        ["Wednesday", "A Good Girl’s Guide to Murder"],
        ["Outer Banks", "My Life with the Walter Boys", "Ginny & Georgia"],
    ]
    return [list(group) for group in groups for _ in range(3)]


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
    # Für die Anzeige eine Zielserie pro Regel; links bleiben Kombinationen erlaubt.
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


def matching_rules(likes, rules):
    """UND-Abgleich; Rangfolge nach Konfidenz, Support und Lift, ohne Längenbonus."""
    chosen = set(likes)
    matches = [rule for rule in rules
               if set(antecedents(rule)).issubset(chosen)
               and rule["target"] not in chosen and rule["lift"] > 1]
    return sorted(matches, key=lambda r: (-r["confidence"], -r["support"], -r["lift"],
                                         len(antecedents(r)), r["target"], tuple(antecedents(r))))


def recommend(likes, rules):
    """Pro Zielserie die bestplatzierte passende Regel, maximal sechs Vorschläge."""
    best = {}
    for rule in matching_rules(likes, rules):
        best.setdefault(rule["target"], rule)
    return list(best.values())[:6]
