"""Reproduzierbare Simulationsannahmen, keine Schätzung realer X-Nutzer."""
from dataclasses import asdict, dataclass
import hashlib
import json

import numpy as np

from feedlab.catalog import POSTS, TOPICS


@dataclass(frozen=True)
class Settings:
    users: int = 300
    tendency: int = 0
    polarization: int = 55
    similarity: int = 75
    activity: int = 40
    seed: int = 42


def generate(settings):
    """Eine Transaktion = alle Like-Post-IDs eines fiktiven Nutzers.

    Tendenz verschiebt das Zentrum. Polarisierung trennt zwei Gruppen.
    Ähnlichkeitsliebe erhöht die Wirkung politischer Nähe auf Like-Chancen.
    Themeninteressen, Aktivität und Zufall verhindern deterministische Likes.
    Alle Nutzer bekommen modellhaft alle 20 Posts zu sehen.
    """
    if not 50 <= settings.users <= 1000 or not -100 <= settings.tendency <= 100:
        raise ValueError("Ungültige Anzahl oder Tendenz.")
    if any(not 0 <= value <= 100 for value in (settings.polarization, settings.similarity, settings.activity)):
        raise ValueError("Regler müssen zwischen 0 und 100 liegen.")
    if not 0 <= settings.seed <= 999999:
        raise ValueError("Seed muss zwischen 0 und 999999 liegen.")
    rng = np.random.default_rng(settings.seed)
    n = settings.users
    groups = rng.choice([-1, 1], n)
    positions = np.clip(settings.tendency / 100 + groups * settings.polarization / 125
                        + rng.normal(0, .20, n), -1, 1)
    interests = rng.normal(0, .65, (n, len(TOPICS)))
    activeness = rng.normal(0, .35, n)
    draws = rng.random((n, len(POSTS)))
    rows = []
    for i in range(n):
        likes, probabilities = [], {}
        for j, post in enumerate(POSTS):
            distance = abs(positions[i] - post["position"])
            logit = (-2.8 + 4.0 * settings.activity / 100 + activeness[i]
                     + interests[i, TOPICS.index(post["topic"])]
                     + 5.0 * settings.similarity / 100 * (.65 - distance))
            probability = float(1 / (1 + np.exp(-logit)))
            probabilities[post["id"]] = probability
            if draws[i, j] < probability:
                likes.append(post["id"])
        rows.append({"user": f"sim_{i+1:04d}", "position": float(positions[i]),
                     "likes": likes, "probabilities": probabilities})
    return {"schema": "feedlab-1", "settings": asdict(settings),
            "posts": [dict(post) for post in POSTS], "users": rows}


def transactions(dataset):
    return [user["likes"] for user in dataset["users"]]


def dataset_id(dataset):
    return hashlib.sha256(json.dumps(dataset, sort_keys=True).encode()).hexdigest()[:12]
