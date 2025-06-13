import os
import importlib
import pytest
from werkzeug.security import check_password_hash


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
            'notify_by_email': True,
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


def test_password_reset_flow(monkeypatch):
    app, db = create_test_app()

    with app.app_context():
        register_data = {
            'name': 'Tester',
            'email': 'tester@example.com',
            'password': 'secret',
            'accept_rules': True,
            'notify_by_email': True,
            'submit': 'Sign Me Up!'
        }
        app.test_client().post('/register', data=register_data, follow_redirects=True)

        captured = {}

        def fake_send_email(to_addr, subject, body):
            captured['body'] = body

        monkeypatch.setattr(importlib.import_module('main'), 'send_email', fake_send_email)

        request_data = {
            'email': 'tester@example.com',
            'submit': 'Send Reset Link'
        }
        app.test_client().post('/reset-password', data=request_data, follow_redirects=True)

        token = captured['body'].split('/')[-1].strip()

        reset_data = {
            'password': 'newsecret',
            'confirm': 'newsecret',
            'submit': 'Reset Password'
        }
        response = app.test_client().post(f'/reset/{token}', data=reset_data, follow_redirects=True)

        assert response.status_code == 200
        user = db.session.execute(db.select(importlib.import_module('main').User).where(importlib.import_module('main').User.email == 'tester@example.com')).scalar()
        assert user and importlib.import_module('main').check_password_hash(user.password, 'newsecret')


def test_new_post_notification_trigger(monkeypatch):
    app, db = create_test_app()

    with app.app_context():
        client = app.test_client()
        reg = {
            'name': 'Admin',
            'email': 'admin@example.com',
            'password': 'secret',
            'accept_rules': True,
            'notify_by_email': True,
            'submit': 'Sign Me Up!'
        }
        client.post('/register', data=reg, follow_redirects=True)
        login_data = {
            'email': 'admin@example.com',
            'password': 'secret',
            'submit': 'Let Me In!'
        }
        client.post('/login', data=login_data, follow_redirects=True)

        triggered = {}

        def fake_notify(post):
            triggered['called'] = True

        monkeypatch.setattr(importlib.import_module('main'), 'send_new_post_notification', fake_notify)

        post_data = {
            'title': 'Test',
            'subtitle': 'Sub',
            'img_url': 'http://example.com/img.jpg',
            'body': 'Body',
            'submit': 'Submit Post'
        }
        client.post('/new-post', data=post_data, follow_redirects=True)

        assert triggered.get('called')


def test_comment_notification_trigger(monkeypatch):
    app, db = create_test_app()

    with app.app_context():
        client = app.test_client()
        reg_admin = {
            'name': 'Admin',
            'email': 'admin@example.com',
            'password': 'secret',
            'accept_rules': True,
            'notify_by_email': True,
            'submit': 'Sign Me Up!'
        }
        client.post('/register', data=reg_admin, follow_redirects=True)
        client.post('/login', data={'email': 'admin@example.com', 'password': 'secret', 'submit': 'Let Me In!'}, follow_redirects=True)
        post_data = {
            'title': 'First',
            'subtitle': 'Sub',
            'img_url': 'http://example.com/img.jpg',
            'body': 'Body',
            'submit': 'Submit Post'
        }
        client.post('/new-post', data=post_data, follow_redirects=True)
        client.get('/logout')

        reg_user = {
            'name': 'User',
            'email': 'user@example.com',
            'password': 'secret',
            'accept_rules': True,
            'notify_by_email': True,
            'submit': 'Sign Me Up!'
        }
        client.post('/register', data=reg_user, follow_redirects=True)
        client.post('/login', data={'email': 'user@example.com', 'password': 'secret', 'submit': 'Let Me In!'}, follow_redirects=True)

        triggered = {}

        def fake_notify(comment):
            triggered['called'] = True

        monkeypatch.setattr(importlib.import_module('main'), 'send_comment_notification', fake_notify)

        client.post('/post/1', data={'comment_text': 'Hi', 'submit': 'Submit Comment'}, follow_redirects=True)

        assert triggered.get('called')

