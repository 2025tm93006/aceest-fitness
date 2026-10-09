import pytest
from app import create_app
@pytest.fixture
def client(tmp_path):return create_app({'TESTING':True,'SECRET_KEY':'test','DATABASE':str(tmp_path/'x.db')}).test_client()
def login(c):return c.post('/login',data={'username':'admin','password':'admin'})
def add(c):return c.post('/clients',data={'name':'Asha','age':'25','height':'165','weight':'70','program':'fat-loss','membership_expiry':'2027-01-01'})
def test_login_and_protected_dashboard(client):
 assert client.get('/').status_code==302
 assert login(client).status_code==302
 assert client.get('/').status_code==200
def test_invalid_login(client):assert client.post('/login',data={'username':'admin','password':'wrong'}).status_code==401
def test_client_plan_and_pdf(client):
 login(client);r=add(client);assert r.status_code==303;url=r.headers['Location'];assert b'Asha'in client.get(url).data
 assert client.post(url+'/plan',data={'level':'intermediate'}).status_code==303
 pdf=client.get(url+'/report.pdf');assert pdf.status_code==200 and pdf.mimetype=='application/pdf' and pdf.data.startswith(b'%PDF')
def test_invalid_program_level(client):
 login(client);url=add(client).headers['Location'];assert client.post(url+'/plan',data={'level':'bad'}).status_code==400
