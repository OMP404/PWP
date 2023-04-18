import os
import sys
import tempfile

import pytest
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError


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


def test_nonexisting_tapdrink_in_bar(client_handle, db_handle):
    '''
    Tests whether a non-existing tapdrink in a bar returns a 404 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()

    response = client_handle.get(
        '/bar/Test-bar/tapdrinks/Non-existing-tapdrink')
    assert response.status_code == 404


def test_nonexisting_coctail_in_bar(client_handle, db_handle):
    '''
    Tests whether a non-existing cocktail in a bar returns a 404 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()

    response = client_handle.get(
        '/bar/Test-bar/cocktails/Non-existing-cocktail')
    assert response.status_code == 404


def test_barcollection_post_unsupported_mediatype(client_handle, db_handle):
    '''
    Tests whether an unsupported media type (a list) returns a 415 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    response = client_handle.post(
        '/api/bars/', json="'name': 'Test-bar', 'address': 'Test-address'", content_type='text/plain')
    assert response.status_code == 415


def test_barcollection_post_invalid_json_schema(client_handle, db_handle):
    '''
    Tests whether an invalid JSON returns a 400 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    response = client_handle.post(
        '/api/bars/', json={"test_name": "Test-bar", "test-address": "test_address", "test_extra_object": "test-object"})
    assert response.status_code == 400


def test_barcollection_post_db_error(client_handle):
    '''
    Tests whether a database error returns a 500 error when it's not created.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    response = client_handle.post(
        '/api/bars/', json={'name': f'{bar.name}', 'address': f'{bar.address}'})
    assert response.status_code == 500


def test_baritem_put_unsupported_mediatype(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific bar with an unsupported media type.

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
        '/api/bars/Test-bar/', json="'name': 'Test-bar-new', 'address': 'Test-address-new'", content_type='text/plain')
    assert response.status_code == 415


def test_baritem_put_invalid_json_schema(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific bar with an invalid JSON schema.

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
        '/api/bars/Test-bar/', json={'test_name': 'Test-bar-new', 'test_address': 'Test-address-new'})
    assert response.status_code == 400


def test_baritem_put_nonexisting_bar(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific bar that doesn't exist.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    response = client_handle.put(
        '/api/bars/Test-bar/', json={'name': 'Test-bar-new', 'address': 'Test-address-new'})
    assert response.status_code == 404


def test_baritem_delete_nonexisting_bar(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific bar that doesn't exist.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    response = client_handle.delete('/api/bars/Test-bar/')
    assert response.status_code == 404


def test_tapdrinkcollection_post_unsupported_mediatype(client_handle, db_handle):
    '''
    Tests whether an unsupported media type (a list) returns a 415 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    response = client_handle.post(f'/api/bars/{bar.name}/tapdrinks/',
                                  json="'bar_name': f'{bar.name}', \
                                        'drink_type': f'{tapdrink.drink_type}', \
                                        'drink_name': f'{tapdrink.drink_name}', \
                                        'drink_size': tapdrink.drink_size, \
                                        'price': tapdrink.price", content_type='text/plain')
    assert response.status_code == 415


