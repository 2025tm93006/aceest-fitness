"""Flask migration of Aceestver-2.2.1.py."""
import os, sqlite3
from datetime import datetime
from pathlib import Path
from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

PROGRAMS = {"fat-loss": ("Fat Loss (FL)", 22), "muscle-gain": ("Muscle Gain (MG)", 35),
            "beginner": ("Beginner (BG)", 26)}


def create_app(config=None):
    app = Flask(__name__);
    app.config["DATABASE"] = os.environ.get("ACEEST_DB", str(Path(app.instance_path) / "aceest.sqlite3"));
    app.config.update(config or {});
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if "db" not in g: g.db = sqlite3.connect(app.config["DATABASE"]);g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        if (c := g.pop("db", None)): c.close()

    with app.app_context():
        db().executescript(
            "CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,name TEXT UNIQUE,age INTEGER,weight REAL,program TEXT,calories INTEGER);CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY,client_name TEXT,week TEXT,adherence INTEGER);");db().commit()

    def client_data(data):
        n, p = data.get('name', '').strip(), data.get('program', '')
        if not n or p not in PROGRAMS: raise ValueError('Name and program are required.')
        try:
            a, w = int(data.get('age', 0) or 0), float(data.get('weight', 0) or 0)
        except ValueError as e:
            raise ValueError('Age and weight must be numbers.') from e
        if a < 0 or w < 0: raise ValueError('Age and weight cannot be negative.')
        return n, a, w, p, int(w * PROGRAMS[p][1])

    @app.get('/')
    def index():
        n = request.args.get('name', '');
        c = db().execute('SELECT * FROM clients WHERE name=?', (n,)).fetchone() if n else None;
        rows = db().execute('SELECT * FROM progress WHERE client_name=? ORDER BY id', (n,)).fetchall() if n else []
        return render_template('index.html', programs=PROGRAMS,
                               clients=db().execute('SELECT name FROM clients ORDER BY name').fetchall(), client=c,
                               progress=rows, message=request.args.get('message'))

    @app.post('/clients')
    def save_client():
        try:
            n, a, w, p, k = client_data(request.form)
        except ValueError as e:
            return render_template('error.html', message=str(e)), 400
        db().execute('INSERT OR REPLACE INTO clients(name,age,weight,program,calories) VALUES(?,?,?,?,?)',
                     (n, a, w, p, k));
        db().commit();
        return redirect(url_for('index', name=n, message='Client data saved'), 303)

    @app.post('/progress')
    def save_progress():
        n = request.form.get('name', '')
        try:
            a = int(request.form.get('adherence', 0))
        except ValueError:
            a = -1
        if not db().execute('SELECT 1 FROM clients WHERE name=?',
                            (n,)).fetchone() or not 0 <= a <= 100: return render_template('error.html',
                                                                                          message='Select a saved client and adherence from 0 to 100.'), 400
        db().execute('INSERT INTO progress(client_name,week,adherence)VALUES(?,?,?)',
                     (n, datetime.now().strftime('Week %U - %Y'), a));
        db().commit();
        return redirect(url_for('index', name=n, message='Weekly progress logged'), 303)

    @app.get('/api/clients')
    def api_clients():
        return jsonify([dict(x) for x in db().execute('SELECT * FROM clients ORDER BY name')])

    @app.get('/api/clients/<name>/progress')
    def api_progress(name):
        if not db().execute('SELECT 1 FROM clients WHERE name=?', (name,)).fetchone(): abort(404)
        return jsonify([dict(x) for x in
                        db().execute('SELECT week,adherence FROM progress WHERE client_name=? ORDER BY id', (name,))])

    @app.get('/clients/<name>/progress-chart')
    def progress_chart(name):
        client = db().execute('SELECT * FROM clients WHERE name=?', (name,)).fetchone()
        if not client: abort(404)
        rows = db().execute('SELECT week,adherence FROM progress WHERE client_name=? ORDER BY id', (name,)).fetchall()
        if not rows: return render_template('chart_empty.html', name=name), 400
        width = max(760, 180 + 140 * len(rows));
        left, right, top, bottom = 80, width - 35, 40, 400
        step = (right - left) / (len(rows) - 1) if len(rows) > 1 else 0
        points = [{"x": left + index * step, "y": bottom - row['adherence'] * 3.2, "week": row['week'],
                   "adherence": row['adherence']} for index, row in enumerate(rows)]
        return render_template('progress_chart.html', name=name, points=points, width=width, left=left, right=right,
                               top=top, bottom=bottom)

    return app


app = create_app()

if __name__ == '__main__':
 app.run()
