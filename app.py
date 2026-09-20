"""SeriesLab — interaktives Python-Labor für Assoziationsanalyse."""
import hashlib
import inspect
import io
import json
import os
import secrets
from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlencode

import pandas as pd
import streamlit as st

from serieslab.model import CATALOG, demo_data, encode, recommend, train, source_label, matching_rules, antecedents
from serieslab.storage import Store

st.set_page_config(page_title="SeriesLab · Deine Klasse. Dein Algorithmus.", page_icon="✳", layout="wide")
st.html("""<style>
.block-container{max-width:1300px;padding-top:2rem;padding-bottom:3rem}
h1{font-size:3.5rem!important;letter-spacing:-.065em;line-height:1.06!important}
h2,h3{letter-spacing:-.035em} p{line-height:1.65}
[data-testid="stSidebar"]{border-right:1px solid #263047}
[data-testid="stMetric"]{background:#151d32;border:1px solid #2a3450;border-radius:14px;padding:16px}
[data-testid="stMetricLabel"]{color:#a7b5cd}
div.stButton>button{border-radius:10px;min-height:46px}
.eyebrow{color:#9dafce;font-size:.73rem;font-weight:700;letter-spacing:.18em;text-transform:uppercase}
.brand{font-size:1.4rem;font-weight:800;letter-spacing:-.05em;margin-bottom:2rem}.brand span{color:#ff718c}
.hero{padding:1rem 0 1.5rem}.hero em{color:#ff718c;font-style:normal}
.sub{color:#a7b5cd;max-width:670px;font-size:1.05rem}
.pill{display:inline-block;border:1px solid #39425b;padding:5px 12px;border-radius:20px;font-size:.75rem;color:#bcc9df;margin-bottom:15px}
.node{border:1px solid #35405b;border-radius:14px;background:linear-gradient(140deg,#1c2944,#121b2e);padding:18px 15px;min-height:160px;margin-bottom:9px}
.node.active{border-color:#ff718c;box-shadow:0 0 0 1px #ff718c}
.node .symbol{font-size:1.6rem;color:#7bdaca;margin-bottom:10px}.node .label{font-weight:700;font-size:1rem}.node small{color:#a7b5cd}.node .step{float:right;color:#7e8ba6;font-size:.75rem}
.connector{text-align:center;color:#7bdaca;font-size:1.5rem;padding-top:65px}
.result{padding:20px;border:1px solid #365352;background:linear-gradient(120deg,#172f35,#162037);border-radius:14px;margin-bottom:14px}
.result h3{margin:4px 0 12px;font-size:1.4rem}.result .rank{color:#7bdaca;font-size:.72rem;letter-spacing:.13em}
.footer{border-top:1px solid #29334b;color:#8998b4;padding-top:20px;margin-top:35px;font-size:.8rem}
@media(max-width:700px){h1{font-size:2.5rem!important}.connector{display:none}.node{min-height:100px}}
</style>""")


def setting(name, default=""):
    try:
        return os.environ.get(name) or st.secrets.get(name, default)
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        return os.environ.get(name, default)


