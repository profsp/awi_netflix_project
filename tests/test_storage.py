from concurrent.futures import ThreadPoolExecutor
import pytest
from serieslab.storage import Store


def test_room_lifecycle_and_isolation(tmp_path):
    store = Store(path=str(tmp_path / "test.sqlite"))
    code, secret = store.create_room()
    other, other_secret = store.create_room()
    assert store.authorized(code, secret)
    assert not store.authorized(code, "wrong")
    store.submit(code, "person", ["Wednesday"])
    store.submit(code, "person", ["One Piece"])
    assert store.transactions(code, secret) == [["One Piece"]]
    assert store.transactions(other, other_secret) == []
    with pytest.raises(ValueError):
        store.transactions(code, other_secret)
    with pytest.raises(ValueError):
        store.update(code, "wrong", opened=False)
    with pytest.raises(ValueError):
        store.submit(code, "bad", ["not in catalog"])
    store.update(code, secret, opened=False, model={"rules": [], "n": 1})
    assert store.room(code)["model"]["n"] == 1
    with pytest.raises(ValueError):
        store.submit(code, "new", ["Wednesday"])
    store.delete(code, secret)
    assert store.room(code) is None
    assert store.room(other) is not None


def test_concurrent_classroom_answers(tmp_path):
    store = Store(path=str(tmp_path / "test.sqlite"))
    code, secret = store.create_room()
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: store.submit(code, str(i), ["Wednesday"]), range(30)))
    assert len(store.transactions(code, secret)) == 30


def test_explicit_votes_and_catalog_snapshot(tmp_path):
    from serieslab.model import CATALOG, LEGACY_CATALOG
    store = Store(path=str(tmp_path / "votes.sqlite"))
    code, secret = store.create_room()
    assert store.room(code)["catalog"] == CATALOG
    votes = dict.fromkeys(CATALOG, False)
    store.submit(code, "all-no", votes)
    assert store.transactions(code, secret) == [[]]
    with pytest.raises(ValueError):
        store.submit(code, "incomplete", {"Wednesday": True})
    with pytest.raises(ValueError):
        store.submit(code, "invalid", {**votes, "Wednesday": "Nein"})
    with store.connection() as conn:
        import json
        saved = json.loads(conn.execute("SELECT likes FROM responses").fetchone()[0])
        assert saved == votes
        conn.execute("DELETE FROM room_catalogs WHERE room=?", (code,))
    assert store.room(code)["catalog"] == LEGACY_CATALOG
