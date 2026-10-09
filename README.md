# ACEest Flask version 2.2.4

Migration of `Aceestver-2.2.4.py`: expanded client profiles and goals, SQLite persistence, weekly adherence, BMI, body metrics, workouts, optional exercises, and workout history.

Run `python -m pytest -q` after installing `requirements-test.txt`. Jenkins path: `flask-v2.2.4/Jenkinsfile`. Docker test: `docker build --target test -t aceest-v2.2.4:test . && docker run --rm aceest-v2.2.4:test`.

Source issue: this desktop version may drop an existing `clients` table if its schema is older. This migration uses additive `CREATE TABLE IF NOT EXISTS` setup and does not delete existing client data.
