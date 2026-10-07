"""Fiktive Positionen auf einer bewusst vereinfachten Links-rechts-Achse.

Die Texte, Accounts und Einordnungen sind erfunden. Sie beschreiben weder
reale Personen noch Parteien und sind keine empirische politische Taxonomie.
"""

POSITIONS = {-1.0: "stark links", -0.5: "eher links", 0.0: "Mitte", 0.5: "eher rechts", 1.0: "stark rechts"}
TOPICS = ["Wirtschaft", "Klima", "Digitales", "Europa"]

_TEXTS = {
    "Wirtschaft": [
        ("Gewinne gemeinsam", "Große Unternehmen gehören in gemeinsame Hand. Beschäftigte sollten über Gewinne und Investitionen entscheiden."),
        ("Vermögen beteiligen", "Hohe Vermögen stärker besteuern und damit öffentliche Schulen und bezahlbare Wohnungen finanzieren."),
        ("Investieren mit Maß", "Öffentliche Investitionen und private Unternehmen sollen sich ergänzen. Entscheidend ist, was vor Ort funktioniert."),
        ("Mehr Spielraum", "Weniger Steuern und Bürokratie geben Unternehmen mehr Spielraum. Wachstum entsteht durch Eigeninitiative."),
        ("Eigene Wirtschaft zuerst", "Wirtschaftspolitik muss nationale Unternehmen zuerst stärken. Internationale Verpflichtungen sollten dahinter zurückstehen."),
    ],
    "Klima": [
        ("Umbau statt Weiter-so", "Für Klimagerechtigkeit brauchen wir einen grundlegenden Umbau der Wirtschaft statt immer mehr Produktion und Konsum."),
        ("Klimaschutz sozial", "Erneuerbare Energien und Bus und Bahn ausbauen. Haushalte mit wenig Einkommen müssen beim Umbau entlastet werden."),
        ("Ziele prüfen", "Klimaziele mit überprüfbaren Etappen verbinden. Kosten, Versorgung und Emissionsminderung gehören gemeinsam auf den Tisch."),
        ("Technik statt Vorgaben", "Innovation und Wettbewerb können Emissionen senken. Technologieoffenheit ist sinnvoller als immer neue Verbote."),
        ("National entscheiden", "Internationale Klimavorgaben sollen unsere Industrie nicht einschränken. Über Energie entscheidet allein die nationale Politik."),
    ],
    "Digitales": [
        ("Plattformen gemeinsam", "Große digitale Plattformen sollten gemeinschaftlich organisiert werden. Ihre Regeln dürfen nicht allein Eigentümern dienen."),
        ("Plattformmacht begrenzen", "Digitale Plattformen brauchen wirksame öffentliche Kontrolle und starke Rechte für Nutzerinnen und Nutzer."),
        ("Transparente Regeln", "Plattformregeln müssen verständlich sein. Unabhängige Prüfungen sollen zeigen, welche Folgen Empfehlungssysteme haben."),
        ("Freiraum für Plattformen", "Digitale Unternehmen brauchen mehr Freiraum. Der Staat sollte sich bei Plattformregeln möglichst zurückhalten."),
        ("Digitale Souveränität", "Nationale Behörden sollten die digitale Infrastruktur kontrollieren. Internationale Plattformen müssen nationale Prioritäten beachten."),
    ],
    "Europa": [
        ("Solidarität ohne Grenzen", "Europäische Zusammenarbeit soll soziale Rechte über Marktinteressen stellen. Vermögen und Macht müssen europaweit umverteilt werden."),
        ("Gemeinsam sozial", "Eine stärkere europäische Zusammenarbeit kann soziale Mindeststandards, Klimaschutz und gemeinsame Investitionen voranbringen."),
        ("Gemeinsam, wo es hilft", "Europa soll dort gemeinsam handeln, wo es Vorteile bringt. Andere Entscheidungen können regional bleiben."),
        ("Mehr Zuständigkeit vor Ort", "Europäische Institutionen sollten weniger Vorgaben machen. Nationale Parlamente müssen mehr selbst entscheiden können."),
        ("Nationalstaat vor Union", "Nationale Selbstbestimmung hat Vorrang vor europäischer Integration. Die zentralen Kompetenzen sollen vollständig zurück zu den Staaten."),
    ],
}

POSTS = [
    {"id": f"P{topic_index * 5 + stance_index + 1:02d}", "topic": topic,
     "position": position, "label": POSITIONS[position], "title": title, "text": body,
     "author": f"Stimme {topic_index * 5 + stance_index + 1:02d}",
     "handle": f"stimme_{topic_index * 5 + stance_index + 1:02d}"}
    for topic_index, (topic, texts) in enumerate(_TEXTS.items())
    for stance_index, (position, (title, body)) in enumerate(zip(POSITIONS, texts))
]
# Fiktive Minuten seit Veröffentlichung für die Chronik-Simulation.
_RECENCY = [8, 74, 19, 116, 43, 52, 6, 97, 27, 141,
            13, 88, 35, 4, 126, 61, 22, 109, 31, 156]
for post, minutes in zip(POSTS, _RECENCY):
    post["minutes_ago"] = minutes
POST_BY_ID = {post["id"]: post for post in POSTS}
CATALOG = list(POST_BY_ID)

# Ausschließlich fiktive Testprofile. Keine Frage nach der Haltung der Studierenden.
PROFILES = {
    "Linkes Testprofil": ["P02", "P07"],
    "Mittiges Testprofil": ["P03", "P13"],
    "Rechtes Testprofil": ["P04", "P09"],
    "Gemischtes Testprofil": ["P02", "P09"],
}


def post_label(post_id):
    post = POST_BY_ID[post_id]
    return f"{post_id} · {post['title']}"
