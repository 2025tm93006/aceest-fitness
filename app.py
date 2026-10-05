"""Flask milestone for Aceestver-1.1.py; client data is not persisted."""

import math

from flask import Flask, abort, jsonify, render_template, request

from programs import PROGRAMS


def estimate_calories(weight, program):
    """Use the original int(weight * factor) rule; zero means unspecified."""
    if not math.isfinite(weight) or weight < 0:
        raise ValueError("Weight must be a finite, non-negative number.")
    return int(weight * PROGRAMS[program]["calorie_factor"]) if weight > 0 else None


def create_app():
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        values = {"name": "", "age": "0", "weight": "0", "program": "", "adherence": "0"}
        error = message = None
        calories = None
        if request.method == "POST":
            values.update({key: request.form.get(key, default).strip() for key, default in values.items()})
            try:
                age = int(values["age"] or "0")
                adherence = int(values["adherence"] or "0")
                weight = float(values["weight"] or "0")
                if age < 0 or not 0 <= adherence <= 100:
                    raise ValueError("Age must be non-negative and adherence must be between 0 and 100.")
                if not math.isfinite(weight) or weight < 0:
                    raise ValueError("Weight must be a finite, non-negative number.")
                selected = values["program"]
                if selected and selected not in PROGRAMS:
                    raise ValueError("Choose a valid program.")
                if selected:
                    calories = estimate_calories(weight, selected)
                action = request.form.get("action", "preview")
                if action == "save":
                    if not values["name"] or not selected:
                        raise ValueError("Please fill client name and program.")
                    message = f"Client {values['name']} saved successfully. Adherence: {adherence}%"
                elif action != "preview":
                    raise ValueError("Unknown action.")
            except (ValueError, OverflowError) as exc:
                error = str(exc)
        return render_template(
            "index.html", programs=PROGRAMS, values=values,
            program=PROGRAMS.get(values["program"]), calories=calories,
            error=error, message=message,
        ), 400 if error else 200

    @app.get("/api/programs")
    def list_programs():
        return jsonify([{"id": slug, "name": details["name"]} for slug, details in PROGRAMS.items()])

    @app.get("/api/programs/<slug>")
    def get_program(slug):
        if slug not in PROGRAMS:
            abort(404)
        try:
            calories = estimate_calories(float(request.args.get("weight", "0")), slug)
        except (ValueError, OverflowError):
            return jsonify(error="Weight must be a finite, non-negative number."), 400
        return jsonify(id=slug, **PROGRAMS[slug], estimated_calories=calories)

    return app


app = create_app()

if __name__ == "__main__":
    app.run()

