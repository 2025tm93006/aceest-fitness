FROM python:3.12-slim AS base
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && groupadd --system aceest && useradd --system --gid aceest aceest
COPY app.py ./
COPY templates ./templates
COPY static ./static
RUN chown -R aceest:aceest /app
USER aceest
FROM base AS test
USER root
COPY requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt
COPY tests ./tests
USER aceest
CMD ["python","-m","pytest","-q"]
FROM base AS runtime
EXPOSE 8000
CMD ["gunicorn","--bind","0.0.0.0:8000","app:app"]
