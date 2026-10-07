# ✕ FeedLab — Wer formt deinen Feed?

Ein mobiles Python-Lernlabor im Stil eines Social-Media-Feeds. Studierende erzeugen eine **vollständig fiktive Community**, untersuchen deren Likes, lernen mit **mlxtend** Assoziationsregeln und experimentieren mit Empfehlungen politischer Posts für fiktive Testprofile.

Unabhängiges Lehrprojekt, nicht mit X verbunden. Kein Scraping, keine X-API, keine echten Accounts, keine Befragung von Studierenden und keine Speicherung persönlicher politischer Einstellungen.

## Sofort starten

Python 3.11 oder neuer, im Projektverzeichnis:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

`http://localhost:8501` öffnen. Ein vorbereiteter Datensatz mit 300 fiktiven Personen ist sofort verfügbar. Jede Browser-Sitzung hat ein unabhängiges Experiment. Passwörter, Datenbank und Hosting-Secrets werden nicht benötigt.

## Lernpfad

1. **Mission:** Zwei Feeds für dasselbe fiktive Profil vergleichen, zunächst eine Vermutung abgeben und die Leitfrage entdecken: Warum verändert die Trainingscommunity den Feed?
2. **Experiment:** Eine Hypothese wählen und zunächst nur eine Generatorannahme verändern. Einzelne Personen, Chancen, Transaktionen, Posts und die 0/1-Matrix liegen in einem optionalen Vertiefungstab.
3. **Muster erklären:** Mindest-Support und Mindest-Konfidenz einstellen. Apriori findet häufige Post-Kombinationen; `association_rules()` erzeugt Regeln. Die Oberfläche erklärt zuerst „Wie häufig?“ und „Wie zuverlässig im Datensatz?“; Lift, Tabellen und Python-Code sind Vertiefungen.
4. **Feed gestalten:** Das identische Testprofil mit drei Produktreglern untersuchen: Anteil Assoziationsregeln vs. Chronik, Mindest-Lift und Gewicht der Perspektivenvielfalt. Feed und Balkendiagramm der politischen Modell-Tags reagieren live. Eine Gestaltung A lässt sich speichern und mit B vergleichen.

Alle Schritte zeigen den tatsächlich verwendeten Python-Code in einem aufklappbaren Bereich. Die Navigation bleibt auf schmalen Smartphone-Bildschirmen als 2×2-Auswahl bedienbar; breite Datentabellen sind horizontal scrollbar. Für eine kurze Studienorientierung kann man Mission, eine Regel und die Produktentscheidung durchlaufen, ohne Matrix oder Code zu öffnen.

## Datendesign: viele Personen, derselbe Post-Katalog

**Eine Transaktion = alle gelikten Post-IDs einer fiktiven Person.** Eine einzelne Person mit vielen Posts würde nur eine Transaktion liefern. Für gemeinsame Like-Muster simulieren wir deshalb viele Personen, die denselben Katalog sehen.

Der Katalog enthält 20 kurze, selbst verfasste Posts: vier Themen (Wirtschaft, Klima, Digitales, Europa), jeweils mit fünf fest zugeordneten Modell-Positionen −1, −0,5, 0, +0,5, +1. Accounts und Texte sind erfunden. Die Labels „stark links“ bis „stark rechts“ sind **didaktische Modellannahmen**, keine empirische politische Taxonomie. Reale Haltungen sind mehrdimensional; beispielsweise ist Technologieoffenheit kein eindeutiges Kennzeichen einer bestimmten politischen Gruppe. Die Simulation behauptet keine Haltung oder Verbindung realer Personen oder Parteien.

**Die Items des Lernverfahrens sind Post-IDs, nicht politische Tags.** Tags und Texte dienen der Interpretation. Politische Nähe beeinflusst ausschließlich die synthetische Datengenerierung. Das Modell entdeckt die so erzeugten Zusammenhänge nur über die Likes.

## Wie die Regler wirken

Für jede Person wird eine Position `z` erzeugt:

```text
z = clip(Tendenz / 100 + Gruppe × Polarisierung / 125 + Rauschen, -1, 1)
Gruppe ∈ {-1, +1}, gleich wahrscheinliche Ziehung
Rauschen ~ Normalverteilung(0, 0.20)
```

- **Tendenz −100 … +100:** verschiebt das Zentrum der Bevölkerung nach links/rechts. Sie ist keine exakte Vorgabe für den empirischen Mittelwert.
- **Polarisierung 0 … 100:** trennt zwei Teilgruppen. Bei 0 liegen sie gemeinsam um das Zentrum, bei 100 deutlich auseinander. An den Achsengrenzen wird abgeschnitten; bei starker Tendenz entstehen daher asymmetrische Gruppen.
- **Vorliebe für ähnliche Positionen 0 … 100:** bestimmt die Stärke politischer Nähe beim Liken. Bei 0 haben politische Positionen keinerlei Einfluss auf die Likes; Themenmuster und Zufall bleiben.
- **Like-Aktivität 0 … 100:** verändert die allgemeine Like-Neigung. Der Reglerwert ist nicht der Prozentsatz gelikter Posts.

