import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_initial_view_and_reset(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Estimated Calories: --" in response.data
    assert b'value="0"' in response.data
    assert b"Capacity" not in response.data
    client.post("/", data={"name": "Asha", "program": "fat-loss", "weight": "70", "action": "save"})
    reset = client.get("/")
    assert b"Asha" not in reset.data
    assert b"Estimated Calories: --" in reset.data
    assert b"Back Squat" not in reset.data


@pytest.mark.parametrize("slug,calories,workout,diet", [
    ("fat-loss", 1540, "Back Squat 5x5 + Core", "Target: ~2000 kcal"),
    ("muscle-gain", 2450, "Barbell Rows 4x10", "Target: ~3200 kcal"),
    ("beginner", 1820, "Full Body Circuit", "Protein Target: 120g/day"),
])
def test_program_preview_and_calorie_estimate(client, slug, calories, workout, diet):
    response = client.post("/", data={"program": slug, "weight": "70", "action": "preview"})
    assert response.status_code == 200
    assert f"Estimated Calories: {calories} kcal".encode() in response.data
    assert workout.encode() in response.data
    assert diet.encode() in response.data
    api = client.get(f"/api/programs/{slug}?weight=70")
    assert api.status_code == 200
    assert api.json["estimated_calories"] == calories


def test_zero_weight_clears_estimate_and_fractional_weight_truncates(client):
    assert client.get("/api/programs/fat-loss?weight=70.19").json["estimated_calories"] == 1544
    assert client.get("/api/programs/fat-loss?weight=0").json["estimated_calories"] is None
    page = client.post("/", data={"program": "fat-loss", "weight": "0"})
    assert b"Estimated Calories: --" in page.data


def test_save_confirmation_preserves_fields_without_persistence(client):
    response = client.post("/", data={
        "name": "Asha", "age": "25", "weight": "70", "program": "fat-loss",
        "adherence": "85", "action": "save",
    })
    assert response.status_code == 200
    assert b"Client Asha saved successfully. Adherence: 85%" in response.data
    assert b'value="25"' in response.data
    assert b'value="70"' in response.data
    assert b"They are not stored" in response.data
    assert b"Asha" not in client.get("/").data


@pytest.mark.parametrize("data", [
    {"name": "", "program": "fat-loss"},
    {"name": "Asha", "program": ""},
    {"name": "Asha", "program": "unknown"},
    {"name": "Asha", "program": "fat-loss", "adherence": "101"},
    {"name": "Asha", "program": "fat-loss", "age": "abc"},
    {"name": "Asha", "program": "fat-loss", "weight": "nan"},
])
def test_invalid_save_is_rejected(client, data):
    response = client.post("/", data={**data, "action": "save"})
    assert response.status_code == 400
    assert b"saved successfully" not in response.data


def test_user_text_is_escaped(client):
    response = client.post("/", data={"name": "<script>alert(1)</script>", "program": "beginner", "action": "save"})
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_program_api_and_missing_program(client):
    assert len(client.get("/api/programs").json) == 3
    assert client.get("/api/programs/unknown").status_code == 404
    assert client.get("/api/programs/beginner?weight=-1").status_code == 400
    assert client.get("/api/programs/beginner?weight=inf").status_code == 400

