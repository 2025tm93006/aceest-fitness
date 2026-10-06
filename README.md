# ACEest Flask version 2.0.1

Migration of `Aceestver2.0.1.py`: SQLite client persistence, client summaries, and weekly progress logging. Saving a matching client name replaces that record, following the source's `INSERT OR REPLACE` behavior.

Run `python -m pytest -q` after installing `requirements-test.txt`. Use `flask --app app run` for local development. Build the test image with `docker build --target test -t aceest-v2.0.1:test .` and run it with `docker run --rm aceest-v2.0.1:test`.

Use `flask-v2.0.1/Jenkinsfile` for a Pipeline from SCM job. The Jenkins agent needs Python 3 and Docker access.

Source issue: the desktop version allows orphan progress rows because its schema has no foreign key. This web migration validates that the client exists before saving progress.
