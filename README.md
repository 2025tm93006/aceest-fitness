# ACEest Flask version 2.2.1

Migration of `Aceestver-2.2.1.py`. It adds a client-specific weekly adherence chart to the SQLite client and progress features from 2.1.2. **View Progress Chart** opens a separate browser window and renders a line chart with point markers, matching the original Matplotlib popup.

Run `python -m pytest -q` after installing `requirements-test.txt`. Jenkins script: `flask-v2.2.1/Jenkinsfile`. Docker test: `docker build --target test -t aceest-v2.2.1:test . && docker run --rm aceest-v2.2.1:test`.

Source issue: weeks use `Week %U - %Y`, so logging more than one entry in the same week creates multiple points with the same label. This migration preserves that behavior.
