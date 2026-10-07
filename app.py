"""FeedLab: mobiles Lernlabor mit ausschließlich synthetischen Daten."""
import inspect
import json
from collections import Counter
from dataclasses import asdict
from html import escape

import pandas as pd
import streamlit as st

from feedlab.catalog import CATALOG, POSTS, POST_BY_ID, POSITIONS, PROFILES, post_label
from feedlab.model import (encode, train, recommend, recommend_diverse,
                           matching_rules, antecedents, source_label)
from feedlab.synthetic import Settings, generate, transactions, dataset_id

st.set_page_config(page_title="FeedLab · Wer formt deinen Feed?", page_icon="✕", layout="centered",
                   initial_sidebar_state="collapsed")
st.html("""<style>
:root{color-scheme:dark}.stApp{background:#08090b}
.block-container{max-width:790px;padding:1.1rem 1.35rem 4rem}
header[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stToolbar"]{display:none}
h1{font-size:3.3rem!important;line-height:1.04!important;letter-spacing:-.065em;padding-top:.4rem!important}
h2{font-size:1.55rem!important;letter-spacing:-.04em}h3{font-size:1.14rem!important}
p{line-height:1.6}button{touch-action:manipulation}
[data-testid="stBaseButton-primary"],[data-testid="stBaseButton-secondary"]{min-height:46px;border-radius:24px;font-weight:650}
[data-testid="stBaseButton-primary"]{color:#fff!important}
[data-testid="stMetric"]{padding:12px 14px;border:1px solid #292d34;border-radius:14px;background:#101216}
[data-testid="stMetricValue"]{font-size:1.6rem}[data-testid="stMetricLabel"]{color:#8c98a5;font-size:.76rem}
[data-testid="stTabs"] button{min-height:44px}[data-testid="stExpander"]{border-color:#292d34;border-radius:14px}
.topbar{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #272b32;padding:8px 0 20px;margin-bottom:24px}
.brand{font-size:1.4rem;font-weight:800;letter-spacing:-.06em}.brand b{font-size:1.85rem;margin-right:12px}.brand span{font-weight:400;color:#7c8794}
.lab-label{font-size:.66rem;letter-spacing:.14em;color:#8c98a5;border:1px solid #303640;padding:7px 10px;border-radius:20px}
.kicker{color:#1d9bf0;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.hero-sub{color:#929ca9;font-size:1rem;max-width:550px;line-height:1.7;margin:10px 0 22px}
.blue{color:#1d9bf0}.tag{color:#7cbbeb;font-size:.73rem;background:#0d2231;padding:4px 9px;border-radius:5px;display:inline-block;margin:3px 4px 3px 0}
.steps{font-size:.72rem;color:#8995a2;margin-bottom:10px;letter-spacing:.04em}
.post{border-bottom:1px solid #282c32;padding:20px 4px;overflow-wrap:anywhere}
.post-head{display:flex;gap:11px;align-items:center;margin-bottom:10px}.avatar{width:39px;height:39px;flex-shrink:0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:800;background:#172f42;color:#80c4ff;font-size:.85rem}
.post-author{font-size:.88rem;font-weight:700}.post-handle{font-size:.76rem;color:#7f8c98}.post-text{font-size:1rem;line-height:1.65;color:#e7e9ea;margin:8px 0 12px}
.post-meta{display:flex;justify-content:space-between;gap:8px;color:#7f8c98;font-size:.73rem;margin-top:13px}
.reason{border-left:2px solid #1d9bf0;background:#101b24;padding:11px 13px;margin-top:14px;font-size:.8rem;color:#b2d2ea;line-height:1.7}
.spectrum{height:5px;border-radius:6px;background:linear-gradient(90deg,#b085f5,#748fec,#82909f,#5ba6b4,#e5a169);margin:9px 0}
.spectrum-labels{display:flex;justify-content:space-between;font-size:.72rem;color:#8b98a5;margin-bottom:20px}
.footer{color:#74808d;border-top:1px solid #262a30;margin-top:30px;padding-top:18px;font-size:.73rem;line-height:1.7}
@media(max-width:600px){.block-container{padding:1rem .8rem 3rem}h1{font-size:2.4rem!important;margin:8px 0!important}.topbar{margin-bottom:12px}.lab-label{font-size:.58rem;padding:6px 8px}
.hero-sub{font-size:.9rem;margin:8px 0 12px}[data-testid="stVerticalBlock"]{gap:.7rem}
[data-testid="stHorizontalBlock"]{gap:.5rem;flex-wrap:nowrap!important}
[data-testid="stColumn"]{min-width:0!important;flex:1 1 0!important;width:0!important}
[data-testid="stMetric"]{padding:10px 7px}[data-testid="stMetricValue"]{font-size:1.3rem}[data-testid="stMetricLabel"]{font-size:.65rem}
[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{font-size:.8rem;padding:.5rem .6rem}
.post-text{font-size:.95rem}.post{padding:17px 2px}}
</style>""")

