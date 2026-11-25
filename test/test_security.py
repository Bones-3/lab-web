import pytest
import init_db
import app as appmod

@pytest.fixture
def client():
    init_db.crear_base_de_datos()      # base limpia en cada prueba
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()

def test_login_rechaza_sql_injection(client):
    r = client.post("/login", data={"username": "admin' --", "password": "x"})
    assert r.status_code == 401        # debe denegar, no entrar

def test_login_valido(client):
    r = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 302        # redirige al dashboard

def test_dashboard_sin_sesion_redirige(client):
    r = client.get("/dashboard")
    assert r.status_code == 302