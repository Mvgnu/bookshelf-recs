import os
import sys
import tempfile
import json
import pytest
from datetime import datetime, timezone
import jwt

os.environ.setdefault('SECRET_KEY', 'test-secret')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app import app, db, limiter

@app.route('/error-test')
def error_test_route():
    raise Exception('boom')

@pytest.fixture()
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['PROPAGATE_EXCEPTIONS'] = False

    with app.app_context():
        db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.drop_all()
    limiter.reset()
    os.close(db_fd)
    os.unlink(db_path)

def register_and_login(client):
    client.post('/api/register', json={
        'username': 'tester',
        'email': 'test@example.com',
        'password': 'password123'
    })
    resp = client.post('/api/login', json={
        'identifier': 'tester',
        'password': 'password123'
    })
    token = resp.get_json()['token']
    return token

def test_register_and_login(client):
    resp = client.post('/api/register', json={
        'username': 'foo',
        'email': 'foo@example.com',
        'password': 'secret123'
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['user']['username'] == 'foo'

    login = client.post('/api/login', json={'identifier': 'foo', 'password': 'secret123'})
    assert login.status_code == 200
    assert 'token' in login.get_json()

def test_bookshelf_crud(client):
    token = register_and_login(client)
    headers = {'Authorization': f'Bearer {token}'}

    # create shelf
    resp = client.post('/api/bookshelves', headers=headers, json={'name': 'My Shelf'})
    assert resp.status_code == 201
    shelf_id = resp.get_json()['id']

    # update shelf
    resp = client.put(f'/api/bookshelves/{shelf_id}', headers=headers, json={'description': 'desc'})
    assert resp.status_code == 200
    assert resp.get_json()['description'] == 'desc'

    # list shelves
    resp = client.get('/api/bookshelves', headers=headers)
    assert resp.status_code == 200
    assert len(resp.get_json()) >= 1

    # delete shelf
    resp = client.delete(f'/api/bookshelves/{shelf_id}', headers=headers)
    assert resp.status_code == 200


def test_unknown_route_returns_json(client):
    resp = client.get('/nonexistent')
    assert resp.status_code == 404
    assert resp.get_json()['error'] == 'Not found'


def test_internal_error_returns_json(client):
    resp = client.get('/error-test')
    assert resp.status_code == 500
    assert resp.get_json()['error'] == 'Internal server error'


def test_method_not_allowed_returns_json(client):
    resp = client.delete('/api/bookshelves')
    assert resp.status_code == 405
    assert resp.get_json()['error'] == 'Method not allowed'


def test_health_endpoint(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'ok'


def test_api_spec_endpoint(client):
    resp = client.get('/api/spec')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['openapi'].startswith('3.')
    assert '/api/register' in data['paths']


def test_login_respects_token_expiry_env(client, monkeypatch):
    client.post('/api/register', json={
        'username': 'expuser',
        'email': 'exp@example.com',
        'password': 'pass1234'
    })
    monkeypatch.setenv('TOKEN_EXPIRY_HOURS', '2')
    resp = client.post('/api/login', json={'identifier': 'expuser', 'password': 'pass1234'})
    assert resp.status_code == 200
    token = resp.get_json()['token']
    decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    exp = datetime.fromtimestamp(decoded['exp'], tz=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    assert 1.9 < delta.total_seconds() / 3600 <= 2.1


def test_login_rate_limit(client):
    client.post('/api/register', json={
        'username': 'limituser',
        'email': 'limit@example.com',
        'password': 'pass1234'
    })
    # Perform 5 successful logins
    for _ in range(5):
        resp = client.post('/api/login', json={'identifier': 'limituser', 'password': 'pass1234'})
        assert resp.status_code == 200
    # Sixth attempt should be blocked by rate limiting
    resp = client.post('/api/login', json={'identifier': 'limituser', 'password': 'pass1234'})
    assert resp.status_code == 429
    assert resp.get_json()['error'] == 'Too many requests'


def test_friend_request_and_accept(client):
    # create two users
    client.post('/api/register', json={
        'username': 'alice',
        'email': 'alice@example.com',
        'password': 'password'
    })
    client.post('/api/register', json={
        'username': 'bob',
        'email': 'bob@example.com',
        'password': 'password'
    })
    token_a = client.post('/api/login', json={'identifier': 'alice', 'password': 'password'}).get_json()['token']
    token_b = client.post('/api/login', json={'identifier': 'bob', 'password': 'password'}).get_json()['token']
    headers_a = {'Authorization': f'Bearer {token_a}'}
    headers_b = {'Authorization': f'Bearer {token_b}'}

    resp = client.post('/api/friends/2', headers=headers_a)
    assert resp.status_code == 201

    resp = client.get('/api/friends/requests', headers=headers_b)
    reqs = resp.get_json()
    assert len(reqs) == 1

    resp = client.post('/api/friends/1', headers=headers_b)
    assert resp.status_code == 200

    resp = client.get('/api/friends', headers=headers_a)
    friends = resp.get_json()
    assert len(friends) == 1


def test_friend_request_cancel_decline_and_remove(client):
    # create two users
    client.post('/api/register', json={'username': 'carl', 'email': 'carl@example.com', 'password': 'pass123'})
    client.post('/api/register', json={'username': 'dana', 'email': 'dana@example.com', 'password': 'pass123'})

    token_c = client.post('/api/login', json={'identifier': 'carl', 'password': 'pass123'}).get_json()['token']
    token_d = client.post('/api/login', json={'identifier': 'dana', 'password': 'pass123'}).get_json()['token']
    headers_c = {'Authorization': f'Bearer {token_c}'}
    headers_d = {'Authorization': f'Bearer {token_d}'}

    # send request from carl to dana
    resp = client.post('/api/friends/2', headers=headers_c)
    assert resp.status_code == 201

    # carl can list outgoing request
    resp = client.get('/api/friends/outgoing', headers=headers_c)
    assert len(resp.get_json()) == 1

    # carl cancels it
    resp = client.delete('/api/friends/2', headers=headers_c)
    assert resp.status_code == 200

    # send another request
    client.post('/api/friends/2', headers=headers_c)
    # dana declines
    resp = client.delete('/api/friends/1', headers=headers_d)
    assert resp.status_code == 200

    # send and accept to test removal
    client.post('/api/friends/2', headers=headers_c)
    client.post('/api/friends/1', headers=headers_d)
    resp = client.delete('/api/friends/2', headers=headers_c)
    assert resp.status_code == 200


def test_public_bookshelves_access(client):
    token = register_and_login(client)
    headers = {'Authorization': f'Bearer {token}'}

    resp = client.post('/api/bookshelves', headers=headers, json={'name': 'Public Shelf', 'is_public': True})
    shelf_id = resp.get_json()['id']

    # public listing should include the shelf without auth
    resp = client.get('/api/public/bookshelves')
    data = resp.get_json()
    assert any(s['id'] == shelf_id for s in data)

    # detail endpoint
    resp = client.get(f'/api/public/bookshelves/{shelf_id}')
    assert resp.status_code == 200
    assert resp.get_json()['id'] == shelf_id


def test_view_friend_bookshelves(client):
    # create two users
    client.post('/api/register', json={'username': 'erin', 'email': 'erin@example.com', 'password': 'password1'})
    client.post('/api/register', json={'username': 'frank', 'email': 'frank@example.com', 'password': 'password1'})

    token_e = client.post('/api/login', json={'identifier': 'erin', 'password': 'password1'}).get_json()['token']
    token_f = client.post('/api/login', json={'identifier': 'frank', 'password': 'password1'}).get_json()['token']
    headers_e = {'Authorization': f'Bearer {token_e}'}
    headers_f = {'Authorization': f'Bearer {token_f}'}

    # Erin creates one public and one private shelf
    client.post('/api/bookshelves', headers=headers_e, json={'name': 'Public', 'is_public': True})
    client.post('/api/bookshelves', headers=headers_e, json={'name': 'Private', 'is_public': False})

    # Frank is not yet a friend, should only see public shelf
    resp = client.get('/api/users/1/bookshelves', headers=headers_f)
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Public'

    # Become friends
    client.post('/api/friends/2', headers=headers_e)
    client.post('/api/friends/1', headers=headers_f)

    resp = client.get('/api/users/1/bookshelves', headers=headers_f)
    data = resp.get_json()
    names = {s['name'] for s in data}
    assert {'Public', 'Private'} <= names


def test_community_create_and_join(client):
    token_a = register_and_login(client)
    headers_a = {'Authorization': f'Bearer {token_a}'}

    resp = client.post('/api/communities', headers=headers_a, json={'name': 'Sci-Fi Fans'})
    assert resp.status_code == 201
    comm_id = resp.get_json()['id']

    resp = client.get('/api/communities')
    assert any(c['id'] == comm_id for c in resp.get_json())

    client.post('/api/register', json={'username': 'joiner', 'email': 'join@example.com', 'password': 'pass123'})
    token_b = client.post('/api/login', json={'identifier': 'joiner', 'password': 'pass123'}).get_json()['token']
    headers_b = {'Authorization': f'Bearer {token_b}'}

    resp = client.post(f'/api/communities/{comm_id}/join', headers=headers_b)
    assert resp.status_code == 200

    resp = client.get(f'/api/communities/{comm_id}/members')
    assert len(resp.get_json()) == 2

    resp = client.delete(f'/api/communities/{comm_id}/leave', headers=headers_b)
    assert resp.status_code == 200

    resp = client.get(f'/api/communities/{comm_id}/members')
    assert len(resp.get_json()) == 1


def test_my_communities_and_delete(client):
    token_a = register_and_login(client)
    headers_a = {'Authorization': f'Bearer {token_a}'}

    resp = client.post('/api/communities', headers=headers_a, json={'name': 'Readers'})
    comm_id = resp.get_json()['id']

    resp = client.get('/api/communities/mine', headers=headers_a)
    assert any(c['id'] == comm_id for c in resp.get_json())

    client.post('/api/register', json={'username': 'helper', 'email': 'h@e.com', 'password': 'pass123'})
    resp = client.post('/api/login', json={'identifier': 'helper', 'password': 'pass123'})
    assert resp.status_code == 200
    token_b = resp.get_json()['token']
    headers_b = {'Authorization': f'Bearer {token_b}'}
    client.post(f'/api/communities/{comm_id}/join', headers=headers_b)

    resp = client.get('/api/communities/mine', headers=headers_b)
    assert any(c['id'] == comm_id for c in resp.get_json())

    resp = client.delete(f'/api/communities/{comm_id}', headers=headers_b)
    assert resp.status_code == 403

    resp = client.delete(f'/api/communities/{comm_id}', headers=headers_a)
    assert resp.status_code == 200
    resp = client.get('/api/communities')
    assert not any(c['id'] == comm_id for c in resp.get_json())


def test_get_and_update_community(client):
    token = register_and_login(client)
    headers = {'Authorization': f'Bearer {token}'}

    resp = client.post('/api/communities', headers=headers, json={'name': 'EditMe', 'description': 'desc'})
    comm_id = resp.get_json()['id']

    resp = client.get(f'/api/communities/{comm_id}', headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()['name'] == 'EditMe'

    resp = client.put(f'/api/communities/{comm_id}', headers=headers, json={'name': 'NewName'})
    assert resp.status_code == 200
    assert resp.get_json()['name'] == 'NewName'


def test_update_community_non_owner_forbidden(client):
    token_a = register_and_login(client)
    headers_a = {'Authorization': f'Bearer {token_a}'}

    resp = client.post('/api/communities', headers=headers_a, json={'name': 'Owned'})
    comm_id = resp.get_json()['id']

    client.post('/api/register', json={'username': 'other', 'email': 'o@e.com', 'password': 'pass123'})
    token_b = client.post('/api/login', json={'identifier': 'other', 'password': 'pass123'}).get_json()['token']
    headers_b = {'Authorization': f'Bearer {token_b}'}

    resp = client.put(f'/api/communities/{comm_id}', headers=headers_b, json={'name': 'Hack'})
    assert resp.status_code == 403


def test_search_communities(client):
    token = register_and_login(client)
    headers = {'Authorization': f'Bearer {token}'}

    client.post('/api/communities', headers=headers, json={'name': 'Sci-Fi Fans'})
    client.post('/api/communities', headers=headers, json={'name': 'Fantasy Club'})

    resp = client.get('/api/communities/search?q=fant')
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'Fantasy Club'


def test_token_refresh_and_logout(client):
    token = register_and_login(client)
    headers = {'Authorization': f'Bearer {token}'}

    # refresh token
    resp = client.post('/api/token/refresh', headers=headers)
    assert resp.status_code == 200
    new_token = resp.get_json()['token']
    assert new_token != token

    # logout using new token
    headers_new = {'Authorization': f'Bearer {new_token}'}
    resp = client.post('/api/logout', headers=headers_new)
    assert resp.status_code == 200

    # ensure revoked token cannot be used
    resp = client.get('/api/bookshelves', headers=headers_new)
    assert resp.status_code == 401