STEPS = ["◉  Mission", "▦  Experiment", "⌘  Muster erklären", "✦  Feed gestalten"]


def go(step):
    st.session_state.step = step


def defaults():
    if "dataset" not in st.session_state:
        st.session_state.dataset = generate(Settings())
        st.session_state.model = None
        st.session_state.step = 0
        st.session_state.feed_likes = list(PROFILES["Linkes Testprofil"])
    # Widgets verschwinden beim Schrittwechsel. Werte dennoch sitzungsweit halten.
    for key, value in asdict(Settings()).items():
        widget = "gen_" + key
        st.session_state[widget] = st.session_state.get(widget, value)
    for key, value in {"support": 8, "confidence": 55, "profile": "Linkes Testprofil",
                       "feed_likes": list(PROFILES["Linkes Testprofil"])}.items():
        st.session_state[key] = st.session_state.get(key, value)


def post_card(post_id, counts=None, rule=None):
    post = POST_BY_ID[post_id]
    count = counts.get(post_id, 0) if counts is not None else None
    like_meta = f"♡ {count} synthetische Likes" if count is not None else "✦ Feed-Kandidat"
    explanation = ""
    if rule:
        names = " UND ".join(post_label(pid) for pid in antecedents(rule))
        explanation = (f'<div class="reason"><b>Weil das Testprofil {escape(names)} gelikt hat</b><br>'
                       f'{rule["together"]} von {rule["source_count"]} simulierten Personen mit diesen Likes '
                       f'liken auch diesen Post.<br>Konfidenz {rule["confidence"]:.0%} · '
                       f'Support {rule["support"]:.0%} · Lift {rule["lift"]:.2f}</div>')
    st.html(f'<article class="post"><div class="post-head"><div class="avatar">{post_id}</div>'
            f'<div><div class="post-author">{post["author"]} <span class="blue">✧</span></div>'
            f'<div class="post-handle">@{post["handle"]} · fiktiver Account</div></div></div>'
            f'<div class="post-text">{escape(post["text"])}</div>'
            f'<span class="tag">#{post["topic"]}</span><span class="tag">{post["label"]} · Modell-Tag</span>'
            f'<div class="post-meta"><span>{like_meta}</span><span>{post_id} · Simulation</span></div>'
            f'{explanation}</article>')


def code_panel(*functions):
    with st.expander("Python hinter diesem Schritt"):
        st.caption("Tatsächlicher Quellcode. Das Lernen übernimmt mlxtend, nicht ein selbst geschriebener Lernalgorithmus.")
        for function in functions:
            st.code(inspect.getsource(function), language="python")


@st.cache_data
def opening_comparison():
    likes = list(PROFILES["Linkes Testprofil"])
    scenarios = []
    for title, tendency in [("Community A", -70), ("Community B", 70)]:
        dataset = generate(Settings(tendency=tendency, seed=42))
        rules = train(transactions(dataset), .08, .55)
        scenarios.append({"title": title, "tendency": tendency,
                          "feed": [rule["target"] for rule in recommend(likes, rules)]})
    return likes, scenarios


