import os
import sys
import tempfile

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine

# add parent directory to path to import app (when running tests from root directory)
current = os.path.dirname(os.path.realpath(__file__))  # nopep8
sys.path.append(os.path.dirname(current))  # nopep8

from app import Bar, Cocktail, Tapdrink, app, db  # nopep8


@pytest.fixture
def db_handle():
    '''
    Fixture that sets up a temporary SQLite database for testing purposes using the Flask app and SQLAlchemy.

    Yields:
        SQLAlchemy database handle.
    '''
    db_df, db_path = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['TESTING'] = True

    with app.app_context():
        db.create_all()

    yield db

    db.session.remove()
    os.close(db_df)
    os.unlink(db_path)


@pytest.fixture
def client_handle():
    '''
    Fixture that creates a test client for the Flask app.

    Yields:
        Flask test client.
    '''
    client = app.test_client()
    yield client


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    '''
    SQLite pragma listener that enables foreign key support.

    Args:
        dbapi_connection: Database connection.
        connection_record: Connection record.

    Returns:
        None.
    '''
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def test_html_profiles(client_handle, db_handle):
    '''
    Test that the html profile pages are accessible.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    response = client_handle.get('/profiles/bar/')
    assert response.status_code == 200
    response = client_handle.get('/profiles/tapdrink/')
    assert response.status_code == 200
    response = client_handle.get('/profiles/cocktail/')
    assert response.status_code == 200
    response = client_handle.get('/profiles/error/')
    assert response.status_code == 200


def test_link_relations(client_handle, db_handle):
    '''
    Test that the link relations are accessible.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    response = client_handle.get("/almeta/link-relations/")
    assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__])
