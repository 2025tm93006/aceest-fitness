import pytest
from app import create_app

@pytest.fixture
def client(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")}).test_client()

def save(client, **extra):
    data={"name":"Asha","age":"25","weight":"70","program":"fat-loss"}; data.update(extra)
    return client.post("/clients",data=data)

def test_save_load_and_calories(client):
    response=save(client)
    assert response.status_code==303
    page=client.get(response.headers["Location"])
    assert b"Asha" in page.data and b"1540 kcal/day" in page.data
    assert client.get("/api/clients").json[0]["calories"]==1540

def test_replaces_client_by_name(client):
    save(client,weight="70")
    save(client,weight="80",program="muscle-gain")
    rows=client.get("/api/clients").json
    assert len(rows)==1 and rows[0]["calories"]==2800

def test_save_progress_uses_current_week_and_lists_it(client):
    save(client)
    assert client.post("/progress",data={"name":"Asha","adherence":"83"}).status_code==303
    assert client.get("/api/clients/Asha/progress").json[0]["adherence"]==83

@pytest.mark.parametrize("data",[{"name":"","program":"fat-loss"},{"name":"Asha","program":"bad"},{"name":"Asha","program":"fat-loss","weight":"-1"}])
def test_invalid_client_rejected(client,data):
    assert client.post("/clients",data=data).status_code==400

def test_invalid_progress_and_unknown_client(client):
    assert client.post("/progress",data={"name":"Missing","adherence":"101"}).status_code==400
    assert client.get("/api/clients/Missing/progress").status_code==404