def mission_page():
    likes, scenarios = opening_comparison()
    st.markdown("## Gleiche Likes. Anderer Feed.")
    st.write("Du arbeitest im Produktteam einer Social-Media-Plattform. Ein fiktives Profil hat in beiden Szenarien exakt dieselben Posts gelikt:")
    st.write(" · ".join(post_label(pid) for pid in likes))
    choice = st.radio("Was erwartest du?", ["Beide Feeds sind gleich", "Die Feeds unterscheiden sich"],
                      index=None, key="opening_prediction")
    if st.button("Feeds vergleichen", type="primary", width="stretch"):
        st.session_state.opening_revealed = True
    if st.session_state.get("opening_revealed"):
        if choice is None:
            st.caption("Du kannst zuerst eine Vermutung wählen — der Vergleich ist trotzdem sichtbar.")
        elif choice == "Die Feeds unterscheiden sich":
            st.success("Deine Vermutung passt zu diesem Simulationslauf.")
        else:
            st.info("Überraschung: Die Likes des Profils sind gleich, aber die gelernten Umgebungen unterscheiden sich.")
        tabs = st.tabs([scenario["title"] for scenario in scenarios])
        for tab, scenario in zip(tabs, scenarios):
            with tab:
                st.caption(f"Politische Tendenz der fiktiven Trainingscommunity: {scenario['tendency']:+d}")
                for pid in scenario["feed"]:
                    post_card(pid)
        st.markdown("### Deine Mission")
        st.write("Finde heraus, **warum** derselbe Ausgangspunkt zu anderen Empfehlungen führt. Entscheide danach, ob deine Plattform nur geschätzte Relevanz oder zusätzlich Perspektivenvielfalt berücksichtigen soll.")
        st.button("Mission starten →", on_click=go, args=(1,), type="primary", width="stretch")
    else:
        st.caption("Die Daten sind vollständig synthetisch. Deine Auswahl wird nicht gespeichert und sagt nichts über deine politische Haltung aus.")


def generator_page():
    st.markdown("## Verändere genau eine Annahme.")
    st.write("Simuliere eine Bevölkerung, die 20 politische Posts sieht. Für einen sauberen Vergleich lässt du Seed, Testprofil und Lernschwellen gleich und veränderst zunächst nur die politische Tendenz.")
    st.radio("Deine Vorhersage vor dem Experiment", [
        "Der Feed verschiebt sich in Richtung der Community",
        "Der Feed bleibt weitgehend gleich",
        "Ich bin unsicher"
    ], index=None, key="experiment_hypothesis")
    st.slider("Politische Tendenz der Bevölkerung", -100, 100, key="gen_tendency",
              help="Verschiebt das Zentrum der erzeugten Positionen. −100 = stark links, +100 = stark rechts. Kein Wert über dich.")
    st.html('<div class="spectrum"></div><div class="spectrum-labels"><span>−100 · stark links</span><span>0 · Mitte</span><span>+100 · stark rechts</span></div>')
    st.slider("Polarisierung", 0, 100, key="gen_polarization", format="%d %%",
              help="0: eine Gruppe nahe dem Zentrum. 100: zwei weit auseinanderliegende Gruppen. Die Tendenz verschiebt beide.")
    st.slider("Vorliebe für ähnliche Positionen", 0, 100, key="gen_similarity", format="%d %%",
              help="0: politische Nähe hat keinen Einfluss auf Likes. 100: ähnliche Positionen werden deutlich wahrscheinlicher gelikt. Themeninteressen und Zufall bleiben erhalten.")
    st.slider("Like-Aktivität", 0, 100, key="gen_activity", format="%d %%",
              help="Regelt die allgemeine Neigung zu liken, nicht den exakten Anteil gelikter Posts.")
    with st.expander("Datengröße & Reproduzierbarkeit"):
        st.slider("Fiktive Personen", 50, 1000, step=50, key="gen_users")
        st.number_input("Zufallsstartwert (Seed)", min_value=0, max_value=999999, step=1, key="gen_seed")
        st.caption("Gleiche Einstellungen und gleicher Seed ergeben dieselben Daten. Halte den Seed beim Vergleich konstant.")
    settings = Settings(**{key: st.session_state["gen_" + key] for key in asdict(Settings())})
    pending = asdict(settings) != st.session_state.dataset["settings"]
    if pending:
        st.info("Regler geändert. Der bisherige Datensatz bleibt aktiv, bis du neu erzeugst.")
    if st.button("↻  Datensatz erzeugen", type="primary", width="stretch"):
        st.session_state.dataset = generate(settings)
        st.session_state.model = None
        st.session_state.generated = True
        st.rerun()
    if st.session_state.get("generated") and not pending:
        st.success("Datensatz erzeugt. Erkunde die Likes und lerne anschließend neue Regeln.")
    st.caption("Neue Daten ersetzen nur dein Sitzungsexperiment und setzen das gelernte Modell zurück. Ein gespeicherter Vergleich bleibt erhalten.")
    with st.expander("Warum viele Personen und dieselben Posts?"):
        st.write("Eine Person mit vielen Posts liefert nur eine Transaktion. Um gemeinsame Vorlieben zu erkennen, brauchen wir viele unabhängige Like-Sammlungen. Deshalb sieht jede fiktive Person denselben festen Katalog: 4 Themen × 5 Positionen = 20 Posts.")
        st.write("Politische Nähe, persönliche Themeninteressen, Aktivität und Zufall bestimmen die Like-Chance. Die Regler sind Annahmen unserer Simulation, keine Messwerte über X. Nicht-Likes werden nicht als politische Ablehnung interpretiert.")
    code_panel(generate)


