# ✳ SeriesLab

Eine deutschsprachige Python-Web-Anwendung für eine interaktive Unterrichtsstunde: Eine Klasse sammelt Serienvorlieben und baut daraus ein erklärbares Empfehlungssystem. Vier klickbare Prozessknoten zeigen Antworten, Datenmatrix, gelernte Regeln und Empfehlungen. Hinter jedem Knoten lässt sich der tatsächlich ausgeführte Python-Code ansehen.

## Lokal starten

Python 3.11 oder neuer. Im Projektverzeichnis:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Im Browser `http://localhost:8501` öffnen. Die Demo mit 24 ausdrücklich synthetischen Antworten funktioniert sofort und verändert keine Klassenantworten.

Für eigene Klassenräume `.streamlit/secrets.toml.example` nach `.streamlit/secrets.toml` kopieren. `TEACHER_PASSWORD` durch ein eigenes langes Passwort ersetzen. Lokal die Beispielzeile `DATABASE_URL` entfernen: Ohne diese Einstellung wird automatisch SQLite in `data/classroom.sqlite3` verwendet. `APP_URL` auf die erreichbare Adresse ohne abschließenden Pfad oder Query setzen, lokal etwa `http://localhost:8501`. Für Smartphones im selben WLAN die LAN-IP des Computers verwenden und gegebenenfalls Port 8501 in der Firewall freigeben; `localhost` auf dem Smartphone verweist auf das Smartphone selbst.

## Ablauf für eine Schulstunde (ca. 25 Minuten)

**Passwort:** Nur `.streamlit/secrets.toml` wird geladen; `.streamlit/secrets.toml.example` ist eine Vorlage. Nach Änderungen die App neu starten. Umgebungsvariablen haben Vorrang. Das Lehrkraft-Passwort erstellt Räume; der separate Verwaltungsschlüssel öffnet einen bestehenden Raum. Umlaute werden unterstützt.

**Neuer Fragebogen:** Jede Serie hat eine Ja/Nein-Auswahl ohne Vorgabe. Alle 20 Antworten sind erforderlich; auch überall Nein ist gültig. Ja bedeutet „kenne ich und gefällt mir“, Nein „gefällt mir nicht oder kenne ich noch nicht“. Das Modell unterscheidet deshalb Nichtkennen und Abneigung nicht. In der Datenbank werden alle Ja/Nein-Werte explizit gespeichert; Training und Export verwenden die Ja-Titel. Ein Raum speichert seinen Serienkatalog. Ältere Räume behalten ihre ursprüngliche Auswahl — für die 20 Serien einen neuen Raum erstellen.

1. **Entdecken (3 Min.):** Demo öffnen. Frage: „Woher weiß ein Streamingdienst, was ich mag?“
2. **Sammeln (5 Min.):** „Meine Klasse“ wählen, Lehrkraft-Passwort eingeben und Raum erstellen. Den privaten Verwaltungsschlüssel sichern. Im ersten Knoten Teilnahme-Link oder QR-Code zeigen. Die Klasse öffnet den Fragebogen und wählt bekannte, beliebte Serien. Mit „Antworten aktualisieren“ den aktuellen Stand abrufen; anschließend Sammlung schließen.
3. **Verstehen (5 Min.):** Zweiten Knoten öffnen. Zeilen sind Antworten, Spalten Serien. Eine Null bedeutet „nicht gewählt“, nicht zwingend „mag ich nicht“.
4. **Lernen (7 Min.):** Im dritten Knoten Support und Konfidenz einstellen und „Modell lernen & für die Klasse veröffentlichen“ drücken. Eine Regel gemeinsam nachrechnen. Die Schwellenwerte verändern und erneut lernen: Welche Regeln verschwinden?
5. **Anwenden (5 Min.):** Vierten Knoten ausprobieren. Schülerinnen und Schüler können auf ihrem Teilnahme-Link zum Tab „Empfehlungen entdecken“ wechseln und das veröffentlichte Modell aktualisieren. Diese Auswahl wird nicht in die Trainingsdaten geschrieben.

Der Lernpfad ist bewusst fest vorgegeben, kein frei verdrahtbarer KNIME-Editor. Training und Anwenden bleiben getrennte Schritte. Neue Antworten oder veränderte Regler ändern ein bereits gelerntes Modell erst beim nächsten Training.

## Kostenlos hosten

**Netlify-Ordnerupload funktioniert für diese App nicht.** SeriesLab ist eine Streamlit-Anwendung und benötigt einen laufenden Python-Server (`streamlit run app.py`). Der Ordner enthält keine statische `index.html`. Ein Netlify-Upload startet den Python-Server nicht und führt deshalb zu „Page not found“. Eine zusätzliche HTML-Datei oder eine Weiterleitungsregel würde das Python-Backend nicht ersetzen. Verwende für dieses Projekt den folgenden Streamlit-Deploymentweg.

