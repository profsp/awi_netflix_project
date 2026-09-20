"""SQLite lokal oder PostgreSQL in der Cloud; alle Werte werden parametrisiert."""
import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from serieslab.model import CATALOG, LEGACY_CATALOG


class Store:
    def __init__(self, url="", path="data/classroom.sqlite3"):
        self.url = url
        self.path = path
        if not url:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS rooms (code TEXT PRIMARY KEY, secret TEXT NOT NULL, opened INTEGER NOT NULL DEFAULT 1, model TEXT)")
            conn.execute("CREATE TABLE IF NOT EXISTS responses (room TEXT NOT NULL, participant TEXT NOT NULL, likes TEXT NOT NULL, PRIMARY KEY(room, participant))")
            conn.execute("CREATE TABLE IF NOT EXISTS room_catalogs (room TEXT PRIMARY KEY, catalog TEXT NOT NULL)")

    @contextmanager
    def connection(self):
        if self.url:
            import psycopg
            conn = psycopg.connect(self.url, connect_timeout=10)
        else:
            conn = sqlite3.connect(self.path, timeout=15)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def sql(self, query):
        return query.replace("?", "%s") if self.url else query

    def create_room(self):
        code = secrets.token_hex(4).upper()
        secret = secrets.token_urlsafe(24)
        with self.connection() as conn:
            conn.execute(self.sql("INSERT INTO rooms(code,secret) VALUES (?,?)"), (code, self.digest(secret)))
            conn.execute(self.sql("INSERT INTO room_catalogs(room,catalog) VALUES (?,?)"), (code, json.dumps(CATALOG)))
        return code, secret

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def room(self, code):
        with self.connection() as conn:
            row = conn.execute(self.sql("SELECT opened,model FROM rooms WHERE code=?"), (code,)).fetchone()
            catalog = conn.execute(self.sql("SELECT catalog FROM room_catalogs WHERE room=?"), (code,)).fetchone()
        return None if row is None else {"opened": bool(row[0]), "model": json.loads(row[1]) if row[1] else None,
                                         "catalog": json.loads(catalog[0]) if catalog else LEGACY_CATALOG}

    def authorized(self, code, secret):
        with self.connection() as conn:
            row = conn.execute(self.sql("SELECT secret FROM rooms WHERE code=?"), (code,)).fetchone()
        return bool(row and secrets.compare_digest(row[0], self.digest(secret)))

    def require_owner(self, code, secret):
        if not self.authorized(code, secret):
            raise ValueError("Der Verwaltungsschlüssel ist ungültig.")

    def submit(self, code, participant, likes):
        room = self.room(code)
        if not room:
            raise ValueError("Dieser Klassenraum existiert nicht.")
        # Neue Fragebögen speichern jede Ja/Nein-Antwort explizit.
        valid = (set(likes) == set(room["catalog"]) and all(type(v) is bool for v in likes.values())) if isinstance(likes, dict) else (isinstance(likes, list) and set(likes).issubset(room["catalog"]))
        if not valid or not participant or len(participant) > 100:
            raise ValueError("Bitte jede Serie mit Ja oder Nein beantworten.")
        with self.connection() as conn:
            # Serialize with close/delete so no response can arrive after closing.
            if not self.url:
                conn.execute("BEGIN IMMEDIATE")
            lock = " FOR UPDATE" if self.url else ""
            row = conn.execute(self.sql("SELECT opened FROM rooms WHERE code=?" + lock), (code,)).fetchone()
            if not row or not row[0]:
                raise ValueError("Dieser Klassenraum sammelt gerade keine Antworten.")
            payload = likes if isinstance(likes, dict) else sorted(set(likes))
            conn.execute(self.sql("INSERT INTO responses(room,participant,likes) VALUES (?,?,?) ON CONFLICT(room,participant) DO UPDATE SET likes=excluded.likes"), (code, self.digest(participant), json.dumps(payload)))

    def transactions(self, code, secret):
        self.require_owner(code, secret)
        with self.connection() as conn:
            rows = conn.execute(self.sql("SELECT likes FROM responses WHERE room=? ORDER BY participant"), (code,)).fetchall()
        responses = [json.loads(row[0]) for row in rows]
        return [sorted(title for title, yes in answer.items() if yes) if isinstance(answer, dict) else answer for answer in responses]

    def update(self, code, secret, *, opened=None, model=None):
        self.require_owner(code, secret)
        with self.connection() as conn:
            if opened is not None:
                conn.execute(self.sql("UPDATE rooms SET opened=? WHERE code=?"), (int(opened), code))
            if model is not None:
                conn.execute(self.sql("UPDATE rooms SET model=? WHERE code=?"), (json.dumps(model), code))

    def delete(self, code, secret):
        self.require_owner(code, secret)
        with self.connection() as conn:
            conn.execute(self.sql("DELETE FROM rooms WHERE code=?"), (code,))
            conn.execute(self.sql("DELETE FROM responses WHERE room=?"), (code,))
            conn.execute(self.sql("DELETE FROM room_catalogs WHERE room=?"), (code,))
