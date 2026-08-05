# 🚕 RelaxiTaxi — Cab Aggregator Platform

A Streamlit-based cab aggregator web app that connects riders and drivers — book rides, track them live on a map, manage driver requests, and pay via cash, card, or UPI.

## Features

- **Role-based entry** — choose to continue as a Customer or a Driver from the landing page.
- **Registration & login** for both riders and drivers, backed by a SQLite database with hashed passwords.
- **Ride booking** — enter pickup/drop locations, choose AC/Non-AC, and get an estimated fare based on distance.
- **Live ride tracking** with an interactive map (Folium) and geocoding via geopy/Nominatim.
- **Driver view** — drivers can see and accept incoming ride requests.
- **Ride history** for both riders and drivers.
- **Payments** — Cash, Card, or UPI (with a generated QR code) checkout flow.

## Tech Stack

- [Streamlit](https://streamlit.io/) — UI/app framework
- SQLite (via `sqlite3`) — persistence layer
- [geopy](https://github.com/geopy/geopy) — geocoding and distance calculations
- [folium](https://python-visualization.github.io/folium/) / `streamlit-folium` — interactive maps
- [qrcode](https://pypi.org/project/qrcode/) — UPI payment QR generation

## Project Structure

```
src/
├── app.py                 # Landing page (role selection)
├── db_utils.py             # SQLite connection, schema, auth, ride CRUD
├── ride_utils.py           # Fare/distance calculation helpers
├── shared_state.py         # Shared in-memory app state (cached resource)
└── pages/
    ├── rider_login.py / rider_register.py
    ├── driver_login.py / driver_register.py
    ├── book_ride.py
    ├── track_ride.py
    ├── driver_view.py
    ├── payment_ui.py
    ├── rider_history.py
    └── driver_history.py
tests/                      # Unit, integration, and security tests
```

## Getting Started

### Prerequisites

- Python 3.9+

### Installation

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### Running the app

```bash
streamlit run src/app.py
```

The app will open in your browser (default: http://localhost:8501). A SQLite database (`relaxitaxi.db`) is created automatically under `src/` on first run.

## Testing

```bash
pytest tests/ -v --cov=src --cov-report=html
```

See [COVERAGE_GUIDE.md](COVERAGE_GUIDE.md) for coverage details and [CI_PIPELINE_SETUP.md](CI_PIPELINE_SETUP.md) for the full CI pipeline (build, test, coverage, lint, and security stages).

## Code Quality & Security

```bash
pylint src/ tests/     # Linting (threshold: 7.5/10)
bandit -r src/         # Security scan
safety check           # Dependency vulnerability scan
```