Für jede Person und jeden Post ergibt sich die Like-Chance aus einer logistischen Funktion:

```text
s = -2.8 + 4 × Aktivität/100 + persönliche_Aktivität + Themeninteresse
    + 5 × Ähnlichkeitsliebe/100 × (0.65 - abs(z - Postposition))
P(Like) = 1 / (1 + exp(-s))
```

Persönliche Aktivität wird aus `Normal(0, 0.35)`, Themeninteresse pro Person und Thema aus `Normal(0, 0.65)` gezogen. Ein gleichverteilter Zufallswert entscheidet dann über den einzelnen Like. Diese Koeffizienten sind transparente, frei gesetzte Unterrichtsannahmen, **nicht aus X-Daten geschätzt**. Hohe Wahrscheinlichkeit garantiert keinen Like.

Alle 20 Posts gelten modellhaft als gesehen. Wir modellieren keine reale Ausspielungslogik, Bots, Retweets, zeitliche Reihenfolge oder ungleiche Sichtbarkeit. Ein Nicht-Like ist kein Beweis für Ablehnung. Leere Like-Sammlungen bleiben als Transaktionen erhalten.

Gleiche Einstellungen und gleicher Seed erzeugen dieselben Daten. Bei festem Seed und gleicher Personenanzahl bleiben die Zufallsziehungen gleich, wenn einzelne Regler verändert werden. Damit lassen sich Annahmen gezielt vergleichen. Verschiedene Seeds zeigen die Unsicherheit kleiner Stichproben.

## Lernen & Empfehlen

`feedlab/model.py` verwendet `mlxtend.frequent_patterns.apriori` und `association_rules`. Die getestete Bibliotheksversion steht in `requirements.txt`. Intern begrenzt `max_len=4` die Suche auf höchstens drei Voraussetzungen und einen Zielpost, damit dichte Datensätze auf kostenlosem Hosting handhabbar bleiben. Dies ist keine einstellbare Qualitätsmetrik.

Für X → Y:

- **Support:** Personen mit allen Likes aus X und Y / alle simulierten Personen.
- **Konfidenz:** Personen mit allen Likes aus X und Y / Personen mit allen Likes aus X.
- **Lift:** Konfidenz / allgemeine Like-Häufigkeit von Y.

Bei der Empfehlung müssen **alle Voraussetzungen** gewählt sein. Bereits gelikte Posts werden ausgeblendet; nur Regeln mit Lift > 1 kommen infrage. Sortierung: Konfidenz, dann Support, dann Lift; bei gleichen Werten die kürzere Regel. Pro Zielpost zählt nur die bestplatzierte Regel, maximal sechs Ziele. Mehrere passende Regeln werden nicht addiert. Kombinationen bleiben vollständig berücksichtigt, erhalten aber keinen pauschalen Vorrang.

