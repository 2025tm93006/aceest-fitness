import pytest
from app import create_app


@pytest.fixture
def client(tmp_path): return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'x.db')}).test_client()


def make(c): return c.post('/clients',
                           data={'name': 'Asha', 'age': '25', 'height': '165', 'weight': '70', 'program': 'fat-loss-3',
                                 'target_weight': '65', 'target_adherence': '80'})


def test_profile_summary_and_bmi(client):
    r = make(client);
    assert r.status_code == 303;
    p = client.get(r.headers['Location']);
    assert b'1540 kcal/day' in p.data and b'25.7' in p.data


def test_progress_metrics_workout_and_exercise(client):
    r = make(client);
    url = r.headers['Location'];
    cid = url.rsplit('/', 1)[1]
    assert client.post(f'/clients/{cid}/progress', data={'adherence': '75'}).status_code == 303
    assert client.post(f'/clients/{cid}/metrics',
                       data={'date': '2026-01-01', 'weight': '69', 'waist': '80', 'bodyfat': '22'}).status_code == 303
    assert client.post(f'/clients/{cid}/workouts',
                       data={'date': '2026-01-01', 'type': 'Strength', 'duration': '45', 'exercise': 'Squat',
                             'sets': '3', 'reps': '8', 'exercise_weight': '50'}).status_code == 303
    page = client.get(url);
    assert b'Squat' in page.data and b'75%' in page.data


def test_invalid_profile_and_history(client):
    assert client.post('/clients', data={'name': '', 'program': 'fat-loss-3'}).status_code == 400
    assert client.get('/api/clients').json == []
