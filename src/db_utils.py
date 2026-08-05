"""Database uitilities and connection."""

# db_utils.py -- Stable SQLite backend for RelaxiTaxi
import sqlite3
import hashlib
from datetime import datetime
import os

# --- Absolute DB path to avoid multiple DBs ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "relaxitaxi.db")


# --- DB Connection helper ---
"""Connecting to SQLlite database."""
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
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

    conn.commit()
    conn.close()


# --- Password hashing ---
"""Hashing password for security."""
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


# --- User authentication ---
def authenticate_user(user_type: str, email: str, password: str):
    if user_type not in ("riders", "drivers"):
        raise ValueError("user_type must be 'riders' or 'drivers'")

    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(password)
    cur.execute(f"SELECT * FROM {user_type} WHERE email=? AND password=?", (email, hashed))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


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
"""Function for driver accepting ride to be stored in db."""
def accept_ride(ride_id: int, driver_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE rides SET driver_id=?, status=? WHERE id=?", (driver_id, "accepted", ride_id))
        conn.commit()
    finally:
        conn.close()


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
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {user_type} WHERE email=?", (email,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# --- Auto-initialize DB ---
if not os.path.exists(DB_PATH):
    init_db()










