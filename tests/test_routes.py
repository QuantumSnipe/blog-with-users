import os
import importlib
import pytest


def create_test_app():
    os.environ.setdefault('DATABASE_URL', '')
    import main
    importlib.reload(main)
    app = main.app
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:'
    )
    # reset engines and create tables for in-memory DB
    if 'sqlalchemy' in app.extensions and 'engines' in app.extensions['sqlalchemy']:
        app.extensions['sqlalchemy']['engines'] = {}
    with app.app_context():
        main.db.create_all()
    return app, main.db


@pytest.fixture
def client():
    app, _ = create_test_app()
    return app.test_client()


def test_root_route(client):
    response = client.get('/')
    assert response.status_code == 200


def test_login_page_renders(client):
    response = client.get('/login')
    assert b'<h1>Log In</h1>' in response.data


def test_register_and_login(client):
    app, db = create_test_app()
    with app.app_context():
        register_data = {
            'name': 'Tester',
            'email': 'tester@example.com',
            'password': 'secret',
            'accept_rules': True,
            'submit': 'Sign Me Up!'
        }
        response = app.test_client().post('/register', data=register_data, follow_redirects=True)
        assert response.status_code == 200
        assert db.session.query(main.User).count() == 1

        login_data = {
            'email': 'tester@example.com',
            'password': 'secret',
            'submit': 'Let Me In!'
        }
        response = app.test_client().post('/login', data=login_data, follow_redirects=True)
        assert response.status_code == 200
