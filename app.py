"""Flask migration of Aceestver2.0.1.py."""
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

PROGRAMS = {"fat-loss": ("Fat Loss (FL)", 22), "muscle-gain": ("Muscle Gain (MG)", 35), "beginner": ("Beginner (BG)", 26)}

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=os.environ.get("ACEEST_DB", str(Path(app.instance_path) / "aceest.sqlite3")))
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    def db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db
    @app.teardown_appcontext
    def close_db(_error):
        conn = g.pop("db", None)
        if conn:
            conn.close()
    with app.app_context():
        db().executescript("CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL, age INTEGER, weight REAL, program TEXT NOT NULL, calories INTEGER); CREATE TABLE IF NOT EXISTS progress (id INTEGER PRIMARY KEY, client_name TEXT NOT NULL, week TEXT NOT NULL, adherence INTEGER NOT NULL);")
        db().commit()
    def parse_client(data):
        name, program = data.get("name", "").strip(), data.get("program", "")
        if not name or program not in PROGRAMS:
            raise ValueError("Name and program are required.")
        try:
            age, weight = int(data.get("age", 0) or 0), float(data.get("weight", 0) or 0)
        except ValueError as error:
            raise ValueError("Age and weight must be numbers.") from error
        if age < 0 or weight < 0:
            raise ValueError("Age and weight cannot be negative.")
        return name, age, weight, program, int(weight * PROGRAMS[program][1])
    @app.get("/")
    def index():
        name = request.args.get("name", "")
        client = db().execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone() if name else None
        progress = db().execute("SELECT * FROM progress WHERE client_name=? ORDER BY id DESC", (name,)).fetchall() if name else []
        return render_template("index.html", programs=PROGRAMS, clients=db().execute("SELECT name FROM clients ORDER BY name").fetchall(), client=client, progress=progress, message=request.args.get("message"))
    @app.post("/clients")
    def save_client():
        try:
            name, age, weight, program, calories = parse_client(request.form)
        except ValueError as error:
            return render_template("error.html", message=str(error)), 400
        db().execute("INSERT OR REPLACE INTO clients (name,age,weight,program,calories) VALUES (?,?,?,?,?)", (name, age, weight, program, calories))
        db().commit()
        return redirect(url_for("index", name=name, message="Client data saved"), code=303)
    @app.post("/progress")
    def save_progress():
        name = request.form.get("name", "").strip()
        try:
            adherence = int(request.form.get("adherence", 0))
        except ValueError:
            adherence = -1
        if not db().execute("SELECT 1 FROM clients WHERE name=?", (name,)).fetchone() or not 0 <= adherence <= 100:
            return render_template("error.html", message="Select a saved client and an adherence value from 0 to 100."), 400
        db().execute("INSERT INTO progress (client_name,week,adherence) VALUES (?,?,?)", (name, datetime.now().strftime("Week %U - %Y"), adherence))
        db().commit()
        return redirect(url_for("index", name=name, message="Weekly progress logged"), code=303)
    @app.get("/api/clients")
    def api_clients():
        return jsonify([dict(row) for row in db().execute("SELECT * FROM clients ORDER BY name")])
    @app.get("/api/clients/<name>/progress")
    def api_progress(name):
        if not db().execute("SELECT 1 FROM clients WHERE name=?", (name,)).fetchone():
            abort(404)
        return jsonify([dict(row) for row in db().execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,))])
    return app

app = create_app()

if __name__ == "__main__":
    app.run()