def data_page(dataset, counts, embedded=False):
    if not embedded:
        st.markdown("## Ein Like ist noch kein Muster.")
    st.write("**1 Transaktion = 1 fiktive Person.** Die Items sind die IDs ihrer gelikten Posts. Politische Tags erklären die Simulation; das Lernverfahren sieht ausschließlich Post-Likes.")
    tab_people, tab_posts, tab_matrix = st.tabs(["Personen", "Posts", "0/1-Matrix"])
    with tab_people:
        users = dataset["users"]
        bins = pd.cut(pd.Series([u["position"] for u in users]), [-1.01, -.6, -.2, .2, .6, 1.01], labels=list(POSITIONS.values()))
        st.caption("Tatsächlich erzeugte Verteilung — die Regler sind keine Garantie für exakt gleiche Gruppengrößen.")
        st.bar_chart(bins.value_counts(sort=False).rename("Personen"), color="#1d9bf0")
        user_id = st.selectbox("Eine fiktive Person ansehen", [u["user"] for u in users])
        user = next(u for u in users if u["user"] == user_id)
        st.write(f"**{user_id}** · simulierte Position **{user['position']:+.2f}** · **{len(user['likes'])} Likes**")
        st.code("{ " + ", ".join(user["likes"]) + " }" if user["likes"] else "{ } — leere Transaktion", language=None)
        st.dataframe(pd.DataFrame([{"Post": post_label(pid), "Like-Chance": f"{user['probabilities'][pid]:.0%}",
                                    "Zufallsergebnis": "♥ Like" if pid in user["likes"] else "Kein Like"} for pid in CATALOG]),
                     hide_index=True, width="stretch", height=290)
        st.caption("Eine Chance von 70 % garantiert keinen Like. Der Seed steuert den Zufall. Positionen und Chancen sind nur zur Kontrolle des Generators sichtbar.")
        with st.expander("Alle Transaktionen einsehen"):
            st.dataframe(pd.DataFrame([{"Person": u["user"], "Position": round(u["position"], 2), "Likes": ", ".join(u["likes"])} for u in users]), hide_index=True, width="stretch")
    with tab_posts:
        topic = st.selectbox("Thema filtern", ["Alle Themen"] + list(dict.fromkeys(p["topic"] for p in POSTS)))
        st.caption("Alle Texte, Accounts und politischen Zuordnungen sind erfunden. Die eindimensionale Achse ist eine didaktische Vereinfachung, keine Einordnung realer Parteien oder Menschen.")
        for post in POSTS:
            if topic == "Alle Themen" or post["topic"] == topic:
                post_card(post["id"], counts)
    with tab_matrix:
        frame = pd.DataFrame(encode(transactions(dataset)), index=[u["user"] for u in dataset["users"]])
        st.caption("1 = Like, 0 = kein Like. Auf dem Smartphone lässt sich die Tabelle seitlich scrollen. Auch leere Transaktionen zählen im Nenner des Supports.")
        st.dataframe(frame, width="stretch", height=340)
        st.download_button("↓  Matrix als CSV", frame.to_csv().encode("utf-8-sig"), "feedlab-matrix.csv", "text/csv")
    st.download_button("↓  Gesamten synthetischen Datensatz herunterladen", json.dumps(dataset, ensure_ascii=False, indent=2), "feedlab-daten.json", "application/json")
    code_panel(encode)
    if not embedded:
        st.button("Weiter: Regeln lernen →", on_click=go, args=(2,), width="stretch")


