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


def _create_bar():
    '''
    Creates a new bar object for testing purposes.

    Returns:
        New bar object.
    '''
    return Bar(name="Test-bar", address="Test-address")


def _create_tapdrink():
    '''
    Creates a new tapdrink object for testing purposes.

    Returns:
        New Tapdrink object.
    '''
    return Tapdrink(bar_name="Test-bar",
                    drink_type="Test-type",
                    drink_name="Test-tapdrink",
                    drink_size=0.5,
                    price=1.0)


def _create_cocktail():
    '''
    Creates a new cocktail object for testing purposes.

    Returns:
        New Cocktail object.
    '''
    return Cocktail(bar_name="Test-bar",
                    cocktail_name="Test-cocktail",
                    price=1.0)


def test_barcollection_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve a the "BarCollection" i.e. a list of bars.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.get('/api/bars/')
    assert response.status_code == 200
    assert response.json['items'][0]['name'] == 'Test-bar'
    assert response.json['items'][0]['address'] == 'Test-address'


def test_barcollection_post(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific bar.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    response = client_handle.post(
        '/api/bars/', json={'name': f'{bar.name}', 'address': f'{bar.address}'})
    assert response.status_code == 201
    get_response = client_handle.get('/api/bars/')
    assert get_response.status_code == 200
    assert get_response.json['items'][0]['name'] == 'Test-bar'
    assert get_response.json['items'][0]['address'] == 'Test-address'


def test_baritem_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve a specific bar.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.get('/api/bars/Test-bar/')
    assert response.status_code == 200
    assert response.json['name'] == 'Test-bar'
    assert response.json['address'] == 'Test-address'


def test_baritem_put(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific bar.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.put(
        '/api/bars/Test-bar/', json={'name': 'Test-bar-new', 'address': 'Test-address-new'})
    assert response.status_code == 204
    new_response = client_handle.get('/api/bars/Test-bar-new/')
    old_response = client_handle.get('/api/bars/Test-bar/')
    # assert new bar exists and old bar does not
    assert new_response.status_code == 200
    assert old_response.status_code == 404
    assert new_response.json['name'] == 'Test-bar-new'
    assert new_response.json['address'] == 'Test-address-new'


def test_baritem_delete(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific bar.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.delete('/api/bars/Test-bar/')
    assert response.status_code == 204
    new_response = client_handle.get('/api/bars/Test-bar/')
    # assert the bar does not exist
    assert new_response.status_code == 404


def test_tapdrinkcollection_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve a the "TapdrinkCollection" i.e. a list of tapdrinks.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    # tapdrink.bar = bar
    tapdrink.bar_name = bar.name
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.get('/api/bars/Test-bar/tapdrinks/')
    assert response.status_code == 200
    assert response.json['items'][0]['bar_name'] == 'Test-bar'
    assert response.json['items'][0]['drink_type'] == 'Test-type'
    assert response.json['items'][0]['drink_name'] == 'Test-tapdrink'
    assert response.json['items'][0]['drink_size'] == 0.5
    assert response.json['items'][0]['price'] == 1.0


def test_tapdrinkcollection_post(db_handle, client_handle):
    '''
    Test method for the POST request to create a new tapdrink.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    # tapdrink.bar = bar
    response = client_handle.post(f'/api/bars/{bar.name}/tapdrinks/',
                                  json={'bar_name': bar.name,
                                        'drink_type': tapdrink.drink_type,
                                        'drink_name': tapdrink.drink_name,
                                        'drink_size': tapdrink.drink_size,
                                        'price': tapdrink.price})
    assert response.status_code == 201
    get_response = client_handle.get('/api/bars/Test-bar/tapdrinks/')
    assert get_response.status_code == 200
    assert get_response.json['items'][0]['bar_name'] == 'Test-bar'
    assert get_response.json['items'][0]['drink_type'] == 'Test-type'
    assert get_response.json['items'][0]['drink_name'] == 'Test-tapdrink'
    assert get_response.json['items'][0]['drink_size'] == 0.5
    assert get_response.json['items'][0]['price'] == 1.0


def test_tapdrinkitem_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve a specific tapdrink.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    tapdrink.bar = bar
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.get(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink/0.5/')
    assert response.status_code == 200
    assert response.json['bar_name'] == 'Test-bar'
    assert response.json['drink_type'] == 'Test-type'
    assert response.json['drink_name'] == 'Test-tapdrink'
    assert response.json['drink_size'] == 0.5
    assert response.json['price'] == 1.0


def test_tapdrinkitem_put(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific tapdrink.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    tapdrink.bar = bar
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.put(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink/0.5/',
        json={'bar_name': "Test-bar", 'drink_type': 'Test-type-new', 'drink_name': 'Test-tapdrink-new', 'drink_size': 0.33, 'price': 2.5})
    assert response.status_code == 204
    new_response = client_handle.get(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink-new/0.33/')
    old_response = client_handle.get(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink/0.5/')
    # assert new tapdrink exists and old tapdrink does not
    assert new_response.status_code == 200
    assert old_response.status_code == 404
    assert new_response.json['bar_name'] == 'Test-bar'
    assert new_response.json['drink_type'] == 'Test-type-new'
    assert new_response.json['drink_name'] == 'Test-tapdrink-new'
    assert new_response.json['drink_size'] == 0.33
    assert new_response.json['price'] == 2.5


def test_tapdrinkitem_delete(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific tapdrink.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    tapdrink.bar = bar
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.delete(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink/0.5/')
    assert response.status_code == 204
    new_response = client_handle.get(
        '/api/bars/Test-bar/tapdrinks/Test-tapdrink/0.5/')
    # assert the tapdrink does not exist
    assert new_response.status_code == 404


def test_cocktailcollection_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve all coctails.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    cocktail.bar = bar
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.get(
        '/api/bars/Test-bar/cocktails/')
    assert response.status_code == 200
    assert response.json['items'][0]['bar_name'] == 'Test-bar'
    assert response.json['items'][0]['cocktail_name'] == 'Test-cocktail'
    assert response.json['items'][0]['price'] == 1.0


def test_cocktailcollection_post(db_handle, client_handle):
    '''
    Test method for the POST request to create a new coctail.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    response = client_handle.post(
        '/api/bars/Test-bar/cocktails/',
        json={'bar_name': bar.name, 'cocktail_name': cocktail.cocktail_name, 'price': cocktail.price})
    assert response.status_code == 201
    new_response = client_handle.get(
        '/api/bars/Test-bar/cocktails/Test-cocktail/')
    # assert the new coctail exists
    assert new_response.status_code == 200
    assert new_response.json['bar_name'] == 'Test-bar'
    assert new_response.json['cocktail_name'] == 'Test-cocktail'
    assert new_response.json['price'] == 1.0


def test_cocktailitem_get(db_handle, client_handle):
    '''
    Test method for the GET request to retrieve a specific coctail.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    cocktail.bar = bar
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.get(
        '/api/bars/Test-bar/cocktails/Test-cocktail/')
    assert response.status_code == 200
    assert response.json['bar_name'] == 'Test-bar'
    assert response.json['cocktail_name'] == 'Test-cocktail'
    assert response.json['price'] == 1.0


def test_cocktailitem_put(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific cocktail.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    cocktail.bar = bar
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.put('/api/bars/Test-bar/cocktails/Test-cocktail/', json={
                                 'bar_name': "Test-bar", 'cocktail_name': 'Test-cocktail-new', 'price': 2.5})
    assert response.status_code == 204
    new_response = client_handle.get(
        '/api/bars/Test-bar/cocktails/Test-cocktail-new/')
    old_response = client_handle.get(
        '/api/bars/Test-bar/cocktails/Test-cocktail/')
    assert new_response.status_code == 200
    assert old_response.status_code == 404
    assert new_response.json['bar_name'] == 'Test-bar'
    assert new_response.json['cocktail_name'] == 'Test-cocktail-new'
    assert new_response.json['price'] == 2.5


def test_cocktailitem_delete(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific cocktail.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    cocktail.bar = bar
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.delete(
        '/api/bars/Test-bar/cocktails/Test-cocktail/')
    assert response.status_code == 204
    new_response = client_handle.get(
        '/api/bars/Test-bar/cocktails/Test-cocktail/')
    assert new_response.status_code == 404


if __name__ == '__main__':
    pytest.main(['-v', '-s', __file__])
