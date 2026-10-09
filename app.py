"""Flask migration of Aceestver-2.2.4.py."""
import os, sqlite3
from datetime import date, datetime
from pathlib import Path
from flask import Flask, abort, g, jsonify, redirect, render_template, request, url_for

PROGRAMS = {"fat-loss-3": ("Fat Loss (FL) – 3 day", 22, "3-day full-body fat loss"),
            "fat-loss-5": ("Fat Loss (FL) – 5 day", 24, "5-day split, higher volume fat loss"),
            "muscle-gain": ("Muscle Gain (MG) – PPL", 35, "Push/Pull/Legs hypertrophy"),
            "beginner": ("Beginner (BG)", 26, "3-day simple beginner full-body")}
TYPES = ("Strength", "Hypertrophy", "Conditioning", "Mixed", "Mobility")


def create_app(config=None):
    app = Flask(__name__);
    app.config['DATABASE'] = os.environ.get('ACEEST_DB', str(Path(app.instance_path) / 'aceest.sqlite3'));
    app.config.update(config or {});
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g: g.db = sqlite3.connect(app.config['DATABASE']);g.db.row_factory = sqlite3.Row;g.db.execute(
            'PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close(_):
        if (c := g.pop('db', None)): c.close()

    with app.app_context():
        db().executescript('''CREATE TABLE IF NOT EXISTS clients
                              (
                                  id
                                  INTEGER
                                  PRIMARY
                                  KEY,
                                  name
                                  TEXT
                                  UNIQUE
                                  NOT
                                  NULL,
                                  age
                                  INTEGER,
                                  height
                                  REAL,
                                  weight
                                  REAL,
                                  program
                                  TEXT
                                  NOT
                                  NULL,
                                  calories
                                  INTEGER,
                                  target_weight
                                  REAL,
                                  target_adherence
                                  INTEGER
                              );
        CREATE TABLE IF NOT EXISTS progress
        (
            id
            INTEGER
            PRIMARY
            KEY,
            client_id
            INTEGER
            NOT
            NULL,
            week
            TEXT
            NOT
            NULL,
            adherence
            INTEGER
            NOT
            NULL,
            FOREIGN
            KEY
        (
            client_id
        ) REFERENCES clients
        (
            id
        ));
        CREATE TABLE IF NOT EXISTS workouts
        (
            id
            INTEGER
            PRIMARY
            KEY,
            client_id
            INTEGER
            NOT
            NULL,
            date
            TEXT
            NOT
            NULL,
            workout_type
            TEXT
            NOT
            NULL,
            duration_min
            INTEGER
            NOT
            NULL,
            notes
            TEXT,
            FOREIGN
            KEY
        (
            client_id
        ) REFERENCES clients
        (
            id
        ));
        CREATE TABLE IF NOT EXISTS exercises
        (
            id
            INTEGER
            PRIMARY
            KEY,
            workout_id
            INTEGER
            NOT
            NULL,
            name
            TEXT,
            sets
            INTEGER,
            reps
            INTEGER,
            weight
            REAL,
            FOREIGN
            KEY
        (
            workout_id
        ) REFERENCES workouts
        (
            id
        ));
        CREATE TABLE IF NOT EXISTS metrics
        (
            id
            INTEGER
            PRIMARY
            KEY,
            client_id
            INTEGER
            NOT
            NULL,
            date
            TEXT
            NOT
            NULL,
            weight
            REAL,
            waist
            REAL,
            bodyfat
            REAL,
            FOREIGN
            KEY
        (
            client_id
        ) REFERENCES clients
        (
            id
        ));''');
        db().commit()

    def number(data, key, kind=float, minimum=0, required=False):
        raw = data.get(key, '')
        if raw == '':
            if required: raise ValueError(f'{key} is required.')
            return None
        try:
            value = kind(raw)
        except ValueError as e:
            raise ValueError(f'{key} must be a number.') from e
        if value < minimum: raise ValueError(f'{key} cannot be negative.')
        return value

    def profile(data):
        name, p = data.get('name', '').strip(), data.get('program', '')
        if not name or p not in PROGRAMS: raise ValueError('Name and program are required.')
        age = number(data, 'age', int);
        h = number(data, 'height');
        w = number(data, 'weight');
        tw = number(data, 'target_weight');
        ta = number(data, 'target_adherence', int)
        if ta is not None and ta > 100: raise ValueError('target adherence must be at most 100.')
        return name, age, h, w, p, int(w * PROGRAMS[p][1]) if w else None, tw, ta

    def get_client(cid):
        c = db().execute('SELECT * FROM clients WHERE id=?', (cid,)).fetchone()
        if not c: abort(404)
        return c

    @app.get('/')
    def home():
        return render_template('index.html', programs=PROGRAMS,
                               clients=db().execute('SELECT * FROM clients ORDER BY name').fetchall())

    @app.post('/clients')
    def save_client():
        try:
            values = profile(request.form)
        except ValueError as e:
            return render_template('error.html', message=str(e)), 400
        db().execute(
            'INSERT INTO clients(name,age,height,weight,program,calories,target_weight,target_adherence)VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET age=excluded.age,height=excluded.height,weight=excluded.weight,program=excluded.program,calories=excluded.calories,target_weight=excluded.target_weight,target_adherence=excluded.target_adherence',
            values);
        db().commit();
        cid = db().execute('SELECT id FROM clients WHERE name=?', (values[0],)).fetchone()['id'];
        return redirect(url_for('client', cid=cid), 303)

    @app.get('/clients/<int:cid>')
    def client(cid):
        c = get_client(cid);
        progress = db().execute('SELECT * FROM progress WHERE client_id=? ORDER BY id', (cid,)).fetchall();
        metrics = db().execute('SELECT * FROM metrics WHERE client_id=? ORDER BY date DESC,id DESC', (cid,)).fetchall();
        workouts = db().execute(
            'SELECT w.*,e.name exercise,e.sets,e.reps,e.weight exercise_weight FROM workouts w LEFT JOIN exercises e ON e.workout_id=w.id WHERE w.client_id=? ORDER BY w.date DESC,w.id DESC',
            (cid,)).fetchall();
        bmi = round(c['weight'] / (c['height'] / 100) ** 2, 1) if c['weight'] and c['height'] else None
        return render_template('client.html', c=c, programs=PROGRAMS, progress=progress, metrics=metrics,
                               workouts=workouts, bmi=bmi, types=TYPES, today=date.today().isoformat())

    @app.post('/clients/<int:cid>/progress')
    def add_progress(cid):
        get_client(cid)
        try:
            a = number(request.form, 'adherence', int, 0, True)
        except ValueError as e:
            return render_template('error.html', message=str(e)), 400
        if a > 100: return render_template('error.html', message='Adherence must be at most 100.'), 400
        db().execute('INSERT INTO progress(client_id,week,adherence)VALUES(?,?,?)',
                     (cid, datetime.now().strftime('Week %U - %Y'), a));
        db().commit();
        return redirect(url_for('client', cid=cid), 303)

    @app.post('/clients/<int:cid>/metrics')
    def add_metrics(cid):
        get_client(cid)
        try:
            d = date.fromisoformat(request.form.get('date', '')).isoformat();w = number(request.form, 'weight', float,
                                                                                        0, True);waist = number(
                request.form, 'waist');bf = number(request.form, 'bodyfat')
        except(ValueError) as e:
            return render_template('error.html', message=str(e)), 400
        db().execute('INSERT INTO metrics(client_id,date,weight,waist,bodyfat)VALUES(?,?,?,?,?)',
                     (cid, d, w, waist, bf));
        db().commit();
        return redirect(url_for('client', cid=cid), 303)

    @app.post('/clients/<int:cid>/workouts')
    def add_workout(cid):
        get_client(cid)
        try:
            d = date.fromisoformat(request.form.get('date', '')).isoformat();duration = number(request.form, 'duration',
                                                                                               int, 1, True)
        except ValueError as e:
            return render_template('error.html', message=str(e)), 400
        typ = request.form.get('type', '')
        if typ not in TYPES: return render_template('error.html', message='Choose a valid workout type.'), 400
        cur = db().execute('INSERT INTO workouts(client_id,date,workout_type,duration_min,notes)VALUES(?,?,?,?,?)',
                           (cid, d, typ, duration, request.form.get('notes', '').strip()))
        if (n := request.form.get('exercise', '').strip()):
            try:
                s = number(request.form, 'sets', int, 1, True);r = number(request.form, 'reps', int, 1,
                                                                          True);w = number(request.form,
                                                                                           'exercise_weight') or 0
            except ValueError as e:
                return render_template('error.html', message=str(e)), 400
            db().execute('INSERT INTO exercises(workout_id,name,sets,reps,weight)VALUES(?,?,?,?,?)',
                         (cur.lastrowid, n, s, r, w))
        db().commit();
        return redirect(url_for('client', cid=cid), 303)

    @app.get('/api/clients')
    def api_clients():
        return jsonify([dict(x) for x in db().execute('SELECT * FROM clients ORDER BY name')])

    @app.get('/api/clients/<int:cid>/progress')
    def api_progress(cid):
        get_client(cid);return jsonify([dict(x) for x in db().execute(
            'SELECT week,adherence FROM progress WHERE client_id=? ORDER BY id', (cid,))])

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
