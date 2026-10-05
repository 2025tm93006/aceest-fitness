"""Flask port of Aceestver-1.0.py's read-only program viewer."""

from flask import Flask, abort, jsonify, render_template, request


PROGRAMS = {
    "fat-loss": {
        "name": "Fat Loss (FL)",
        "workout": "Mon: 5x5 Back Squat + AMRAP\nTue: EMOM 20min Assault Bike\nWed: Bench Press + 21-15-9\nThu: 10RFT Deadlifts/Box Jumps\nFri: 30min Active Recovery",
        "diet": "B: 3 Egg Whites + Oats Idli\nL: Grilled Chicken + Brown Rice\nD: Fish Curry + Millet Roti\nTarget: 2,000 kcal",
        "color": "#e74c3c",
    },
    "muscle-gain": {
        "name": "Muscle Gain (MG)",
        "workout": "Mon: Squat 5x5\nTue: Bench 5x5\nWed: Deadlift 4x6\nThu: Front Squat 4x8\nFri: Incline Press 4x10\nSat: Barbell Rows 4x10",
        "diet": "B: 4 Eggs + PB Oats\nL: Chicken Biryani (250g Chicken)\nD: Mutton Curry + Jeera Rice\nTarget: 3,200 kcal",
        "color": "#2ecc71",
    },
    "beginner": {
        "name": "Beginner (BG)",
        "workout": "Circuit Training: Air Squats, Ring Rows, Push-ups.\nFocus: Technique Mastery & Form (90% Threshold)",
        "diet": "Balanced Tamil Meals: Idli-Sambar, Rice-Dal, Chapati.\nProtein: 120g/day",
        "color": "#3498db",
    },
}

SITE_METRICS = {
    "capacity_users": 150,
    "area_sq_ft": 10_000,
    "break_even_members": 250,
}


def create_app():
    app = Flask(__name__)

    @app.get("/")
    def index():
        selected = request.args.get("program")
        if selected is not None and selected not in PROGRAMS:
            abort(404)
        return render_template(
            "index.html",
            programs=PROGRAMS,
            selected=selected,
            program=PROGRAMS.get(selected),
            metrics=SITE_METRICS,
        )

    @app.get("/api/programs")
    def list_programs():
        return jsonify([
            {"id": slug, "name": details["name"]}
            for slug, details in PROGRAMS.items()
        ])

    @app.get("/api/programs/<slug>")
    def get_program(slug):
        details = PROGRAMS.get(slug)
        if details is None:
            abort(404)
        return jsonify({"id": slug, **details})

    @app.get("/api/site-metrics")
    def site_metrics():
        return jsonify(SITE_METRICS)

    return app


app = create_app()

if __name__ == "__main__":
    app.run()
