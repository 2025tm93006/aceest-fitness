"""Flask migration of Aceestver-3.1.2.py."""
import os, random, sqlite3
from io import BytesIO
from pathlib import Path

from flask import Flask, abort, g, jsonify, redirect, render_template, request, send_file, session, url_for
from fpdf import FPDF

PROGRAMS = {"fat-loss": ("Fat Loss (FL) – 3 day", 22), "fat-loss-5": ("Fat Loss (FL) – 5 day", 24),
            "muscle-gain": ("Muscle Gain (MG) – PPL", 35), "beginner": ("Beginner (BG)", 26)}
POOLS = {"Strength": ["Squat", "Deadlift", "Bench Press", "Overhead Press", "Pull-Up", "Barbell Row"],
         "Hypertrophy": ["Leg Press", "Incline Dumbbell Press", "Lat Pulldown", "Lateral Raise", "Bicep Curl",
                         "Tricep Extension"],
         "Conditioning": ["Running", "Cycling", "Rowing", "Burpees", "Jump Rope", "Kettlebell Swings"],
         "Full Body": ["Push-Up", "Pull-Up", "Lunge", "Plank", "Dumbbell Row", "Dumbbell Press"]}


def create_app(config=None):
    app = Flask(__name__)

    app.config.update(SECRET_KEY='development-only-change-me',
                      DATABASE=os.environ.get('ACEEST_DB', str(Path(app.instance_path) / 'aceest.sqlite3')));
    app.config.update(config or {});
    Path(app.config['DATABASE']).parent.mkdir(parents=True, exist_ok=True)

    def db():
        if 'db' not in g: g.db = sqlite3.connect(app.config['DATABASE']);g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close(_):
        if (c := g.pop('db', None)): c.close()

    with app.app_context():
        db().executescript(
            "CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT UNIQUE,password TEXT,role TEXT);CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,name TEXT UNIQUE,age INTEGER,height REAL,weight REAL,program TEXT,calories INTEGER,target_weight REAL,target_adherence INTEGER,membership_expiry TEXT);");
        db().execute("INSERT OR IGNORE INTO users(username,password,role)VALUES('admin','admin','Admin')");
        db().commit()

    def auth():
        if 'user' not in session: abort(401)

    def client(cid):
        row = db().execute('SELECT * FROM clients WHERE id=?', (cid,)).fetchone()
        if not row: abort(404)
        return row

    @app.get('/')
    def index():
        if 'user' not in session: return redirect(url_for('login'))
        return render_template('index.html', clients=db().execute('SELECT * FROM clients ORDER BY name').fetchall(),
                               programs=PROGRAMS, user=session['user'])

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            row = db().execute('SELECT * FROM users WHERE username=? AND password=?',
                               (request.form.get('username', ''), request.form.get('password', ''))).fetchone()
            if row: session['user'] = row['username'];session['role'] = row['role'];return redirect(url_for('index'))
            return render_template('login.html', error='Invalid credentials'), 401
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear();
        return redirect(url_for('login'), 303)

    @app.post('/clients')
    def save_client():
        auth();
        n, p = request.form.get('name', '').strip(), request.form.get('program', '')
        if not n or p not in PROGRAMS: return render_template('error.html',
                                                              message='Name and program are required.'), 400
        try:
            a = int(request.form.get('age', 0) or 0);
            h = float(request.form.get('height', 0) or 0);
            w = float(
                request.form.get('weight', 0) or 0)
        except ValueError:
            return render_template('error.html', message='Age, height and weight must be numeric.'), 400
        if min(a, h, w) < 0: return render_template('error.html', message='Profile values cannot be negative.'), 400
        db().execute(
            'INSERT INTO clients(name,age,height,weight,program,calories,target_weight,target_adherence,membership_expiry)VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(name)DO UPDATE SET age=excluded.age,height=excluded.height,weight=excluded.weight,program=excluded.program,calories=excluded.calories,target_weight=excluded.target_weight,target_adherence=excluded.target_adherence,membership_expiry=excluded.membership_expiry',
            (n, a, h, w, p, int(w * PROGRAMS[p][1]), request.form.get('target_weight') or None,
             request.form.get('target_adherence') or None, request.form.get('membership_expiry') or None));
        db().commit();
        cid = db().execute('SELECT id FROM clients WHERE name=?', (n,)).fetchone()['id'];
        return redirect(url_for('detail', cid=cid), 303)

    @app.get('/clients/<int:cid>')
    def detail(cid):
        auth();
        return render_template('detail.html', client=client(cid), programs=PROGRAMS,
                               plan=session.get(f'plan-{cid}'))

    @app.post('/clients/<int:cid>/plan')
    def plan(cid):
        auth();
        c = client(cid);
        level = request.form.get('level', '').lower()
        if level not in ('beginner', 'intermediate', 'advanced'): return render_template('error.html',
                                                                                         message='Choose beginner, intermediate, or advanced.'), 400
        focus = 'Conditioning' if 'Fat Loss' in c['program'] else 'Hypertrophy' if 'Muscle Gain' in c[
            'program'] else 'Full Body';
        days, sets, reps = \
            {'beginner': (3, (2, 3), (8, 12)), 'intermediate': (4, (3, 4), (8, 15)), 'advanced': (5, (4, 5), (6, 15))}[
                level];
        result = []
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][:days]:
            for exercise in random.sample(POOLS[focus], 3 if days < 4 else 4): result.append(
                (day, exercise, random.randint(*sets), random.randint(*reps)))
        session[f'plan-{cid}'] = result;
        return redirect(url_for('detail', cid=cid), 303)

    @app.get('/clients/<int:cid>/report.pdf')
    def report(cid):
        auth();
        c = client(cid);
        pdf = FPDF();
        pdf.add_page();
        pdf.set_font('Helvetica', 'B', 16);
        pdf.cell(0, 10, f'Client Report - {c["name"]}', new_x='LMARGIN', new_y='NEXT');
        pdf.set_font('Helvetica', size=12)
        for label, value in [('Name', c['name']), ('Age', c['age']), ('Height', c['height']), ('Weight', c['weight']),
                             ('Program', PROGRAMS[c['program']][0]),
                             ('Membership Expiry', c['membership_expiry'] or '')]: pdf.cell(0, 8,
                                                                                            f'{label}: {value}'.replace(
                                                                                                '–', '-'),
                                                                                            new_x='LMARGIN',
                                                                                            new_y='NEXT')
        return send_file(BytesIO(bytes(pdf.output())), mimetype='application/pdf', as_attachment=True,
                         download_name=f'{c["name"]}_report.pdf')

    @app.get('/api/clients')
    def api_clients():
        auth();
        return jsonify([dict(x) for x in db().execute('SELECT * FROM clients ORDER BY name')])

    return app


app = create_app()

if __name__ == "__main__":
    app.run()