Es gibt keinen universell besten Regel-Rankingstandard. Die gewählte Maximum-Konfidenz-Baseline ist erklärbar, aber weder eine kalibrierte Wahrscheinlichkeit für die gesamte Auswahl noch eine Garantie gegen Fehlprognosen. Quellen: [mlxtend Apriori](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/apriori/), [mlxtend Assoziationsregeln](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/), [Feremans & Goethals: Scalable Evaluation of Rule-Based Recommender Systems](https://adrem.uantwerpen.be/bibrem/pubs/rule-based.pdf).

Die alternative Strategie „Mit Perspektivenvielfalt“ lernt kein zweites Modell. Sie verwendet denselben Kandidatenpool und wählt iterativ Posts nach `0,7 × Konfidenz + 0,3 × Perspektivabstand`. Der Abstand ist die kleinste normierte Distanz des politischen Modell-Tags zu bereits ausgewählten Posts. Die Gewichtung 70/30 ist sichtbar, bewusst diskutierbar und nicht aus Daten geschätzt. Sie kann die durchschnittliche Konfidenz senken und garantiert weder faire Repräsentation noch tatsächliche Meinungsvielfalt.

## Bezug zur Wirtschaftsinformatik

Das Lab stellt nicht nur die Frage „Wie funktioniert Apriori?“, sondern „Welches Ziel soll ein digitales Produkt verfolgen?“ Studierende erleben vier typische Perspektiven der Wirtschaftsinformatik:

- **Daten:** Welche Beobachtungen und Annahmen bilden unsere Wirklichkeit ab?
- **Technik:** Wie werden aus Transaktionen Regeln und Empfehlungen?
- **Produkt und Organisation:** Welche Kennzahl optimiert die Plattform und wer entscheidet darüber?
- **Wirkung und Verantwortung:** Welche Nebenfolgen, Messlücken und Zielkonflikte entstehen?

Die abschließende Produktentscheidung hat absichtlich keine Musterlösung. Für eine reale Entscheidung wären zusätzliche Nutzungs-, Qualitäts-, Fairness- und Geschäftsmetriken nötig. Genau diese Verbindung von Mensch, Aufgabe, Organisation und IT ist der Studienorientierungsbezug.

## Experimente für Studierende

**A. Gleiches Testprofil, andere Trainingscommunity:** Nur die zwei Ausgangslikes des Testprofils bleiben gleich. Die jeweils 300 anderen synthetischen Profile bilden verschiedene Trainingscommunities und erzeugen deshalb andere Regeln und neue Empfehlungen.

**B. Gleiche Daten, andere Produktentscheidung:** Gestaltung A speichern, nur einen Feedregler ändern und direkt Feedplätze sowie Verteilung der Modell-Tags vergleichen.

**B. Ohne politische Nähe:** Ähnlichkeitsliebe auf 0 stellen. Themeninteressen können weiterhin Regeln erzeugen. Ein verbliebener politisch markierter Treffer beweist deshalb keine politische Ursache.

**D. Polarisierung bei gleicher Mitte:** Tendenz auf 0 belassen, Polarisierung ändern. Die Mitte einer Verteilung sagt nichts darüber aus, ob sich zwei gegensätzliche Gruppen gegenüberstehen.

**D. Zufall und Stichprobengröße:** Gleiche Regler, anderer Seed; anschließend mehr Personen. Welche Regeln sind stabil? Trainingskonfidenz ist keine auf neuen Personen geprüfte Genauigkeit.

Die Feed-Auswertung zeigt die Verteilung der fest vergebenen Post-Tags und deren ungewichteten Mittelwert. Ein Mittelwert von 0 kann sowohl mittige als auch gegensätzliche Posts bedeuten. **Eine einzige Empfehlungsrunde belegt weder eine dauerhafte Filterblase noch eine Änderung politischer Überzeugungen.** Die Simulation macht ihre eingebauten Annahmen sichtbar; sie validiert keine Aussage über den echten X-Algorithmus.

## Speicherung und Hosting

Es gibt keine Erhebung echter Schülerdaten, keine Anmeldung und keinen Datenbankzugriff. Daten, Testprofil und Vergleich liegen nur im flüchtigen Streamlit-Sitzungsspeicher. Neuladen/Verbindungsabbruch kann das Experiment zurücksetzen. Downloads sichern ausschließlich synthetische Daten auf Wunsch lokal. Server/Hostinganbieter können technische Verbindungsprotokolle führen; Streamlit-Nutzungsstatistiken sind deaktiviert.

Das bestehende öffentliche GitHub-Repository bleibt `profsp/awi_netflix_project`, damit eine bestehende Streamlit-Verknüpfung weiter funktioniert. Für Streamlit Community Cloud: Repository auswählen, Branch `main`, Einstiegspunkt `app.py`, Python 3.11 oder neuer. **Keine Secrets oder externe Datenbank erforderlich.** Die App benötigt weiterhin einen Python-Server; Netlify-Ordnerupload reicht nicht aus.

Bei einem Update von SeriesLab sind Fragebogen, Räume, Passwortzugang und SQLite/PostgreSQL-Code entfernt. Frühere lokale Dateien in `data/` und vorhandene externe Datenbanken werden nicht automatisch gelöscht, aber von FeedLab nicht gelesen. Alte `TEACHER_PASSWORD`, `APP_URL` und `DATABASE_URL`-Secrets können aus den Hosting-Einstellungen entfernt werden. Bestehende Serienmodelle werden nicht importiert. Frühere Teilnahme-Links öffnen die neue Laborseite.

## Projekt & Tests

```text
app.py                  Mobiler Lernpfad, Datenansicht, Feed und A/B-Vergleich
feedlab/catalog.py      20 fiktive Posts, Modell-Tags und Testprofile
feedlab/synthetic.py    Reproduzierbarer Datengenerator
feedlab/model.py        mlxtend-Training und Regelanwendung
tests/                  Rechenwerte, Generatoreffekte, Zustände, UI-Ablauf
```

```powershell
python -m pip install pytest
python -m pytest -q
```

Tests prüfen unter anderem Reproduzierbarkeit, Richtung der Generatorregler, politische Unabhängigkeit bei Ähnlichkeitsliebe 0, exakte Regelkennzahlen, UND-Bedingungen, Modellrücksetzung nach neuen Daten, Sitzungstrennung und den kompletten A/B-Lernpfad. Sie messen keine Vorhersagequalität auf realen politischen Daten.