Bei einem manuellen Upload des gesamten Projektordners werden Dateien nicht durch `.gitignore` geschützt. Falls dabei `.streamlit/secrets.toml` oder `data/` mit hochgeladen wurden, entferne den betreffenden Deploy und ändere die darin enthaltenen Zugangsdaten. Veröffentliche nur den Quellcode über GitHub; Secrets gehören in die geschützten Einstellungen des Hostinganbieters.

Vorbereitet für **Streamlit Community Cloud + Neon PostgreSQL**. Die Anbieter führen kostenlose Tarife; Kontingente und Bedingungen vor dem Einsatz kontrollieren. Ein Hostingkonto, ein GitHub-Repository und ein Datenbankkonto werden von dir eingerichtet. Das Projekt ist noch nicht veröffentlicht.

1. Projekt in ein GitHub-Repository hochladen. Niemals `.streamlit/secrets.toml`, `data/` oder Zugangsdaten hochladen; `.gitignore` ist vorbereitet.
2. Bei [Neon](https://neon.com/pricing) ein PostgreSQL-Projekt im kostenlosen Tarif anlegen. Möglichst eine zur Schule passende Region wählen. Den Connection-String mit `sslmode=require` kopieren.
3. Bei [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud) eine App aus dem Repository erstellen, Einstiegspunkt `app.py`, Python 3.11 oder neuer.
4. In den erweiterten Einstellungen der App unter **Secrets** eintragen:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/DATABASE?sslmode=require"
TEACHER_PASSWORD = "eigenes-langes-passwort"
APP_URL = "https://DEINE-APP.streamlit.app"
```

5. App starten. Die Tabellen werden automatisch angelegt. Einen Klassenraum erstellen, den Teilnahme-Link auf einem zweiten Gerät testen, eine Antwort absenden und ein Modell veröffentlichen.

**Dauerhafte Speicherung:** Streamlit garantiert keine Beständigkeit lokaler Dateien in Community Cloud. Deshalb dort PostgreSQL verwenden, nicht SQLite. Siehe [Streamlit-Dokumentation zur Speicherung](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data). Kostenlose Dienste können bei Inaktivität schlafen oder bei ausgeschöpften Kontingenten pausieren. Die App vor der Veranstaltung öffnen und die lokale Demo als Ausweichmöglichkeit bereithalten.

## Was das Modell macht

`serieslab/model.py` verwendet **mlxtend**: `apriori()` findet häufige Serienkombinationen, `association_rules()` erzeugt Regeln und berechnet Support, Konfidenz und Lift. Die App bereitet die Daten auf und formatiert die Ergebnisse; der Lernalgorithmus kommt aus der Bibliothek. Unterstützt werden ein bis drei Serien als Voraussetzung und eine Zielserie. Standard: bis zu zwei Voraussetzungen, beispielsweise `[A, B] → [C]`. Es werden keine externen KI-Dienste, Netflix-Konten oder APIs benötigt.

Bibliotheksdokumentation: [Apriori](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/apriori/) und [Assoziationsregeln](https://rasbt.github.io/mlxtend/user_guide/frequent_patterns/association_rules/). Die getestete Version `mlxtend==0.23.4` steht in `requirements.txt`. Im Python-Tab des Lernknotens sind die tatsächlichen Bibliotheksaufrufe sichtbar.

Für jede gerichtete Regel X → Y (X ist eine Menge aus ein bis drei Serien, Y eine Zielserie):

- **Support:** Antworten mit Ja zu ALLEN Serien aus X und zu Y / alle Antworten (auch reine Nein-Antworten).
- **Konfidenz:** Antworten mit Ja zu ALLEN Serien aus X und zu Y / Antworten mit Ja zu ALLEN Serien aus X.
- **Lift:** Konfidenz / Anteil der Antworten mit Ja zu Y. Über 1 bedeutet einen positiven Zusammenhang gegenüber der allgemeinen Häufigkeit von Y.

Das Training berücksichtigt Support, Konfidenz und die maximale Anzahl Voraussetzungen. Empfehlungen verwenden passende Regeln mit Lift > 1 und blenden bereits ausgewählte Serien aus. **Alle Voraussetzungen müssen erfüllt sein (UND).** Bei `[A, B] → [C]` genügt A allein nicht; zusätzliche ausgewählte Serien sind erlaubt. Sortierung: zuerst mehr gemeinsam erfüllte Voraussetzungen, dann Lift und Konfidenz. Pro Zielserie erscheint die erste Regel, insgesamt höchstens sechs Empfehlungen. Dadurch erhält eine passende Kombination Vorrang vor einer Einzelregel für dieselbe Zielserie. Diese Präferenz für spezifischere Regeln garantiert keine höhere Vorhersagequalität. Unter „Alle passenden Regeln“ lassen sich auch die übrigen Treffer ansehen. Ohne passende Kombinationsregel bleiben Einzelregeln möglich; ohne passende Regel gibt es keine Empfehlung. Alte Einzelregeln bleiben lesbar; für Kombinationen erneut trainieren.

Konfidenz ist keine auf Testdaten gemessene Genauigkeit. Bei kleinen Stichproben können große Lift-Werte zufällig entstehen. Es gibt keinen Train/Test-Split und keine Behauptung über Vorhersagequalität. Das Projekt demonstriert unüberwachtes Musterlernen, nicht die tatsächliche Netflix-Technik.

## Daten & Verwaltung

Keine Namen, E-Mail-Adressen oder Geburtsdaten werden abgefragt. Pro Antwort speichert die App Serien und einen gehashten zufälligen Teilnahmeschlüssel. Dieser Schlüssel bleibt in der Streamlit-Sitzung; wiederholtes Absenden dort aktualisiert die Antwort. Nach Neuladen oder in einem anderen Browser sind weitere Antworten möglich. Es gibt keinen sicheren Nachweis „eine Person, eine Stimme“. Für eine betreute Unterrichtsstunde ausgelegt, nicht für öffentliche Abstimmungen.

Antworten sind nur über den privaten Verwaltungsschlüssel zugänglich. Der Teilnahme-Link enthält ausschließlich den Klassencode. Das veröffentlichte Modell enthält aggregierte Regeln und Häufigkeiten, die Teilnehmende sehen können. Hostanbieter können unabhängig von der Anwendung Verbindungsprotokolle führen. Die Lehrkraft sollte Nutzung und Serienauswahl mit den schulischen Vorgaben abstimmen und danach den Raum über „Verwaltung & Datensicherung“ löschen. Zuvor bei Bedarf Antworten als JSON, Matrix als CSV und Modell als JSON herunterladen. Exporte dienen der Sicherung/externen Weiterverarbeitung; ein Wiederimport ist nicht implementiert.

Die Serienliste ist eine anpassbare Unterrichtsauswahl in `CATALOG` in `serieslab/model.py`, keine Zusage aktueller Netflix-Verfügbarkeit oder Alterseignung. Vor einer Veranstaltung prüfen und bei Anpassungen neue Räume anlegen. Keine Poster oder fremden Markenbilder werden eingebunden.

## Projektstruktur & Tests

### Serienauswahl (Recherche: 18.09.2026)

Stranger Things, Wednesday, One Piece, Outer Banks, Ginny & Georgia, My Life with the Walter Boys, Heartstopper, XO, Kitty, Never Have I Ever, Sex Education, Young Royals, A Good Girl’s Guide to Murder, Forever, Finding Her Edge, Squid Game, Alice in Borderland, Bridgerton, Cobra Kai, Avatar – Der Herr der Elemente und Arcane.

Die Liste kombiniert Young-Adult-Serien und bekannte Streaming-Hits. Sie ist eine redaktionelle Annäherung an 17–20-Jährige, **keine statistisch belegte aktuelle Top 20 dieser Altersgruppe in Deutschland**. Grundlagen: [Netflix’ Teen-Serienübersicht vom August 2026](https://www.netflix.com/tudum/articles/teen-shows-on-netflix), [Young-Adult-Übersicht 2026](https://www.netflix.com/tudum/articles/new-young-adult-shows-movies), [Nutzungsbericht zweites Halbjahr 2025](https://about.netflix.com/en/news/what-we-watched-the-second-half-of-2025) und [Serienvorschau 2026](https://www.netflix.com/tudum/articles/new-shows-on-netflix-2026). Die Quellen liefern keine vollständige 17–20-Demografie.

```text
app.py                    Oberfläche, Knoten, Fragebogen, Lehrkraftbereich
serieslab/model.py        Kodierung, Kombinationsregeln, Empfehlungen, Demodaten
serieslab/storage.py      Räume, Berechtigungen, SQLite/PostgreSQL
tests/                    Rechenbeispiele, Speicher- und Oberflächentests
.streamlit/               Design und Konfigurationsvorlage
```

```powershell
python -m pip install pytest
python -m pytest -q
```

Tests prüfen bekannte Support-/Konfidenz-/Lift-Werte, Filter, Raumtrennung, Zugriffsschutz, Aktualisierung statt Duplikat, gleichzeitige Abgaben und den Demo-Lernpfad mit Streamlit AppTest. PostgreSQL sollte vor der Veranstaltung zusätzlich mit den tatsächlichen Hosting-Zugangsdaten geprüft werden.
