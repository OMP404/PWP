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


def test_bar_model(db_handle):
    '''
    Test method for the Bar SQLAlchemy model.

    Args:
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    assert Bar.query.count() == 1
    assert Bar.query.first().name == 'Test-bar'
    assert Bar.query.first().address == 'Test-address'


def test_tapdrink_model(db_handle):
    '''
    Test method for the Tapdrink SQLAlchemy model.

    Args:
        db_handle: SQLAlchemy database handle.

    Returns:
        None.

    '''
    bar = _create_bar()
    db_handle.session.add(bar)
    db_handle.session.commit()
    tapdrink = _create_tapdrink()
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    assert Tapdrink.query.count() == 1
    assert Tapdrink.query.first().drink_type == 'Test-type'
    assert Tapdrink.query.first().drink_name == 'Test-tapdrink'
    assert Tapdrink.query.first().drink_size == 0.5
    assert Tapdrink.query.first().price == 1.0


def test_cocktail_model(db_handle):
    '''
    Test method for the Cocktail SQLAlchemy model.

    Args:
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
    assert Cocktail.query.count() == 1
    assert Cocktail.query.first().cocktail_name == 'Test-cocktail'
    assert Cocktail.query.first().price == 1.0


def test_bar_and_tapdrink_model(db_handle):
    '''
    Test method for checking the connection between the Bar and Tapdrink models.

    Args:
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    tapdrink = _create_tapdrink()
    tapdrink.bar = bar
    db_handle.session.add(tapdrink)
    db_handle.session.commit()
    db_bar = Bar.query.first()
    db_tapdrink = Tapdrink.query.first()
    # assert correct number of bars and tapdrinks
    assert Tapdrink.query.count() == 1
    assert Bar.query.count() == 1
    # assert tapdrink has correct values
    assert db_tapdrink.bar_name == 'Test-bar'
    assert db_tapdrink.drink_type == 'Test-type'
    assert db_tapdrink.drink_name == 'Test-tapdrink'
    assert db_tapdrink.drink_size == 0.5
    assert db_tapdrink.price == 1.0
    # assert bar has correct values within tapdrink
    assert db_tapdrink.bar.name == 'Test-bar'
    assert db_tapdrink.bar.address == 'Test-address'
    assert db_tapdrink in db_bar.tapdrink
    # assert bar has correct values
    assert db_bar.name == 'Test-bar'
    assert db_bar.address == 'Test-address'
    # assert tapdrink has correct values within bar
    assert db_bar.tapdrink[0].bar_name == 'Test-bar'
    assert db_bar.tapdrink[0].drink_type == 'Test-type'
    assert db_bar.tapdrink[0].drink_name == 'Test-tapdrink'
    assert db_bar.tapdrink[0].drink_size == 0.5
    assert db_bar.tapdrink[0].price == 1.0
    assert db_bar == db_tapdrink.bar


def test_bar_and_cocktail_model(db_handle):
    '''
    Test method for checking the connection between the Bar and Cocktail models.

    Args:
        db_handle: SQLAlchemy database handle.

    Returns:
        None.
    '''
    bar = _create_bar()
    cocktail = _create_cocktail()
    cocktail.bar = bar
    db_handle.session.add(cocktail)
    db_handle.session.commit()
    db_bar = Bar.query.first()
    db_cocktail = Cocktail.query.first()
    # assert correct number of bars and cocktails
    assert Cocktail.query.count() == 1
    assert Bar.query.count() == 1
    # assert cocktail has correct values
    assert db_cocktail.cocktail_name == 'Test-cocktail'
    assert db_cocktail.price == 1.0
    # assert bar has correct values within cocktail
    assert db_cocktail.bar.name == 'Test-bar'
    assert db_cocktail.bar.address == 'Test-address'
    assert db_cocktail in db_bar.cocktail
    # assert bar has correct values
    assert db_bar.name == 'Test-bar'
    assert db_bar.address == 'Test-address'
    # assert cocktail has correct values within bar
    assert db_bar.cocktail[0].cocktail_name == 'Test-cocktail'
    assert db_bar.cocktail[0].price == 1.0
    assert db_bar == db_cocktail.bar


if __name__ == '__main__':
    pytest.main(['-v', '-s', __file__])
