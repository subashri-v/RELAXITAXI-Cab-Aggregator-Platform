"""Database uitilities and connection."""

# db_utils.py -- Stable SQLite backend for RelaxiTaxi
import os
import sqlite3
import sys
from datetime import datetime, timedelta

import bcrypt

# --- Absolute DB path to avoid multiple DBs ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "relaxitaxi.db")

# Make sibling modules (e.g. ride_utils) importable by bare name regardless
# of whether this module was loaded as top-level `db_utils` (Streamlit's
# runtime import pattern) or as the package `src.db_utils` (tests).
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ride_utils import estimate_eta_minutes  # pylint: disable=wrong-import-position,C0411

# How long a ride can sit "locked_by_driver" before it's treated as
# abandoned (driver's session dropped/refreshed before accepting or
# rejecting) and released back to the pending pool.
LOCK_TIMEOUT_SECONDS = 30


# --- DB Connection helper ---
"""Connecting to SQLlite database."""
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL allows concurrent readers alongside a writer, which matters here
    # since drivers poll for pending rides while riders/other drivers write.
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# --- Initialize DB ---
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Riders table
    """rider details table."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS riders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # Drivers table
    """Driver details table."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        vehicle_no TEXT,
        license_no TEXT
    )
    """)

    # Rides table
    """Ride details table."""
    cur.execute("""
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rider_id INTEGER,
        driver_id INTEGER,
        start_location TEXT,
        end_location TEXT,
        start_lat REAL,
        start_lon REAL,
        end_lat REAL,
        end_lon REAL,
        distance_km REAL,
        fare REAL,
        ac INTEGER,
        status TEXT,
        ride_time TEXT,
        FOREIGN KEY(rider_id) REFERENCES riders(id) ON DELETE SET NULL,
        FOREIGN KEY(driver_id) REFERENCES drivers(id) ON DELETE SET NULL
    )
    """)

    _ensure_ride_columns(conn)

    conn.commit()
    conn.close()


# --- Migration: add columns used by the DB-backed booking flow ---
# needed because CREATE TABLE IF NOT EXISTS won't add columns to a DB file
# that was created before these fields existed.
def _ensure_ride_columns(conn):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(rides)")
    existing = {row[1] for row in cur.fetchall()}
    additions = {
        "driver_name": "TEXT",
        "car_number": "TEXT",
        "eta_minutes": "INTEGER",
        "progress": "REAL DEFAULT 0.0",
        "locked_at": "TEXT",
    }
    for column, coltype in additions.items():
        if column not in existing:
            cur.execute(f"ALTER TABLE rides ADD COLUMN {column} {coltype}")


# --- Password hashing ---
"""Hashing password for security."""
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


# --- User authentication ---
def authenticate_user(user_type: str, email: str, password: str):
    if user_type not in ("riders", "drivers"):
        raise ValueError("user_type must be 'riders' or 'drivers'")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {user_type} WHERE email=?", (email,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    user = dict(row)
    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        return None
    return user


# --- User registration ---
def register_user(user_type: str, name: str, email: str, password: str, vehicle_no=None, license_no=None) -> bool:
    if user_type not in ("riders", "drivers"):
        raise ValueError("user_type must be 'riders' or 'drivers'")

    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(password)

    try:
        if user_type == "riders":
            cur.execute("INSERT INTO riders (name, email, password) VALUES (?, ?, ?)", (name, email, hashed))
        else:
            cur.execute(
                "INSERT INTO drivers (name, email, password, vehicle_no, license_no) VALUES (?, ?, ?, ?, ?)",
                (name, email, hashed, vehicle_no, license_no)
            )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already exists
        return False
    finally:
        conn.close()


# --- Add ride ---
"""Adding new ride to db."""
def add_ride(rider_id, start, end, start_coords, end_coords, distance_km, fare, ac, driver_id=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO rides (
                rider_id, driver_id, start_location, end_location,
                start_lat, start_lon, end_lat, end_lon,
                distance_km, fare, ac, status, ride_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rider_id,
            driver_id,
            start,
            end,
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1],
            distance_km,
            fare,
            1 if ac else 0,
            "pending",
            datetime.now().isoformat()
        ))
        ride_id = cur.lastrowid
        conn.commit()
        return ride_id
    finally:
        conn.close()


# --- Driver accepts ride ---
def accept_ride(ride_id: int, driver_id: int, driver_name: str = None):
    """Assign the accepting driver to the ride, using their real registered
    vehicle and a distance-based ETA rather than book-time placeholder data."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT vehicle_no FROM drivers WHERE id=?", (driver_id,))
        driver_row = cur.fetchone()
        car_number = driver_row["vehicle_no"] if driver_row else None

        cur.execute("SELECT distance_km FROM rides WHERE id=?", (ride_id,))
        ride_row = cur.fetchone()
        eta_minutes = estimate_eta_minutes(ride_row["distance_km"]) if ride_row else None

        cur.execute(
            "UPDATE rides SET driver_id=?, driver_name=?, car_number=?, "
            "eta_minutes=?, status=? WHERE id=?",
            (driver_id, driver_name, car_number, eta_minutes, "accepted", ride_id)
        )
        conn.commit()
    finally:
        conn.close()