def rules_page(dataset):
    st.markdown("## Warum verändert sich der Feed?")
    st.write("**[P01 UND P06] → P11** heißt: Personen, die beide Posts links liken, liken häufig auch den Post rechts. Das ist ein beobachteter Zusammenhang in unseren künstlichen Daten.")
    support = st.slider("Mindest-Support", 1, 50, format="%d %%", key="support")
    st.caption("Wie viel Prozent aller simulierten Personen haben sämtliche Posts einer Regel gelikt?")
    confidence = st.slider("Mindest-Konfidenz", 10, 100, format="%d %%", key="confidence")
    st.caption("Wie viele Personen mit ALLEN Likes links haben auch den Post rechts gelikt?")
    model = st.session_state.model
    if model and (support, confidence) != (model["support"], model["confidence"]):
        st.info("Schwellen geändert. Erst erneutes Lernen wendet sie auf das Modell an.")
    if st.button("⌘  Regeln mit Apriori lernen", type="primary", width="stretch"):
        with st.spinner("mlxtend sucht häufige Kombinationen …"):
            st.session_state.model = {"rules": train(transactions(dataset), support / 100, confidence / 100),
                                      "dataset_id": dataset_id(dataset), "support": support, "confidence": confidence}
        st.rerun()
    model = st.session_state.model
    if model is None:
        st.info("Der Datensatz ist bereit. Starte das Lernen, um die Ergebnisse zu sehen.")
    elif not model["rules"]:
        st.info("Keine Regeln gefunden. Senke Support oder Konfidenz oder erhöhe die Like-Aktivität. Es werden keine Regeln erfunden.")
    else:
        rules = model["rules"]
        st.success(f"{len(rules):,} Regeln gelernt · {sum(len(antecedents(r)) > 1 for r in rules):,} mit mehreren Voraussetzungen".replace(",", "."))
        st.caption(f"Trainingsstand: Support ≥ {model['support']} % · Konfidenz ≥ {model['confidence']} %")
        combined_only = st.checkbox("Nur Kombinationsregeln zeigen")
        filtered = [r for r in rules if not combined_only or len(antecedents(r)) > 1]
        if filtered:
            index = st.selectbox("Eine Regel untersuchen", range(len(filtered)),
                                format_func=lambda i: f"[{source_label(filtered[i])}] → {filtered[i]['target']}")
            rule = filtered[index]
            st.markdown(f"### [{source_label(rule)}] → {rule['target']}")
            st.write("**Wenn:** " + " UND ".join(post_label(pid) for pid in antecedents(rule)))
            st.write("**Dann:** " + post_label(rule["target"]))
            a, b = st.columns(2)
            a.metric("Wie häufig?", f"{rule['support']:.0%}")
            b.metric("Wie zuverlässig im Datensatz?", f"{rule['confidence']:.0%}")
            st.write(f"**{rule['together']} von {rule['total']}** Personen liken alle Posts dieser Regel. **{rule['together']} von {rule['source_count']}** Personen mit den Likes links liken auch den Zielpost.")
            with st.expander("Vertiefung: Lift und Regeltabelle"):
                st.metric("Lift", f"{rule['lift']:.2f}×")
                st.caption("Lift = Konfidenz / allgemeiner Like-Anteil des Zielposts. Über 1 bedeutet: häufiger als ohne Kenntnis der Voraussetzungen zu erwarten. Das ist keine Ursache-Wirkungs-Aussage.")
                st.dataframe(pd.DataFrame([{"Wenn ALLE": source_label(r), "Dann": r["target"], "Support": round(r["support"], 3),
                                           "Konfidenz": round(r["confidence"], 3), "Lift": round(r["lift"], 2)} for r in filtered]), hide_index=True, width="stretch")
        else:
            st.info("Bei diesen Schwellen gibt es nur Einzelregeln.")
        st.download_button("↓  Modell herunterladen", json.dumps(model, ensure_ascii=False, indent=2), "feedlab-modell.json", "application/json")
    with st.expander("Was das Modell weiß — und was nicht"):
        st.write("Apriori sieht nur die 0/1-Likes. Texte, politische Positionen und Themen gehen nicht als Merkmale ins Training ein. Gleichgerichtete Empfehlungen können trotzdem entstehen, weil wir entsprechende Like-Muster in den Generator eingebaut haben.")
        st.write("Das ist nicht der echte X-Algorithmus. Keine Aussage über tatsächliche politische Bündnisse oder das Verhalten realer Menschen. Konfidenz im Training ist keine auf neuen Personen gemessene Trefferquote.")
    code_panel(train)
    st.button("Weiter: Plattform gestalten →", on_click=go, args=(3,), width="stretch")


