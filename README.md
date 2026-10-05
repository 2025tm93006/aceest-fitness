# ACEest Fitness Flask version 1.0

This folder ports **only** `Aceestver-1.0.py` to Flask. It provides the original three fixed programs, their workout and nutrition text, program colors, and site metrics. Version 1.0 has no client persistence, calorie calculation, adherence tracking, or database; those belong to later milestones.

## Run locally

From `flask-v1.0` with Python 3.12 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
flask --app app run
```

Open http://127.0.0.1:5000/ and select a program. This uses Flask's local development server.

## Test

```sh
python -m pytest -q
python -m compileall -q app.py tests
```

The tests verify initial placeholders, all three programs, site metrics, missing-program behavior, and read-only endpoints.

## Docker

With a running Docker daemon, from `flask-v1.0`:

```sh
docker build --target test -t aceest-v1:test .
docker run --rm aceest-v1:test
docker build --target runtime -t aceest-v1:runtime .
docker run --rm -p 127.0.0.1:8000:8000 aceest-v1:runtime
```

Open http://127.0.0.1:8000/. The runtime image runs Gunicorn as a non-root user; Pytest is installed only in the test image.

## Read-only service endpoints

| Method | Path | Response |
| --- | --- | --- |
| GET | `/api/programs` | Program names and IDs |
| GET | `/api/programs/<id>` | Workout, diet, and color for one program |
| GET | `/api/site-metrics` | Capacity, area, and break-even values |

Program IDs are `fat-loss`, `muscle-gain`, and `beginner`.

## Jenkins setup

The `Jenkinsfile` is ready for a Pipeline job that checks out a repository containing this folder. Set the Pipeline script path to `Jenkinsfile`. The Jenkins agent needs Python 3, Docker CLI, and access to a running Docker daemon. The pipeline compiles source, builds test and runtime images, and runs Pytest inside the test image.

No Git repository or Jenkins server is created by this milestone. The assignment's GitHub connection and GitHub Actions workflow can be added when those stages are authorized.