# --- Driver claims a pending ride before accepting/rejecting it ---
def try_lock_ride(ride_id: int) -> bool:
    """Atomically claim a pending ride for a driver.

    Returns True if this call won the race (ride was still 'pending'),
    False if another driver already claimed it first.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE rides SET status='locked_by_driver', locked_at=? WHERE id=? AND status='pending'",
            (datetime.now().isoformat(), ride_id)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# --- Release locks whose driver never accepted/rejected (dropped session) ---
def reclaim_stale_locks():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cutoff = (datetime.now() - timedelta(seconds=LOCK_TIMEOUT_SECONDS)).isoformat()
        cur.execute(
            "UPDATE rides SET status='pending', locked_at=NULL "
            "WHERE status='locked_by_driver' AND (locked_at IS NULL OR locked_at < ?)",
            (cutoff,)
        )
        conn.commit()
    finally:
        conn.close()


# --- Get the oldest ride still waiting for a driver ---
def get_pending_ride():
    reclaim_stale_locks()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM rides WHERE status='pending' ORDER BY id ASC LIMIT 1")
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Get a rider's currently in-progress ride, if any ---
def get_active_ride_for_rider(rider_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM rides WHERE rider_id=? AND status IN "
            "('pending', 'locked_by_driver', 'accepted') ORDER BY id DESC LIMIT 1",
            (rider_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()



# --- Get a driver's currently accepted ride, if any (e.g. to resume after
# their session_state was reset mid-ride) ---
def get_active_ride_for_driver(driver_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM rides WHERE driver_id=? AND status='accepted' "
            "ORDER BY id DESC LIMIT 1",
            (driver_id,)
        )
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Fetch a single ride by id, e.g. to re-sync a cached copy with the DB ---
def get_ride_by_id(ride_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM rides WHERE id=?", (ride_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Persist ride progress as the driver moves ---
def update_ride_progress(ride_id: int, progress: float):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE rides SET progress=? WHERE id=?", (progress, ride_id))
        conn.commit()
    finally:
        conn.close()


# --- Persist a route change made from the tracking page ---
def update_ride_route(ride_id: int, updated: dict):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """UPDATE rides SET start_location=?, end_location=?,
               start_lat=?, start_lon=?, end_lat=?, end_lon=?,
               distance_km=?, fare=? WHERE id=?""",
            (
                updated["start"], updated["end"],
                updated["start_coords"][0], updated["start_coords"][1],
                updated["end_coords"][0], updated["end_coords"][1],
                updated["distance_km"], updated["fare"],
                ride_id
            )
        )
        conn.commit()
    finally:
        conn.close()


# --- Map a rides row into the shapes the UI pages already expect ---
def ride_to_booking_view(ride: dict) -> dict:
    return {
        "ride_id": ride["id"],
        "type": "AC Ride" if ride["ac"] else "Non-AC Ride",
        "fare": ride["fare"],
        "driver": ride.get("driver_name"),
        "car_number": ride.get("car_number"),
        "eta": ride.get("eta_minutes"),
        "status": ride["status"],
    }


def ride_to_distance_data(ride: dict) -> dict:
    return {
        "start": ride["start_location"],
        "end": ride["end_location"],
        "start_coords": (ride["start_lat"], ride["start_lon"]),
        "end_coords": (ride["end_lat"], ride["end_lon"]),
        "distance_km": ride["distance_km"],
    }


# --- Update ride status ---
def update_ride_status(ride_id: int, status: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE rides SET status=? WHERE id=?", (status, ride_id))
        conn.commit()
    finally:
        conn.close()


# --- Get rider history ---
"""Rider rides saved in db."""
def get_rider_history(rider_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM rides WHERE rider_id=? ORDER BY id DESC", (rider_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Get driver history ---
"""Driver rides saved in db."""
def get_driver_history(driver_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM rides WHERE driver_id=? ORDER BY id DESC", (driver_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# --- Optional: get user by email ---
def get_user_by_email(user_type: str, email: str):
    if user_type not in ("riders", "drivers"):
        raise ValueError("user_type must be 'riders' or 'drivers'")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {user_type} WHERE email=?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Get user by id (used to restore a session after a browser refresh) ---
def get_user_by_id(user_type: str, user_id):
    if user_type not in ("riders", "drivers"):
        raise ValueError("user_type must be 'riders' or 'drivers'")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {user_type} WHERE id=?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Auto-initialize DB ---
if not os.path.exists(DB_PATH):
    init_db()










