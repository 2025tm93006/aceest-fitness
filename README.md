# ACEest Fitness

Flask web migration of the final desktop application version, `Aceestver-3.2.4.py`. 

## Functionality

- Login and logout using the assignment demo account.
- Create and select clients from the dashboard.
- Dashboard client actions that match the final Tkinter version:
  - **Add / Save Client**
  - **Generate AI Program**
  - **Generate PDF Report**
  - **Check Membership**
- Generate either an automatically selected workout program from the dashboard or a selected program type from the client detail page.
- Download a client PDF report.
- Check membership status and renewal date in the browser or through a JSON endpoint.
- Log and view workouts with date, type, duration, and notes.
- Persist users, clients, programs, membership fields, progress records, and workouts in SQLite.

## Demo login

| Field | Value |
| --- | --- |
| Username | `admin` |
| Password | `admin` |

## Requirements

- Python 3.9 or later
- pip
- Docker, optional for the container workflow

Runtime dependencies are maintained in [requirements.txt](requirements.txt).

## Run locally

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the development server:

```bash
python app.py
```

Open `http://127.0.0.1:5000` and sign in with the demo account.

By default, the SQLite database is created at `instance/aceest.sqlite3`. Set `ACEEST_DB` to use a different database location:

```bash
ACEEST_DB=/path/to/aceest.sqlite3 python app.py
```

## Tests

Run the test suite from the repository root:

```bash
python -m pytest -q
```

The tests cover authentication, the four dashboard actions, program generation, membership, PDF generation, workout logging, and invalid form data.

## Docker

The [Dockerfile](Dockerfile) uses two stages:

- `test` installs the application dependencies and test suite, then runs pytest.
- `runtime` packages the application behind Gunicorn on port `8000`.

Build and run tests in the container:

```bash
docker build --target test -t aceest:test .
docker run --rm aceest:test
```

Build and run the application image:

```bash
docker build --target runtime -t aceest:runtime .
docker run --rm -p 8000:8000 aceest:runtime
```

Open `http://127.0.0.1:8000` when the runtime container is running.

## Continuous integration

### Jenkins

The [Jenkinsfile](Jenkinsfile) performs these stages:

1. Check out the repository.
2. Create `.venv` and install `requirements-test.txt`.
3. Run `python -m pytest -q` from that virtual environment.

The current pipeline uses SCM polling every five minutes:

```groovy
pollSCM('H/5 * * * *')
```

### GitHub Actions

The workflow at [.github/workflows/ci.yml](.github/workflows/ci.yml) runs on pushes and pull requests targeting `master`. It:

1. Uses Python 3.12.
2. Installs `requirements.txt`.
3. Compiles the application and tests.
4. Runs pytest.
5. Builds and tests the Docker `test` image.
6. Builds the Docker `runtime` image.

## Main routes

| Route | Purpose |
| --- | --- |
| `/login` | Sign in page and login submission |
| `/` | Authenticated dashboard and client selection |
| `/clients` | Create a client |
| `/clients/<id>` | Client details and workout form |
| `/clients/<id>/program` | Generate a selected program type |
| `/clients/<id>/program/auto` | Generate a random program, matching the desktop action |
| `/clients/<id>/report.pdf` | Download a PDF client report |
| `/clients/<id>/membership?view=page` | Show membership details in the browser |
| `/clients/<id>/membership` | Membership JSON response |
| `/clients/<id>/workouts` | Save a workout entry |

## Project layout

```text
.
├── app.py                    Flask application and routes
├── templates/                Jinja templates
├── static/                   Stylesheet
├── tests/test_app.py         Automated tests
├── requirements.txt          Runtime dependencies
├── Dockerfile                Test and runtime container stages
├── Jenkinsfile               Jenkins pipeline
└── .github/workflows/ci.yml  GitHub Actions workflow
```