def select_profile():
    if st.session_state.profile != "Eigenes fiktives Profil":
        st.session_state.feed_likes = list(PROFILES[st.session_state.profile])


def custom_profile():
    st.session_state.profile = "Eigenes fiktives Profil"


def feed_metrics(results):
    if not results:
        return {"confidence": 0, "perspectives": 0, "spread": 0}
    positions = [POST_BY_ID[rule["target"]]["position"] for rule in results]
    return {
        "confidence": sum(rule["confidence"] for rule in results) / len(results),
        "perspectives": len({POST_BY_ID[rule["target"]]["label"] for rule in results}),
        "spread": max(positions) - min(positions),
    }


def feed_page(dataset, counts):
    st.markdown("## Du entscheidest, was der Feed optimiert.")
    st.write("Du bist jetzt im Produktteam. Soll die Plattform nur die stärksten gelernten Regeln nutzen — oder bewusst unterschiedliche Modell-Perspektiven in die Rangfolge einbeziehen?")
    st.selectbox("Testprofil", list(PROFILES) + ["Eigenes fiktives Profil"], key="profile", on_change=select_profile)
    selected = st.multiselect("Bisherige Likes des Testprofils", CATALOG, format_func=post_label, key="feed_likes", on_change=custom_profile)
    st.caption("Das sind Rollen im Experiment, keine Frage nach deiner politischen Haltung. Diese Auswahl verändert die Trainingsdaten nicht.")
    with st.expander("Die gelikten Posts lesen"):
        for pid in selected:
            post_card(pid, counts)
        if not selected:
            st.write("Noch keine Likes ausgewählt.")
    model = st.session_state.model
    if model is None:
        st.info("Zuerst im dritten Schritt Regeln lernen. Dann kann der Feed das Modell anwenden.")
        st.button("Zum Lernen →", on_click=go, args=(2,), width="stretch")
        return
    matches = matching_rules(selected, model["rules"])
    results = recommend(selected, model["rules"])
    positions = {pid: POST_BY_ID[pid]["position"] for pid in CATALOG}
    diverse_results = recommend_diverse(selected, model["rules"], positions)
    st.caption(f"{len(matches)} passende Regeln · davon {sum(len(antecedents(r)) > 1 for r in matches)} Kombinationsregeln · maximal 6 neue Posts")
    relevance_tab, diversity_tab, why_tab = st.tabs(["Nur Relevanz", "Mit Perspektivenvielfalt", "So entscheidet das System"])
    with relevance_tab:
        if not selected:
            st.info("Wähle mindestens einen Like für das Testprofil.")
        elif not results:
            st.info("Keine passende Empfehlung mit Lift über 1. Andere fiktive Likes oder andere Trainingsschwellen können das ändern.")
        for rule in results:
            post_card(rule["target"], counts, rule)
    with diversity_tab:
        st.caption("Dieselben Regelkandidaten, andere Rangfolge: 70 % Konfidenz + 30 % Abstand zu bereits ausgewählten Modell-Positionen.")
        if not diverse_results:
            st.info("Keine passenden Kandidaten für dieses Testprofil.")
        for rule in diverse_results:
            post_card(rule["target"], counts, rule)
    with why_tab:
        st.write("**Gemeinsamer Kandidatenpool:** Alle Likes links müssen gewählt sein (UND). Bereits gelikte Zielposts und Regeln mit Lift ≤ 1 werden ausgeschlossen.")
        st.write("**Nur Relevanz:** Konfidenz zuerst, danach Support und Lift. Pro Zielpost zählt die bestplatzierte Regel.")
        st.write("**Mit Perspektivenvielfalt:** Das Lab kombiniert 70 % Konfidenz mit 30 % Abstand zu bereits ausgewählten politischen Modell-Tags. Diese Gewichtung ist eine Produktentscheidung, kein von den Daten gelernter Wert.")
        if matches:
            st.dataframe(pd.DataFrame([{"Wenn ALLE": source_label(r), "Dann": r["target"], "Konfidenz": f"{r['confidence']:.0%}",
                                       "Support": f"{r['support']:.0%}", "Lift": round(r["lift"], 2)} for r in matches]), hide_index=True, width="stretch")
    if results:
        st.markdown("### Der Zielkonflikt")
        rel, div = feed_metrics(results), feed_metrics(diverse_results)
        st.dataframe(pd.DataFrame([
            {"Strategie": "Nur Relevanz", "Ø Konfidenz": f"{rel['confidence']:.0%}", "Perspektiv-Tags": rel["perspectives"], "Spannweite": f"{rel['spread']:.1f}"},
            {"Strategie": "Mit Perspektivenvielfalt", "Ø Konfidenz": f"{div['confidence']:.0%}", "Perspektiv-Tags": div["perspectives"], "Spannweite": f"{div['spread']:.1f}"},
        ]), hide_index=True, width="stretch")
        decision = st.radio("Welche Strategie würdest du als Produktteam einsetzen?", [
            "Nur Relevanz",
            "Mit Perspektivenvielfalt",
            "Noch keine Entscheidung — mir fehlen Messwerte"
        ], index=None, key="product_decision")
        if decision:
            st.info("Wirtschaftsinformatik heißt hier: Ziele festlegen, Daten und Technik gestalten, Auswirkungen messen und Entscheidungen begründen. Für eine reale Entscheidung bräuchten wir zusätzlich Nutzungs-, Qualitäts- und Fairnessmetriken.")
    if results:
        st.markdown("### Wie einseitig ist dieser Ausschnitt?")
        mean = sum(POST_BY_ID[r["target"]]["position"] for r in results) / len(results)
        st.metric("Mittlere Modell-Position im Feed", f"{mean:+.2f}")
        st.caption("−1 = stark links, +1 = stark rechts. Ungewichteter Mittelwert der fest vergebenen Tags, keine Messung deiner Haltung. Die Mitte kann sowohl mittige als auch gegensätzliche Posts bedeuten.")
        distribution = Counter(POST_BY_ID[r["target"]]["label"] for r in results)
        st.bar_chart(pd.Series({label: distribution[label] for label in POSITIONS.values()}, name="Empfohlene Posts"), color="#1d9bf0")
    st.markdown("### Szenarienvergleich A ↔ B")
    st.caption("Dies ist kein randomisierter A/B-Test. Speichere ein Simulationsszenario, ändere genau eine Annahme, erzeuge neu und lerne erneut. Test-Likes, Seed und Lernschwellen bleiben dabei gleich.")
    if st.button("Szenario A merken", disabled=not results, width="stretch"):
        st.session_state.comparison = {"settings": dataset["settings"], "dataset_id": dataset_id(dataset),
                                       "support": model["support"], "confidence": model["confidence"],
                                       "likes": list(selected), "feed": [r["target"] for r in results]}
        st.success("Stand A ist für diese Sitzung gespeichert.")
    saved = st.session_state.get("comparison")
    if saved:
        if set(saved["likes"]) != set(selected) or (saved["support"], saved["confidence"]) != (model["support"], model["confidence"]):
            st.warning("Test-Likes oder Lernschwellen unterscheiden sich von A. Unterschiede im Feed sind nicht allein auf den Datengenerator zurückzuführen.")
        before, after = saved["feed"], [r["target"] for r in results]
        st.dataframe(pd.DataFrame({"Rang": range(1, max(len(before), len(after)) + 1),
                                   "A · gespeichert": [post_label(pid) for pid in before] + ["—"] * max(0, len(after)-len(before)),
                                   "B · aktuell": [post_label(pid) for pid in after] + ["—"] * max(0, len(before)-len(after))}), hide_index=True, width="stretch")
        with st.expander("Einstellungen A und B vergleichen"):
            labels = {"tendency": "Tendenz", "polarization": "Polarisierung", "similarity": "Ähnlichkeitsliebe", "activity": "Aktivität", "users": "Personen", "seed": "Seed"}
            st.table(pd.DataFrame([{"Parameter": label, "A": saved["settings"][key], "B": dataset["settings"][key]} for key, label in labels.items()]))
        st.download_button("↓  Experimentvergleich herunterladen", json.dumps({"A": saved, "B": {"settings": dataset["settings"], "dataset_id": dataset_id(dataset), "support": model["support"], "confidence": model["confidence"], "likes": selected, "feed": after}}, ensure_ascii=False, indent=2), "feedlab-vergleich.json", "application/json")
    with st.expander("Drei Fragen für dein Experiment"):
        st.write("1. Halte das Testprofil fest und verschiebe nur die Bevölkerung nach links oder rechts. Ändert sich der Feed?")
        st.write("2. Setze die Vorliebe für ähnliche Positionen auf 0. Welche Muster bleiben durch Themeninteressen und Zufall trotzdem bestehen?")
        st.write("3. Ändere nur den Seed. Welche scheinbar sicheren Regeln verschwinden? Was sagt das über eine kleine Stichprobe?")
        st.caption("Wir simulieren eine einzige Empfehlungsrunde. Eine Filterblase über mehrere Runden oder eine Veränderung politischer Überzeugungen wird damit nicht nachgewiesen.")
    code_panel(matching_rules, recommend, recommend_diverse)


