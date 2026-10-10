import pytest
from app import create_app
@pytest.fixture
def client(tmp_path):return create_app({'TESTING':True,'SECRET_KEY':'test','DATABASE':str(tmp_path/'x.db')}).test_client()
def login(c):return c.post('/login',data={'username':'admin','password':'admin'})
def add(c):return c.post('/clients',data={'name':'Asha'})
def test_login_and_client_dashboard(client):
 assert client.get('/').status_code==302;assert login(client).status_code==302;r=add(client);assert r.status_code==303
 page=client.get(r.headers['Location'].replace('/clients/', '/?client_id='));assert b'Asha'in page.data
 assert b'Add / Save Client'in page.data and b'Generate AI Program'in page.data
 assert b'Generate PDF Report'in page.data and b'Check Membership'in page.data
def test_program_membership_and_workout(client):
 login(client);url=add(client).headers['Location'];assert client.post(url+'/program',data={'kind':'Fat Loss'}).status_code==303
 assert client.post(url+'/workouts',data={'date':'2026-01-01','type':'Strength','duration':'45','notes':'Good'}).status_code==303
 assert b'Good'in client.get(url).data;assert client.get(url+'/membership').json['status']=='Active'
 assert b'Membership'in client.get(url+'/membership?view=page').data
 pdf=client.get(url+'/report.pdf');assert pdf.status_code==200 and pdf.mimetype=='application/pdf' and pdf.data.startswith(b'%PDF')

def test_dashboard_auto_program_button(client):
 login(client);url=add(client).headers['Location'];assert client.post(url+'/program/auto').status_code==303
 assert b'Program:' in client.get(url.replace('/clients/', '/?client_id=')).data
def test_invalid_login_and_workout(client):
 assert client.post('/login',data={'username':'admin','password':'bad'}).status_code==401
 login(client);url=add(client).headers['Location'];assert client.post(url+'/workouts',data={'date':'bad','type':'Strength','duration':'0'}).status_code==400
