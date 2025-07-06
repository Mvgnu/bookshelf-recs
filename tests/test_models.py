import os
import sys
import tempfile
import pytest

os.environ.setdefault('SECRET_KEY', 'test-secret')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app import app, db, User, Bookshelf

@pytest.fixture()
def app_context():
    db_fd, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    os.close(db_fd)
    os.unlink(db_path)

def test_user_password_hashing(app_context):
    user = User(username='tester', email='test@example.com')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    assert user.check_password('password123')
    assert not user.check_password('wrong')

