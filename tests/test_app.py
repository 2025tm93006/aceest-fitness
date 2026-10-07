import pytest
from app import create_app
@pytest.fixture
def client(tmp_path):return create_app({'TESTING':True,'DATABASE':str(tmp_path/'test.db')}).test_client()
def save(c):return c.post('/clients',data={'name':'Asha','age':'25','weight':'70','program':'fat-loss'})
def test_chart_includes_each_logged_week(client):
 save(client);client.post('/progress',data={'name':'Asha','adherence':'20'});client.post('/progress',data={'name':'Asha','adherence':'90'})
 page=client.get('/?name=Asha');assert b'20%' in page.data and b'90%' in page.data
def test_chart_api_is_client_specific(client):
 save(client);client.post('/progress',data={'name':'Asha','adherence':'70'});assert client.get('/api/clients/Asha/progress').json[0]['adherence']==70
def test_empty_chart_and_bad_progress(client):
 save(client);assert b'No progress data' in client.get('/?name=Asha').data;assert client.post('/progress',data={'name':'Asha','adherence':'200'}).status_code==400