@st.cache_resource
def get_store(url):
    return Store(url)


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def show_recommendations(model, key, catalog=CATALOG):
    selected = st.multiselect("Welche Serien magst du?", catalog, key=key,
                              help="Diese Auswahl wird nur für die Empfehlung verwendet und nicht als Trainingsantwort gespeichert.")
    if not model:
        st.info("Noch kein Modell vorhanden. Zuerst im Lernlabor Regeln lernen.")
        return
    st.caption(f"Modell aus {model['n']} Antworten · gelernt am {model['created']} · Auswahl hier verändert das Modell nicht.")
    if not selected:
        st.info("Wähle eine oder mehrere Serien. Dann suchen wir passende Regeln im gelernten Modell.")
        return
    results = recommend(selected, model["rules"])
    matches = matching_rules(selected, model["rules"])
    combinations = sum(len(antecedents(rule)) > 1 for rule in matches)
    st.caption(f"Passende Regeln: {len(matches)} · davon Kombinationsregeln: {combinations}. Alle Voraussetzungen einer Regel müssen in deiner Auswahl enthalten sein; weitere ausgewählte Serien sind erlaubt.")
    if len(selected) > 1 and not combinations:
        st.info("Für diese Auswahl gibt es keine passende Kombinationsregel mit Lift über 1. Einzelregeln werden weiterhin berücksichtigt. Neue Antworten werden erst nach erneutem Lernen einbezogen.")
    if not results:
        st.info("Keine passende Regel mit positivem Zusammenhang gefunden. Probiere andere Serien oder sammelt mehr Antworten. Das Modell erfindet keine Empfehlung.")
    for i, rule in enumerate(results, 1):
        source = source_label(rule)
        st.markdown(f"**{'Kombinationsregel' if len(antecedents(rule)) > 1 else 'Einzelregel'}: [{source}] → [{rule['target']}]**")
        st.html(f'<div class="result"><div class="rank">EMPFEHLUNG {i:02d} · WEIL DU {source.upper()} MAGST</div><h3>{rule["target"]}</h3><div>{rule["together"]} von {rule["source_count"]} Personen, die {source} gemeinsam gewählt haben, mögen auch diese Serie.</div></div>')
        st.caption(f"Konfidenz {rule['confidence']:.0%} · Support {rule['support']:.0%} · Lift {rule['lift']:.2f}")
    if matches:
        with st.expander("Alle passenden Regeln zu deiner Auswahl"):
            st.dataframe(pd.DataFrame([{"Wenn du ALLE magst": source_label(r), "Dann auch": r["target"],
                                        "Voraussetzungen": len(antecedents(r)), "Konfidenz": f"{r['confidence']:.0%}", "Support": f"{r['support']:.0%}",
                                        "Lift": round(r["lift"], 2)} for r in matches]), hide_index=True)
        st.caption("Sortierung: Konfidenz, danach Support und Lift. Einzel- und Kombinationsregeln werden gleich bewertet; bei ansonsten gleichen Werten wird die kürzere Regel angezeigt. Pro Zielserie zählt nur die bestplatzierte Regel, keine Addition überlappender Regeln.")
    st.caption("Das sind Zusammenhänge in dieser Gruppe, keine Garantie für deinen Geschmack. Konfidenz ist keine gemessene Vorhersagegenauigkeit.")


def participant_page(store):
    st.markdown('<div class="brand">✳ Series<span>Lab</span></div>', unsafe_allow_html=True)
    st.title("Dein Geschmack zählt.")
    st.write("Hilf deiner Klasse, ein Empfehlungssystem zu bauen. Ohne Namen, ohne Account.")
    code = st.text_input("Klassencode", value=st.query_params.get("room", "")).strip().upper()
    room = store.room(code) if code else None
    if not room:
        st.info("Trage den Klassencode deiner Lehrkraft ein.")
        return
    survey, prediction = st.tabs(["01 · Vorlieben teilen", "02 · Empfehlungen entdecken"])
    with survey:
        st.caption("Gespeichert werden deine Ja/Nein-Antworten und ein zufälliger Teilnahmeschlüssel. Die Lehrkraft kann die Antworten ohne Namen ansehen und löschen.")
        st.session_state.setdefault("participant", secrets.token_urlsafe(24))
        if room["opened"]:
            with st.form("survey_" + code):
                st.markdown(f"#### {len(room['catalog'])} Serien · Gefällt dir die Serie?")
                st.caption("Bei allen Serien ist Nein vorausgewählt. Stelle nur die Serien auf Ja, die du kennst und magst. Nein bedeutet: gefällt mir nicht, kenne ich nicht oder nicht bewertet. Bitte prüfe deine Auswahl vor dem Absenden.")
                answers = {}
                for index, title in enumerate(room["catalog"], 1):
                    answers[title] = st.radio(f"{index:02d} · {title}", ["Ja", "Nein"], index=1,
                                              horizontal=True, key=f"vote_{code}_{title}")
                consent = st.checkbox("Meine Auswahl darf für diese Unterrichtsdemonstration verwendet werden.")
                submitted = st.form_submit_button("Meine Vorlieben teilen →", type="primary")
            if submitted:
                missing = sum(value is None for value in answers.values())
                if missing:
                    st.warning(f"Noch {missing} Serien ohne Antwort. Bitte jede Serie mit Ja oder Nein beantworten.")
                elif not consent:
                    st.warning("Bitte bestätige die Verwendung für den Unterricht.")
                else:
                    store.submit(code, st.session_state.participant, {title: answer == "Ja" for title, answer in answers.items()})
                    st.success("Danke! Deine Antwort ist angekommen. Erneutes Absenden aktualisiert sie in dieser Sitzung.")
                    st.balloons()
        else:
            st.info("Die Sammlung ist geschlossen. Du kannst jetzt das gelernte Modell ausprobieren.")
        st.caption("Bitte nur einmal teilnehmen. Nach einem Neuladen kann eine neue Sitzung entstehen; dies ist keine manipulationssichere Abstimmung.")
    with prediction:
        if st.button("Veröffentlichtes Modell aktualisieren"):
            st.rerun()
        show_recommendations(room["model"], "student_likes_" + code, room["catalog"])


