from pathlib import Path
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception
    assert not app.error


def test_demo_from_data_to_prediction():
    app = AppTest.from_file(APP).run()
    assert not app.exception
    assert not app.error
    click(app, "▦ Daten verstehen")
    assert len(app.dataframe) == 1
    click(app, "✳ Regeln lernen")
    click(app, "✳ Modell lernen")
    assert app.session_state["demo_model"]["rules"]
    click(app, "✧ Serien empfehlen")
    app.multiselect[0].select("Stranger Things").run()
    assert not app.error
    assert not app.exception
    app.multiselect[0].select("Wednesday").run()
    assert any("Kombinationsregel:" in item.value and "Cobra Kai" in item.value for item in app.markdown)
    assert not app.error


def test_unknown_classroom():
    app = AppTest.from_file(APP)
    app.query_params["view"] = "join"
    app.query_params["room"] = "UNKNOWN"
    app.run()
    assert not app.exception
    assert not app.error
    assert any("Klassencode" in info.value for info in app.info)


def test_teacher_survey_publish_and_student_prediction(monkeypatch, tmp_path):
    from serieslab.storage import Store
    import streamlit as st
    original = Store.__init__
    monkeypatch.setattr(Store, "__init__", lambda self, url="": original(self, path=str(tmp_path / "class.sqlite")))
    monkeypatch.setenv("TEACHER_PASSWORD", "Lehrkräft-Passwort-äöü")
    monkeypatch.setenv("APP_URL", "https://example.streamlit.app")
    st.cache_resource.clear()
    teacher = AppTest.from_file(APP).run()
    teacher.radio[0].set_value("Meine Klasse").run()
    teacher.text_input[0].set_value("wrong")
    next(button for button in teacher.button if button.label == "Neuen Klassenraum erstellen").click().run()
    assert any("stimmt nicht" in error.value for error in teacher.error)
    teacher.text_input[0].set_value("Lehrkräft-Passwort-äöü")
    click(teacher, "Neuen Klassenraum erstellen")
    code, secret = teacher.session_state["owner"]
    store = Store()
    student = AppTest.from_file(APP)
    student.query_params.update({"view": "join", "room": code})
    student.run()
    assert len(student.radio) == 20
    assert all(radio.value is None for radio in student.radio)
    click(student, "Meine Vorlieben teilen →")
    assert store.transactions(code, secret) == []
    assert student.warning
    for radio in student.radio:
        radio.set_value("Ja" if radio.label.split(" · ", 1)[1] in ["Wednesday", "Stranger Things"] else "Nein")
    student.checkbox[0].check()
    click(student, "Meine Vorlieben teilen →")
    assert store.transactions(code, secret) == [["Stranger Things", "Wednesday"]]
    for radio in student.radio:
        radio.set_value("Nein")
    click(student, "Meine Vorlieben teilen →")
    assert store.transactions(code, secret) == [[]]
    for radio in student.radio:
        radio.set_value("Ja" if radio.label.split(" · ", 1)[1] in ["Wednesday", "Stranger Things"] else "Nein")
    click(student, "Meine Vorlieben teilen →")
    assert len(store.transactions(code, secret)) == 1
    store.submit(code, "second-student", ["One Piece"])
    click(teacher, "Antworten aktualisieren ↻")
    click(teacher, "Sammlung schließen")
    click(teacher, "✳ Regeln lernen")
    click(teacher, "✳ Modell lernen & für die Klasse veröffentlichen")
    assert store.room(code)["model"]["n"] == 2
    click(student, "Veröffentlichtes Modell aktualisieren")
    student.multiselect[0].set_value(["Wednesday"]).run()
    assert not student.error
    assert not student.exception
    assert any("Konfidenz 100%" in caption.value for caption in student.caption)
    st.cache_resource.clear()
