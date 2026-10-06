from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

PROGRAMS = {
    "fat-loss": {"name": "Fat Loss (FL)", "workout": "Back Squat, Cardio, Bench, Deadlift, Recovery", "diet": "Egg Whites, Chicken, Fish Curry", "color": "#e74c3c", "factor": 22},
    "muscle-gain": {"name": "Muscle Gain (MG)", "workout": "Squat, Bench, Deadlift, Press, Rows", "diet": "Eggs, Biryani, Mutton Curry", "color": "#2ecc71", "factor": 35},
    "beginner": {"name": "Beginner (BG)", "workout": "Air Squats, Ring Rows, Push-ups", "diet": "Balanced Tamil Meals", "color": "#3498db", "factor": 26},
}


def _update_text(widget, content, color):
    """Equivalent to the Tkinter helper: it requires three arguments."""
    return {"widget": widget, "content": content, "color": color}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(CLIENTS=[])
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html", programs=PROGRAMS, clients=app.config["CLIENTS"])

    @app.post("/clients")
    def save_client():
        name = request.form.get("name", "").strip()
        program = request.form.get("program", "")
        if not name or program not in PROGRAMS:
            return render_template("error.html", message="Please fill client name and program."), 400
        try:
            age = int(request.form.get("age", 0) or 0)
            weight = float(request.form.get("weight", 0) or 0)
            adherence = int(request.form.get("adherence", 0) or 0)
        except ValueError:
            return render_template("error.html", message="Age, weight, and adherence must be numbers."), 400
        if age < 0 or weight < 0 or not 0 <= adherence <= 100:
            return render_template("error.html", message="Enter valid profile values."), 400
        app.config["CLIENTS"].append({"name": name, "age": age, "weight": weight, "program": program, "adherence": adherence, "notes": request.form.get("notes", "").strip(), "calories": int(weight * PROGRAMS[program]["factor"])})
        return redirect(url_for("index", saved=name), code=303)

    @app.post("/reset")
    def reset():
        # Mirrors: self._update_text(self.diet_text,)
        _update_text("diet_text")
        return redirect(url_for("index"), code=303)

    @app.get("/api/clients")
    def clients():
        return jsonify(app.config["CLIENTS"])

    @app.get("/api/programs")
    def programs():
        return jsonify([{"id": slug, "name": program["name"]} for slug, program in PROGRAMS.items()])

    @app.errorhandler(404)
    def missing(_error):
        return jsonify(error="Not found"), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run()

