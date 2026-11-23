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

The [Jenkinsfile](Jenkinsfile) polls Git every five minutes, runs Pytest inside the
Docker test image, and publishes the JUnit results when a report is available.
SonarQube analyzes the source and imports the Python coverage report. SonarScanner
polls SonarQube for the quality gate result for up to ten minutes. On `master`,
Jenkins builds and pushes the runtime image only after the quality gate passes.
The exact image tag is saved in the build artifact `ci-reports/image.txt`.

#### Jenkins setup

1. Install the **Pipeline**, **Git**, **JUnit**, **Credentials Binding**, and
   **SonarQube Scanner** plugins. Run the job on a Linux agent with Git, a Docker
   CLI with BuildKit, and access to a running Docker daemon through the default
   socket or `DOCKER_HOST`. Run `docker info` as the agent's service account to
   verify access. The agent must be able to reach GitHub, SonarQube, and Docker Hub.
2. Create a **Pipeline** job using **Pipeline script from SCM**, select **Git**,
   set the branch to `*/master`, and set the script path to `Jenkinsfile`.
   Use a GitHub checkout credential if the repository requires authentication.
   Run the job once to register the polling schedule.
3. Create the SonarQube project with key `aceest-fitness` and assign its quality
   gate. In **Manage Jenkins → Credentials**, store a SonarQube analysis token as
   **Secret text**. In **Manage Jenkins → System → SonarQube servers**, add an
   installation named `SonarQube` with the server URL and that credential.
   In **Manage Jenkins → Tools**, add a SonarScanner CLI installation named
   `SonarScanner`.
4. Create an `aceest-fitness` repository in your Docker Hub user or organization
   namespace. In **Manage Jenkins → System → Global properties → Environment
   variables**, set `DOCKERHUB_NAMESPACE` to that namespace. Add a **Username
   with password** credential with ID `dockerhub-credentials`. Use your Docker
   Hub username and an access token with permission to push to the repository.

After a successful `master` run, check the Jenkins test results, the SonarQube
quality gate status, and the Docker Hub tag. The tag format is
`docker.io/<namespace>/aceest-fitness:build-<jenkins-build-number>-<12-character-commit>`.

### GitHub Actions

The workflow at [.github/workflows/ci.yml](.github/workflows/ci.yml) runs on pushes and pull requests targeting `master`. It:

1. Uses Python 3.12.
2. Installs `requirements.txt`.
3. Compiles the application and tests.
4. Runs pytest.
5. Builds and tests the Docker `test` image.
6. Builds the Docker `runtime` image.

## Deploy to Minikube

Start Docker and run `minikube start --driver=docker` with Minikube and
`kubectl` installed. Download `ci-reports/image.txt` from a successful Jenkins
`master` build. It contains the published Docker Hub image reference. Run
the following from the repository root and adjust the artifact path if needed.

```bash
ACEEST_IMAGE="$(cat "$HOME/Downloads/image.txt")"
kubectl --context minikube apply -f k8s/pvc.yaml -f k8s/service.yaml
kubectl --context minikube set image --local -f k8s/deployment.yaml aceest-fitness="$ACEEST_IMAGE" -o yaml |
  kubectl --context minikube apply -f -
kubectl --context minikube rollout status deployment/aceest-fitness --timeout=180s
kubectl --context minikube get pods,service,pvc -l app.kubernetes.io/name=aceest-fitness
```

The pod should be `1/1` ready and the claim should be `Bound`. The baseline uses
one replica and the `Recreate` strategy so only one pod writes to the SQLite
database. The persistent volume keeps data across pod replacement. This setup
assumes the cluster can pull the Docker Hub image.

Forward the Service to your machine and leave that terminal running.

```bash
kubectl --context minikube port-forward service/aceest-fitness 8081:80
```

In another terminal, verify the login route returns HTTP 200.

```bash
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8081/login
```

Open `http://localhost:8081/login` in a browser. This forwarded endpoint is
for local verification. If the pod fails to start, check the Events section
with `kubectl --context minikube describe pods -l app.kubernetes.io/name=aceest-fitness`.
For image pull errors, check the published tag, the repository's pull
permissions, and whether the image supports the Minikube node's architecture.

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
