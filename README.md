# ACEest Flask version 3.2.4

Migration of `Aceestver-3.2.4.py`: login, add/save client, generated program, membership check, and workout logging. Demo login remains `admin` / `admin` for source compatibility.

Run `python -m pytest -q` after installing `requirements-test.txt`. Jenkins path: `flask-v3.2.4/Jenkinsfile`. Docker test: `docker build --target test -t aceest-v3.2.4:test . && docker run --rm aceest-v3.2.4:test`.

Source issues: it calls `tk.simpledialog` without importing `simpledialog`, stores credentials in plaintext, and has unused `exercises`/`metrics` tables. This migration replaces the broken dialog with a form, preserves the simple demo account, and implements the features exposed in this version's UI.