def test_tapdrinkcollection_post_invalid_json_schema(client_handle, db_handle):
    '''
    Tests whether an invalid JSON returns a 400 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    response = client_handle.post(f'/api/bars/{bar.name}/tapdrinks/',
                                  json={"test_bar_name": f'{bar.name}', "test_drink_type": f'{tapdrink.drink_type}', "test_drink_name": f'{tapdrink.drink_name}', "test_drink_size": tapdrink.drink_size, "test_price": tapdrink.price})
    assert response.status_code == 400


def test_tapdrinkitem_put_unsupported_mediatype(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific tapdrink with an unsupported media type.

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
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.put(
        f'/api/bars/{bar.name}/tapdrinks/{tapdrink.drink_name}/{tapdrink.drink_size}/', json="'drink_name': 'Test-drink-new', 'drink_size': 0.5, 'price': 5.0", content_type='text/plain')
    assert response.status_code == 415


def test_tapdrinkitem_put_invalid_json_schema(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific tapdrink with an invalid JSON schema.

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
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    response = client_handle.put(
        f'/api/bars/{bar.name}/tapdrinks/{tapdrink.drink_name}/{tapdrink.drink_size}/', json={'test_drink_name': 'Test-drink-new', 'test_drink_size': 0.5, 'test_price': 5.0})
    assert response.status_code == 400


def test_tapdrinkitem_put_nonexisting_tapdrink(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific tapdrink that doesn't exist.

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
        f'/api/bars/{bar.name}/tapdrinks/Test-drink/0.5/',
        json={'bar_name': "Test-bar", 'drink_type': 'Test-type-new',
              'drink_name': 'Test-tapdrink-new', 'drink_size': 0.33, 'price': 2.5})
    assert response.status_code == 404


def test_tapdrinkitem_delete_nonexisting_tapdrink(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific tapdrink that doesn't exist.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.delete(
        f'/api/bars/{bar.name}/tapdrinks/Test-drink/0.5/')
    assert response.status_code == 404


def test_cocktailcollection_post_unsupported_mediatype(client_handle, db_handle):
    '''
    Tests whether an unsupported media type (a list) returns a 415 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    response = client_handle.post(f'/api/bars/{bar.name}/cocktails/',
                                  json=f"'bar_name': '{bar.name}', \
                                        'cocktail_name': '{cocktail.cocktail_name}', \
                                        'price': {cocktail.price}", content_type='text/plain')
    assert response.status_code == 415


def test_cocktailcollection_post_invalid_json_schema(client_handle, db_handle):
    '''
    Tests whether an invalid JSON returns a 400 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    response = client_handle.post(f'/api/bars/{bar.name}/cocktails/',
                                  json={"test_bar_name": bar.name,
                                        "test_cocktail_name": cocktail.cocktail_name,
                                        "test_price": cocktail.price})
    assert response.status_code == 400


def test_cocktailitem_put_unsupported_mediatype(db_handle, client_handle):
    '''
    Tests whether an unsupported media type (a list) returns a 415 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.put(f'/api/bars/{bar.name}/cocktails/{cocktail.cocktail_name}/',
                                 json=f"'bar_name': '{bar.name}', \
                                        'cocktail_name': '{cocktail.cocktail_name}', \
                                        'price': {cocktail.price}", content_type='text/plain')
    assert response.status_code == 415


def test_cocktailitem_put_invalid_json_schema(db_handle, client_handle):
    '''
    Tests whether an invalid JSON returns a 400 error.

    Args:
        client_handle: Flask test client.
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    cocktail = _create_cocktail()
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    response = client_handle.put(f'/api/bars/{bar.name}/cocktails/{cocktail.cocktail_name}/',
                                 json={"test_bar_name": bar.name,
                                       "test_cocktail_name": cocktail.cocktail_name,
                                       "test_price": cocktail.price})
    assert response.status_code == 400


def test_cocktailitem_put_nonexisting_cocktail(db_handle, client_handle):
    '''
    Test method for the PUT request to update a specific cocktail that doesn't exist.

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
        f'/api/bars/{bar.name}/cocktails/Test-cocktail/',
        json={'bar_name': "Test-bar", 'cocktail_name': 'Test-cocktail-new', 'price': 2.5})
    assert response.status_code == 404


def test_cocktailitem_delete_nonexisting_cocktail(db_handle, client_handle):
    '''
    Test method for the DELETE request to delete a specific cocktail that doesn't exist.

    Args:
        db_handle: SQLAlchemy database handle.
        client_handle: Flask test client.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    response = client_handle.delete(
        f'/api/bars/{bar.name}/cocktails/Test-cocktail/')
    assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__])
