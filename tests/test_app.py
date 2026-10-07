from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def click(app, label):
    next(button for button in app.button if button.label == label).click().run(timeout=15)
    assert not app.exception
    assert not app.error


def test_entire_path_and_session_persistence():
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert not app.exception
    assert len(app.session_state["dataset"]["users"]) == 300
    click(app, "▦  Likes verstehen")
    assert len(app.dataframe) == 3
    click(app, "⌘  Regeln lernen")
    assert len(app.slider) == 2
    app.slider(key="support").set_value(9).run()
    click(app, "⌘  Regeln mit Apriori lernen")
    assert app.session_state["model"]["rules"]
    click(app, "✦  Feed entdecken")
    assert app.multiselect[0].value == ["P02", "P07"]
    app.selectbox(key="profile").set_value("Rechtes Testprofil").run()
    assert app.multiselect[0].value == ["P04", "P09"]
    click(app, "Stand als Vergleich A merken")
    saved = app.session_state["comparison"]
    click(app, "◉  Daten erzeugen")
    app.slider(key="gen_tendency").set_value(30).run()
    assert app.session_state["dataset"]["settings"]["tendency"] == 0
    assert app.session_state["model"] is not None
    click(app, "↻  Datensatz erzeugen")
    assert app.session_state["dataset"]["settings"]["tendency"] == 30
    assert app.session_state["model"] is None
    assert app.session_state["comparison"] == saved
    click(app, "⌘  Regeln lernen")
    assert app.slider(key="support").value == 9
    click(app, "⌘  Regeln mit Apriori lernen")
    click(app, "✦  Feed entdecken")
    assert app.multiselect[0].value == ["P04", "P09"]
    assert len(app.dataframe) >= 2
    app.multiselect[0].set_value(["P01"]).run()
    assert app.selectbox(key="profile").value == "Eigenes fiktives Profil"
    assert any("unterscheiden" in warning.value for warning in app.warning)
    click(app, "◉  Daten erzeugen")
    assert app.slider(key="gen_tendency").value == 30


def test_sessions_are_isolated_and_no_model_feed_is_explained():
    first = AppTest.from_file(APP).run()
    second = AppTest.from_file(APP).run()
    first.slider(key="gen_tendency").set_value(-80).run()
    click(first, "↻  Datensatz erzeugen")
    assert second.session_state["dataset"]["settings"]["tendency"] == 0
    click(second, "✦  Feed entdecken")
    assert any("Zuerst" in info.value for info in second.info)
    assert not second.text_input


def test_no_rules_and_empty_profile_are_valid_outcomes():
    app = AppTest.from_file(APP).run()
    click(app, "⌘  Regeln lernen")
    app.slider(key="support").set_value(50)
    app.slider(key="confidence").set_value(100).run()
    click(app, "⌘  Regeln mit Apriori lernen")
    assert app.session_state["model"]["rules"] == []
    click(app, "✦  Feed entdecken")
    assert any("Keine passende Empfehlung" in info.value for info in app.info)
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("mindestens einen Like" in info.value for info in app.info)
