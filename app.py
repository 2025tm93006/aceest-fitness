"""Flask migration of Aceestver-3.2.4.py."""
import os, random, sqlite3
from io import BytesIO
from datetime import date
from pathlib import Path
from flask import Flask, abort, g, redirect, render_template, request, send_file, session, url_for
from fpdf import FPDF

PROGRAMS = {"Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
            "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
            "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]}
TYPES = ("Strength", "Hypertrophy", "Cardio", "Mobility")


def create_app(config=None):
    app = Flask(__name__);
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
            "CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,password TEXT,role TEXT);CREATE TABLE IF NOT EXISTS clients(id INTEGER PRIMARY KEY,name TEXT UNIQUE,age INTEGER,height REAL,weight REAL,program TEXT,calories INTEGER,target_weight REAL,target_adherence INTEGER,membership_status TEXT,membership_end TEXT);CREATE TABLE IF NOT EXISTS progress(id INTEGER PRIMARY KEY,client_name TEXT,week TEXT,adherence INTEGER);CREATE TABLE IF NOT EXISTS workouts(id INTEGER PRIMARY KEY,client_name TEXT,date TEXT,workout_type TEXT,duration_min INTEGER,notes TEXT);");
        db().execute("INSERT OR IGNORE INTO users VALUES('admin','admin','Admin')");
        db().commit()

    def auth():
        if 'user' not in session: abort(401)

    def client(cid):
        c = db().execute('SELECT * FROM clients WHERE id=?', (cid,)).fetchone()
        if not c: abort(404)
        return c

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            u, p = request.form.get('username', ''), request.form.get('password', '');
            row = db().execute('SELECT role FROM users WHERE username=? AND password=?', (u, p)).fetchone()
            if row: session['user'] = u;session['role'] = row['role'];return redirect(url_for('index'))
            return render_template('login.html', error='Invalid credentials'), 401
        return render_template('login.html')

    @app.post('/logout')
    def logout():
        session.clear();return redirect(url_for('login'), 303)

    @app.get('/')
    def index():
        if 'user' not in session: return redirect(url_for('login'))
        selected_id = request.args.get('client_id', type=int)
        selected_client = client(selected_id) if selected_id is not None else None
        return render_template('index.html', clients=db().execute('SELECT * FROM clients ORDER BY name').fetchall(),
                               role=session['role'], selected_client=selected_client)

    @app.post('/clients')
    def add_client():
        auth();
        name = request.form.get('name', '').strip()
        if not name: return render_template('error.html', message='Client name is required.'), 400
        db().execute("INSERT OR IGNORE INTO clients(name,membership_status)VALUES(?,?)", (name, 'Active'));
        db().commit();
        c = db().execute('SELECT id FROM clients WHERE name=?', (name,)).fetchone();
        return redirect(url_for('detail', cid=c['id']), 303)

    @app.get('/clients/<int:cid>')
    def detail(cid):
        auth();
        c = client(cid);
        workouts = db().execute('SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC,id DESC',
                                (c['name'],)).fetchall();
        progress = db().execute('SELECT * FROM progress WHERE client_name=? ORDER BY id', (c['name'],)).fetchall();
        return render_template('detail.html', c=c, workouts=workouts, progress=progress, types=TYPES,
                               today=date.today().isoformat())

    @app.post('/clients/<int:cid>/program')
    def generate_program(cid):
        auth();
        c = client(cid);
        kind = request.form.get('kind', '')
        if kind not in PROGRAMS: return render_template('error.html', message='Choose a valid program type.'), 400
        p = random.choice(PROGRAMS[kind]);
        db().execute('UPDATE clients SET program=? WHERE id=?', (p, cid));
        db().commit();
        return redirect(url_for('detail', cid=cid), 303)

    @app.post('/clients/<int:cid>/program/auto')
    def generate_program_automatically(cid):
        auth();
        client(cid)
        kind = random.choice(list(PROGRAMS))
        db().execute('UPDATE clients SET program=? WHERE id=?', (random.choice(PROGRAMS[kind]), cid));
        db().commit();
        return redirect(url_for('index', client_id=cid), 303)

    @app.get('/clients/<int:cid>/report.pdf')
    def report(cid):
        auth();
        c = client(cid)
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, f'ACEest Client Report - {c["name"]}', new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', size=12)
        for label, value in [('Name', c['name']), ('Age', c['age']), ('Height', c['height']),
                             ('Weight', c['weight']), ('Program', c['program']), ('Calories', c['calories']),
                             ('Target Weight', c['target_weight']), ('Target Adherence', c['target_adherence']),
                             ('Membership', c['membership_status']), ('Membership End', c['membership_end'])]:
            pdf.cell(0, 8, f'{label}: {value if value is not None else "N/A"}',
                     new_x='LMARGIN', new_y='NEXT')
        return send_file(BytesIO(bytes(pdf.output())), mimetype='application/pdf', as_attachment=True,
                         download_name=f'{c["name"]}_report.pdf')

    @app.post('/clients/<int:cid>/workouts')
    def add_workout(cid):
        auth();
        c = client(cid);
        typ = request.form.get('type', '')
        if typ not in TYPES: return render_template('error.html', message='Choose a valid workout type.'), 400
        try:
            d = date.fromisoformat(request.form.get('date', '')).isoformat();duration = int(
                request.form.get('duration', 0))
        except ValueError:
            return render_template('error.html', message='Enter a valid date and duration.'), 400
        if duration < 1: return render_template('error.html', message='Duration must be positive.'), 400
        db().execute('INSERT INTO workouts(client_name,date,workout_type,duration_min,notes)VALUES(?,?,?,?,?)',
                     (c['name'], d, typ, duration, request.form.get('notes', '').strip()));
        db().commit();
        return redirect(url_for('detail', cid=cid), 303)

    @app.get('/clients/<int:cid>/membership')
    def membership(cid):
        auth();
        c = client(cid)
        if request.args.get('view') == 'page':
            return render_template('membership.html', client=c)
        return {'status': c['membership_status'], 'renewal_date': c['membership_end']}

    return app


app = create_app()


if __name__ == '__main__':
 app.run()
