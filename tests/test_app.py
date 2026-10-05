import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_home_starts_with_original_placeholders_and_site_metrics(client):
    page = client.get("/")
    assert page.status_code == 200
    assert b"Select a profile to view workout" in page.data
    assert b"Select a profile to view diet" in page.data
    assert b"150 users" in page.data
    assert b"10,000 sq ft" in page.data
    assert b"250 members" in page.data


@pytest.mark.parametrize(
    ("slug", "name", "workout", "diet", "color"),
    [
        ("fat-loss", "Fat Loss (FL)", "5x5 Back Squat + AMRAP", "Oats Idli", "#e74c3c"),
        ("muscle-gain", "Muscle Gain (MG)", "Barbell Rows 4x10", "Mutton Curry", "#2ecc71"),
        ("beginner", "Beginner (BG)", "Technique Mastery", "Balanced Tamil Meals", "#3498db"),
    ],
)
def test_each_version_1_program_is_available_in_browser_and_api(
    client, slug, name, workout, diet, color
):
    page = client.get("/", query_string={"program": slug})
    assert page.status_code == 200
    assert workout.encode() in page.data
    assert diet.encode() in page.data
    assert color.encode() in page.data

    response = client.get(f"/api/programs/{slug}")
    assert response.status_code == 200
    data = response.get_json()
    assert data["name"] == name
    assert workout in data["workout"]
    assert diet in data["diet"]
    assert data["color"] == color


def test_program_list_and_site_metrics_api(client):
    programs = client.get("/api/programs").get_json()
    assert [item["id"] for item in programs] == ["fat-loss", "muscle-gain", "beginner"]
    assert client.get("/api/site-metrics").get_json() == {
        "capacity_users": 150,
        "area_sq_ft": 10_000,
        "break_even_members": 250,
    }


def test_unknown_program_is_not_found_and_api_is_read_only(client):
    assert client.get("/", query_string={"program": "unknown"}).status_code == 404
    assert client.get("/api/programs/unknown").status_code == 404
    assert client.post("/api/programs").status_code == 405
