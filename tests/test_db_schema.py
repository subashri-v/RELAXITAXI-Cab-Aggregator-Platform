import sqlite3
import os
import pytest
from src import db_utils

def test_db_tables_exist(tmp_path, monkeypatch):
    db_file = tmp_path / "schema_test.db"
    monkeypatch.setattr(db_utils, "DB_PATH", str(db_file))
    db_utils.init_db()

    conn = db_utils.get_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]

    assert "riders" in tables
    assert "drivers" in tables

    conn.close()

def test_riders_table_columns(tmp_path, monkeypatch):
    db_file = tmp_path / "schema_test2.db"
    monkeypatch.setattr(db_utils, "DB_PATH", str(db_file))
    db_utils.init_db()

    conn = db_utils.get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(riders)")
    cols = [c[1] for c in cur.fetchall()]

    expected = {"id", "name", "email", "password"}
    assert expected.issubset(cols)

    conn.close()

def test_drivers_table_columns(tmp_path, monkeypatch):
    db_file = tmp_path / "schema_test3.db"
    monkeypatch.setattr(db_utils, "DB_PATH", str(db_file))
    db_utils.init_db()

    conn = db_utils.get_connection()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(drivers)")
    cols = [c[1] for c in cur.fetchall()]

    expected = {"id", "name", "email", "password", "vehicle_no", "license_no"}
    assert expected.issubset(cols)

    conn.close()

def test_email_unique_constraint(tmp_path, monkeypatch):
    db_file = tmp_path / "schema_test4.db"
    monkeypatch.setattr(db_utils, "DB_PATH", str(db_file))
    db_utils.init_db()

    conn = db_utils.get_connection()

    cur = conn.cursor()
    cur.execute("INSERT INTO riders (name, email, password) VALUES (?, ?, ?)",
                ("John", "john@mail.com", "123"))
    conn.commit()

    # attempt duplicate
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO riders (name, email, password) VALUES (?, ?, ?)",
                    ("John2", "john@mail.com", "456"))

    conn.close()