def lab(store):
    with st.sidebar:
        st.markdown('<div class="brand">✳ Series<span>Lab</span></div>', unsafe_allow_html=True)
        st.markdown("**Das Empfehlungslabor**")
        st.caption("Machine Learning zum Mitmachen")
        mode = st.radio("Arbeitsbereich", ["Demo entdecken", "Meine Klasse"], label_visibility="collapsed")
        st.divider()
        st.markdown("**So funktioniert’s**")
        st.write("① Vorlieben sammeln\n\n② Daten sichtbar machen\n\n③ Muster lernen\n\n④ Empfehlungen ausprobieren")
        st.divider()
        st.caption("Python unter der Haube.\n\nJeder Knoten lässt sich öffnen — inklusive Zwischenergebnis und echtem Code.")
    demo = mode == "Demo entdecken"
    code, secret = "", ""
    if not demo:
        st.subheader("Dein Klassenraum")
        with st.expander("Klassenraum erstellen oder wieder öffnen", expanded="owner" not in st.session_state):
            password = st.text_input("Lehrkraft-Passwort", type="password")
            configured = setting("TEACHER_PASSWORD")
            if not configured:
                st.warning("Es ist noch kein Lehrkraft-Passwort eingerichtet. Lokal: .streamlit/secrets.toml anlegen und TEACHER_PASSWORD setzen. Die Datei secrets.toml.example ist nur eine Vorlage. Danach die App neu starten.")
            st.caption("Das Lehrkraft-Passwort erstellt neue Räume. Zum Wiederöffnen verwendest du unten den separaten Verwaltungsschlüssel deines Raums.")
            if st.button("Neuen Klassenraum erstellen", disabled=not bool(configured)):
                if secrets.compare_digest(password.encode("utf-8"), str(configured).encode("utf-8")):
                    st.session_state.owner = store.create_room()
                    st.rerun()
                else:
                    st.error("Das Lehrkraft-Passwort stimmt nicht.")
            c = st.text_input("Vorhandener Klassencode")
            s = st.text_input("Verwaltungsschlüssel", type="password")
            if st.button("Klassenraum öffnen"):
                if store.authorized(c.strip().upper(), s):
                    st.session_state.owner = (c.strip().upper(), s)
                    st.rerun()
                else:
                    st.error("Klassencode oder Verwaltungsschlüssel stimmt nicht.")
        if "owner" not in st.session_state:
            return
        code, secret = st.session_state.owner
        room = store.room(code)
        if room is None:
            del st.session_state.owner
            st.rerun()
        data = store.transactions(code, secret)
        model = room["model"]
        catalog = room["catalog"]
        if catalog != CATALOG:
            st.info("Dieser ältere Raum behält seinen bisherigen Serienkatalog. Erstelle für den neuen Fragebogen mit 20 Serien einen neuen Klassenraum.")
        if not setting("DATABASE_URL"):
            st.warning("Lokale Speicherung aktiv. Für dauerhaftes Cloud-Hosting DATABASE_URL einrichten; Antworten zusätzlich exportieren.")
    else:
        data = demo_data()
        model = st.session_state.get("demo_model")
        catalog = CATALOG
    st.markdown(f'<div class="hero"><span class="pill">{"DEMO · 24 SYNTHETISCHE ANTWORTEN" if demo else "KLASSENRAUM · " + code}</span><div class="eyebrow">Datenbasierte Lernverfahren</div><h1>Woher weiß Netflix<br>was Du<em> als nächstes sehen willst?</em></h1><p class="sub">Warum wird dir eine Serie empfohlen? Baue ein eigenes Empfehlungssystem und entdecke, was hinter dem nächsten Vorschlag steckt.</p></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Gesammelte Antworten", len(data))
    b.metric("Serien im Katalog", len(catalog))
    c.metric("Gelernte Regeln", len(model["rules"]) if model else "—")
    st.write("")
    st.markdown("### Ein Lernpfad. Vier Einblicke.")
    st.caption("Klicke einen Knoten an. Jeder Schritt zeigt dir, was mit den Daten passiert.")
    scope = "demo" if demo else code
    node_key = "node_" + scope
    st.session_state.setdefault(node_key, 0)
    nodes = [("◉", "Vorlieben sammeln", "Fragebogen → Antworten"), ("▦", "Daten verstehen", "Antworten → 0 und 1"), ("✳", "Regeln lernen", "Gemeinsamkeiten → Modell"), ("✧", "Serien empfehlen", "Deine Auswahl → Vorschläge")]
    columns = st.columns([5, .5, 5, .5, 5, .5, 5])
    for i, (symbol, title, subtitle) in enumerate(nodes):
        with columns[i * 2]:
            active = "active" if st.session_state[node_key] == i else ""
            st.markdown(f'<div class="node {active}"><span class="step">0{i+1}</span><div class="symbol">{symbol}</div><div class="label">{title}</div><small>{subtitle}</small></div>', unsafe_allow_html=True)
            if st.button(f"{symbol} {title}", key=f"node_{scope}_{i}", use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state[node_key] = i
                st.rerun()
        if i < 3:
            columns[i * 2 + 1].markdown('<div class="connector">→</div>', unsafe_allow_html=True)
    st.divider()
    node = st.session_state[node_key]
    st.subheader(f"0{node+1} · {nodes[node][1]}")
    function = [Store.submit, encode, train, recommend][node]
    view, python = st.tabs(["Entdecken & ausprobieren", "</> Python-Code"])
    with python:
        st.caption("Dies ist der tatsächliche Quellcode der Funktion, die hinter diesem Knoten arbeitet.")
        if node == 2:
            st.code("from mlxtend.frequent_patterns import apriori, association_rules", language="python")
        if node == 3:
            st.code(inspect.getsource(matching_rules), language="python")
        st.code(inspect.getsource(function), language="python")
    with view:
        if node == 0:
            if demo:
                st.write("24 erfundene Personen haben ihre Lieblingsserien ausgewählt. Mit diesen Demodaten kannst du den gesamten Ablauf sofort ausprobieren.")
                st.dataframe(pd.DataFrame({"Antwort": range(1, len(data)+1), "Mag ich": [", ".join(x) for x in data]}), hide_index=True, use_container_width=True)
                st.info("Bereit für echte Daten? Wechsle links zu „Meine Klasse“ und erstelle einen Klassenraum.")
            else:
                left, right = st.columns([2, 1])
                with left:
                    st.write(f"Teile diesen Klassencode: **{code}**")
                    base = setting("APP_URL").rstrip("/")
                    if base:
                        link = base + "/?" + urlencode({"view": "join", "room": code})
                        st.code(link, language=None)
                        st.link_button("Fragebogen öffnen ↗", link)
                        import qrcode
                        buffer = io.BytesIO()
                        qrcode.make(link).save(buffer, format="PNG")
                        right.image(buffer.getvalue(), caption="Scannen & mitmachen", width=180)
                    else:
                        st.info(f"Setze APP_URL auf die erreichbare App-Adresse, um einen QR-Code zu erzeugen. Fragebogen-Pfad: /?view=join&room={code}")
                    st.caption("Teilnahme auf dem Smartphone; die App-Adresse muss aus dem Schulnetz erreichbar sein.")
                if st.button("Antworten aktualisieren ↻"):
                    st.rerun()
                st.caption(f"Aktuell {len(data)} Antworten · Sammlung {'geöffnet' if room['opened'] else 'geschlossen'}")
                if st.button("Sammlung schließen" if room["opened"] else "Sammlung wieder öffnen"):
                    store.update(code, secret, opened=not room["opened"])
                    st.rerun()
                with st.expander("Verwaltung & Datensicherung"):
                    st.caption("Verwaltungsschlüssel privat sichern. Er erlaubt Zugriff auf Antworten und das Löschen des Raums.")
                    st.text_input("Dein Verwaltungsschlüssel", value=secret, type="password")
                    st.download_button("Antworten als JSON sichern", json.dumps(data, ensure_ascii=False, indent=2), "klassenantworten.json", "application/json")
                    confirm = st.checkbox("Diesen Klassenraum inklusive Antworten und Modell endgültig löschen")
                    if st.button("Klassenraum löschen", disabled=not confirm):
                        store.delete(code, secret)
                        del st.session_state.owner
                        st.rerun()
        elif node == 1:
            st.write("Der Computer braucht Zahlen: Jede Zeile ist eine Antwort, jede Spalte eine Serie. **1 = Ja**, **0 = Nein**. Nein ist vorausgewählt und umfasst auch unbekannte oder nicht bewertete Serien. Es ist kein sicherer Beleg für Abneigung. Das Modell lernt aus gemeinsamem Ja.")
            if data:
                frame = pd.DataFrame(encode(data, catalog))
                st.dataframe(frame.style.map(lambda v: "background-color: #22594f; color: #ffffff" if v else "color: #8290aa"), use_container_width=True, height=320)
                counts = Counter(t for basket in data for t in basket)
                st.markdown("#### Was mag unsere Gruppe?")
                st.bar_chart(pd.DataFrame({"Stimmen": {t: counts[t] for t in catalog}}), color="#7bdaca", horizontal=True)
                st.download_button("0/1-Tabelle herunterladen", frame.to_csv(index=False).encode("utf-8-sig"), "serienmatrix.csv", "text/csv")
            else:
                st.info("Sammelt zuerst Antworten im ersten Knoten.")
        elif node == 2:
            st.write("Wir zählen gemeinsame Vorlieben und lernen Regeln wie **[A, B] → [C]**: Wer **A UND B** mag, mag häufig auch C. Bei der Empfehlung müssen alle Serien links vom Pfeil ausgewählt sein.")
            left, right = st.columns(2)
            support = left.slider("Mindestens so häufig gemeinsam (Support)", 1, 100, 10, format="%d%%", key="support_" + scope)
            confidence = right.slider("Mindestens dieser Anteil mag auch B (Konfidenz)", 1, 100, 50, format="%d%%", key="confidence_" + scope)
            if st.button("✳ Modell lernen" if demo else "✳ Modell lernen & für die Klasse veröffentlichen", type="primary", disabled=not data):
                model = {"rules": train(data, support / 100, confidence / 100), "n": len(data), "fingerprint": fingerprint(data), "support": support, "confidence": confidence, "created": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")}
                if demo:
                    st.session_state.demo_model = model
                else:
                    store.update(code, secret, model=model)
                st.rerun()
            if model:
                if model["fingerprint"] != fingerprint(data):
                    st.warning("Die Antworten haben sich seit dem Training geändert. Erneut lernen, um sie zu berücksichtigen.")
                if (support, confidence) != (model["support"], model["confidence"]):
                    st.info("Die Regler wurden geändert. Klicke auf „Modell lernen“, um die neuen Werte anzuwenden.")
                st.caption(f"Gespeichertes Modell: {model['n']} Antworten · Support ≥ {model['support']} % · Konfidenz ≥ {model['confidence']} %")
                rules = model["rules"]
                if rules:
                    example = next((r for r in rules if isinstance(r['source'], list) and len(r['source']) > 1), rules[0])
                    st.success(f"Beispiel: [{source_label(example)}] → [{example['target']}]")
                    x, y, z = st.columns(3)
                    x.metric("Support · Wie häufig?", f"{example['support']:.0%}")
                    x.caption(f"{example['together']} von {example['total']} Antworten enthalten alle Serien dieser Regel.")
                    y.metric("Konfidenz · Wie verlässlich?", f"{example['confidence']:.0%}")
                    y.caption(f"{example['together']} von {example['source_count']} Personen mit ALLEN Vorlieben links mögen auch die Serie rechts.")
                    z.metric("Lift · Wie besonders?", f"{example['lift']:.2f}×")
                    z.caption("Konfidenz geteilt durch die allgemeine Häufigkeit der Serie rechts. Über 1 bedeutet positiver Zusammenhang.")
                    table = pd.DataFrame([{"Wenn du ALLE magst": source_label(r), "Dann auch": r["target"], "Gemeinsame Stimmen": r["together"], "Support": f"{r['support']:.0%}", "Konfidenz": f"{r['confidence']:.0%}", "Lift": round(r["lift"], 2)} for r in rules])
                    st.dataframe(table, hide_index=True, use_container_width=True)
                    st.download_button("Modell als JSON herunterladen", json.dumps(model, ensure_ascii=False, indent=2), "serienmodell.json", "application/json")
                else:
                    st.info("Keine Regeln erfüllen die Schwellenwerte. Senke die Regler oder sammle mehr Antworten mit gemeinsamen Serien.")
            else:
                st.info("Starte das Lernen, sobald Antworten vorhanden sind.")
            with st.expander("Ist das schon Machine Learning?"):
                st.write("Ja: Die Regeln werden aus Beispielen gelernt, statt einzeln programmiert zu werden. Assoziationsanalyse findet Muster ohne vorgegebene Zielvariable. Hier gibt es keine neuronalen Netze und keine Netflix-Schnittstelle. Netflix verwendet in Wirklichkeit wesentlich komplexere Verfahren.")
                st.write("Eine kleine Klasse ist keine repräsentative Stichprobe. Häufig zusammen heißt nicht Ursache und Wirkung. Für eine echte Qualitätsmessung bräuchten wir zurückgehaltene Testdaten; hier messen wir keine Vorhersagegenauigkeit.")
        else:
            st.write("Jetzt wendest du das gelernte Modell auf eine neue Auswahl an. Bereits gewählte Serien werden ausgeblendet; jede Empfehlung erklärt ihre passende Regel.")
            if model and model["fingerprint"] != fingerprint(data):
                st.warning("Du verwendest den letzten Trainingsstand. Neue Antworten sind noch nicht eingelernt.")
            show_recommendations(model, "likes_" + scope, catalog)
    st.markdown('<div class="footer">✳ SeriesLab · Ein offenes Klassenzimmer für Machine Learning · Unabhängiges Schulprojekt, nicht mit Netflix verbunden.</div>', unsafe_allow_html=True)


def main():
    try:
        store = get_store(setting("DATABASE_URL"))
        if st.query_params.get("view") == "join":
            participant_page(store)
        else:
            lab(store)
    except ValueError as error:
        st.error(str(error))
    except Exception:
        st.error("Die Anwendung konnte die Daten gerade nicht laden oder speichern. Bitte prüfe die Datenbankverbindung und versuche es erneut. Zugangsdaten werden hier nicht angezeigt.")
        if st.button("Erneut versuchen"):
            st.rerun()


if __name__ == "__main__":
    main()