def main():
    defaults()
    st.html('<div class="topbar"><div class="brand"><b>✕</b>Feed<span>Lab</span></div><div class="lab-label">SOCIAL ALGORITHM LAB</div></div>')
    if st.session_state.step == 0:
        st.html('<div class="kicker">Deine Mission im Produktteam</div><h1>Gleiche Likes.<br>Anderer <span class="blue">Feed?</span></h1><div class="hero-sub">Ein Empfehlungssystem ist nicht nur Code. Daten, Ziele und Produktentscheidungen bestimmen, was Menschen sehen.</div>')
    else:
        st.html('<div class="kicker">Dein Experiment · 100 % synthetisch</div>')
    dataset = st.session_state.dataset
    data = transactions(dataset)
    counts = Counter(pid for row in data for pid in row)
    a, b, c = st.columns(3)
    a.metric("Fiktive Personen", len(data))
    b.metric("Likes", sum(counts.values()))
    c.metric("Posts", len(POSTS))
    st.write("")
    st.html('<div class="steps">DEIN LERNPFAD · JEDER SCHRITT IST KLICKBAR</div>')
    for row in (0, 2):
        columns = st.columns(2)
        for i in range(row, row + 2):
            columns[i-row].button(STEPS[i], key=f"step_{i}", type="primary" if st.session_state.step == i else "secondary",
                                  width="stretch", on_click=go, args=(i,))
    st.caption(f"Schritt {st.session_state.step + 1} von 4 · Datensatz {dataset_id(dataset)} · Seed {dataset['settings']['seed']}")
    st.divider()
    if st.session_state.step == 0:
        mission_page()
    elif st.session_state.step == 1:
        experiment_tab, data_tab = st.tabs(["Experiment steuern", "Vertiefung: Daten ansehen"])
        with experiment_tab:
            generator_page()
        with data_tab:
            data_page(dataset, counts, embedded=True)
        st.button("Weiter: Muster erklären →", on_click=go, args=(2,), type="primary", width="stretch")
    elif st.session_state.step == 2:
        rules_page(dataset)
    else:
        feed_page(dataset, counts)
    st.html('<div class="footer">✕ FeedLab · Unabhängiges Lehrprojekt, nicht mit X verbunden.<br>100 % synthetische Profile und Posts. Keine Anmeldung, keine Befragung, keine Datenbank. Experimente liegen nur im flüchtigen Sitzungsspeicher; ein Neuladen kann sie zurücksetzen. Hostinganbieter können technische Verbindungsprotokolle führen.</div>')


if __name__ == "__main__":
    main()
