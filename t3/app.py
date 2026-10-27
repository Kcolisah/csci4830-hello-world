"""Small SQLite-backed motorcycle maintenance log for CSCI 4830 T3."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template_string, request, url_for

app = Flask(__name__)
app.config["DATABASE"] = os.getenv(
    "MT_DB_PATH", str(Path(__file__).resolve().parent / "data" / "maintenance.sqlite3")
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Motorcycle Maintenance Tracker Lite</title>
<style>
  :root { color-scheme: dark; font-family: system-ui, -apple-system, Segoe UI, sans-serif; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #0d1117; color: #e6edf3; }
  main { max-width: 1000px; margin: 0 auto; padding: 48px 22px 64px; }
  .eyebrow { color: #9caec0; letter-spacing: .12em; text-transform: uppercase; font-size: 12px; font-weight: 700; }
  h1 { font-size: clamp(28px, 5vw, 42px); line-height: 1.15; letter-spacing: -.035em; margin: 10px 0; }
  .intro { color: #aab7c6; margin-bottom: 30px; }
  .overview { display: flex; gap: 12px; align-items: baseline; margin-bottom: 22px; }
  .count { font-size: 32px; font-weight: 750; }
  .caption { color: #aab7c6; }
  .layout { display: grid; grid-template-columns: 0.9fr 1.5fr; gap: 20px; align-items: start; }
  .panel { background: #151d27; border: 1px solid #344052; padding: 24px; }
  h2 { font-size: 18px; margin: 0 0 19px; }
  label { display: block; color: #c6d2e0; font-size: 13px; margin: 0 0 6px; font-weight: 650; }
  input, textarea { font: inherit; width: 100%; background: #0d1117; color: #e6edf3; border: 1px solid #526176; padding: 11px; border-radius: 0; margin-bottom: 16px; }
  input:focus, textarea:focus { outline: 2px solid #7eb6ff; outline-offset: 0; }
  textarea { resize: vertical; min-height: 75px; }
  button { background: #dbeafe; border: 0; color: #0c1829; width: 100%; font: inherit; font-weight: 750; padding: 12px; cursor: pointer; }
  button:hover { background: #9dccff; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 12px 9px; text-align: left; border-bottom: 1px solid #344052; vertical-align: top; }
  th { color: #abb9c9; }
  .note { color: #aab7c6; font-size: 12px; }
  .empty { color: #aab7c6; padding: 18px 0; }
  .notice { background: #163525; border: 1px solid #427358; padding: 10px 14px; margin-bottom: 16px; }
  .error { background: #391b20; border: 1px solid #a45d66; padding: 10px 14px; margin-bottom: 16px; }
  footer { padding-top: 28px; color: #8996a6; font-size: 12px; }
  @media(max-width:760px){.layout{grid-template-columns:1fr} .panel{padding:18px} table{font-size:12px} th,td{padding:8px 5px}}
</style>
</head>
<body>
<main>
  <div class="eyebrow">CSCI 4830 · T3 Tech Exercise</div>
  <h1>Motorcycle Maintenance Tracker <span style="color:#a7c9f5">Lite</span></h1>
  <p class="intro">A simple maintenance log built with Flask, SQLite, GitHub, and AWS EC2.</p>
  <div class="overview"><span class="count">{{ records|length }}</span><span class="caption">saved service records</span></div>
  {% if request.args.get('added') == '1' %}<div class="notice" role="status">Record saved to SQLite.</div>{% endif %}
  {% if error %}<div class="error" role="alert">{{ error }}</div>{% endif %}
  <div class="layout">
    <section class="panel">
      <h2>Add maintenance</h2>
      <form method="post" action="{{ url_for('add_record') }}">
        <label for="service">Service</label>
        <input id="service" name="service" placeholder="Chain clean / Oil change" maxlength="80" required>
        <label for="mileage">Odometer (miles)</label>
        <input id="mileage" name="mileage" type="number" min="0" max="9999999" placeholder="3000" required>
        <label for="service_date">Date</label>
        <input id="service_date" name="service_date" type="date" value="{{ today }}" required>
        <label for="notes">Notes (optional)</label>
        <textarea id="notes" name="notes" maxlength="300" placeholder="Anything worth remembering"></textarea>
        <button type="submit">Save record</button>
      </form>
    </section>
    <section class="panel">
      <h2>Service history</h2>
      {% if records %}
      <table>
        <thead><tr><th>Date</th><th>Service</th><th>Mileage</th><th>Notes</th></tr></thead>
        <tbody>
        {% for record in records %}
          <tr><td>{{ record['service_date'] }}</td><td><strong>{{ record['service'] }}</strong></td>
          <td>{{ '{:,}'.format(record['mileage']) }} mi</td><td class="note">{{ record['notes'] or '—' }}</td></tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}<p class="empty">No records yet. Add the first maintenance entry using the form.</p>{% endif %}
    </section>
  </div>
  <footer>Class demonstration app · Please use only test data · /health checks the database</footer>
</main>
</body>
</html>"""


@contextmanager
def connect_db():
    db_path = Path(app.config["DATABASE"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with connect_db() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS maintenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT NOT NULL,
                mileage INTEGER NOT NULL,
                service_date TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            )"""
        )


@app.get("/")
def home():
    with connect_db() as connection:
        records = connection.execute(
            "SELECT service, mileage, service_date, notes FROM maintenance "
            "ORDER BY service_date DESC, id DESC"
        ).fetchall()
    return render_template_string(PAGE, records=records, today=date.today().isoformat(), error=None)


@app.post("/add")
def add_record():
    service = request.form.get("service", "").strip()
    mileage_raw = request.form.get("mileage", "").strip()
    date_raw = request.form.get("service_date", "").strip()
    notes = request.form.get("notes", "").strip()

    error = None
    if not service or len(service) > 80 or len(notes) > 300:
        error = "Enter a service name (up to 80 characters) and a short note."
    try:
        mileage = int(mileage_raw)
        if not 0 <= mileage <= 9_999_999:
            raise ValueError
    except ValueError:
        error = "Mileage must be a number between 0 and 9,999,999."
        mileage = 0
    try:
        date.fromisoformat(date_raw)
    except ValueError:
        error = "Choose a valid service date."

    if error:
        with connect_db() as connection:
            records = connection.execute(
                "SELECT service, mileage, service_date, notes FROM maintenance "
                "ORDER BY service_date DESC, id DESC"
            ).fetchall()
        return render_template_string(
            PAGE, records=records, today=date.today().isoformat(), error=error
        ), 400

    with connect_db() as connection:
        connection.execute(
            "INSERT INTO maintenance (service, mileage, service_date, notes) "
            "VALUES (?, ?, ?, ?)",
            (service, mileage, date_raw, notes),
        )
    return redirect(url_for("home", added="1"), code=303)


@app.get("/health")
def health():
    with connect_db() as connection:
        count = connection.execute("SELECT COUNT(*) FROM maintenance").fetchone()[0]
    return jsonify(status="ok", database="sqlite", records=count)


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
