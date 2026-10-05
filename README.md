# ACEest Fitness Flask version 1.1

This milestone migrates only `Aceestver-1.1.py`. It adds name, age, weight, weekly adherence, weight-based calorie estimates, Save Client confirmation, and Reset to the program viewer. Workout and nutrition text match the 1.1 script exactly. The 1.0 site metrics panel is absent because the supplied 1.1 script removes it.

Save Client only confirms the entered details, as in the original script. Nothing is stored; a fresh visit or Reset clears the form. Client lists, coach notes, CSV export, and progress charts belong to 1.1.2.

## Run and test

From this folder, using Python 3.12 or newer:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -q
flask --app app run
```

Open http://127.0.0.1:5000/. Selecting a program refreshes its plans and calculates `int(weight × calorie_factor)` when weight is positive. View program also works without JavaScript. Save Client requires a name and program. Reset returns to the empty form.

## Docker

```sh
docker build --target test -t aceest-v1.1:test .
docker run --rm aceest-v1.1:test
docker build --target runtime -t aceest-v1.1:runtime .
docker run --rm -p 127.0.0.1:8000:8000 aceest-v1.1:runtime
```

The runtime image serves the app through Gunicorn as a non-root user. Pytest is installed in the test image only.

## Jenkins

Configure a Pipeline from SCM job using script path `flask-v1.1/Jenkinsfile`. It expects this folder inside the repository root. The agent needs Python 3, Docker CLI, and a running Docker daemon. The pipeline checks syntax, builds the two images, and runs the container tests. A repository and Jenkins server must be configured separately.

## API

- `GET /api/programs`: the three program names and IDs.
- `GET /api/programs/<id>?weight=70`: program details and estimated calories. IDs are `fat-loss`, `muscle-gain`, and `beginner`; an omitted or zero weight returns a null estimate.

## Source issues handled

The desktop script can throw conversion errors for invalid numeric inputs and can leave an old calorie estimate visible when weight becomes zero. This port returns a validation message for invalid numbers and clears the estimate at zero. It keeps Save Client as a confirmation and explicitly explains that data is not stored.

