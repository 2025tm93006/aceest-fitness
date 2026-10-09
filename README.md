# ACEest Flask version 3.1.2

Migration of `Aceestver-3.1.2.py`: login, SQLite client profiles with membership expiry, generated workout programs, and PDF reports. Use the source's demo login `admin` / `admin`.

Run `python -m pytest -q` after installing `requirements-test.txt`. Jenkins script path: `flask-v3.1.2/Jenkinsfile`. Docker test: `docker build --target test -t aceest-v3.1.2:test . && docker run --rm aceest-v3.1.2:test`.

Source issues: the original stores the admin password in plaintext, starts a Tkinter login window using blocking nested event loops, and has no authorization checks after login. This migration keeps the assigned demo credential for parity but uses request-based login protection. The next production stage should hash passwords and add CSRF protection.
