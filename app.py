import json

import click
from flask import Flask, Response, request
from flask.cli import with_appcontext
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from jsonschema import ValidationError, validate
from sqlalchemy import UniqueConstraint, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.exceptions import (BadRequest, Conflict, NotFound,
                                 UnsupportedMediaType)
from werkzeug.routing import BaseConverter

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Database/bar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

JSON = "application/json"
api = Api(app)
db = SQLAlchemy(app)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Bar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    address = db.Column(db.String(64), nullable=True)

    tapdrink = db.relationship(
        "Tapdrink", cascade="all, delete-orphan", back_populates="bar")
    cocktail = db.relationship(
        "Cocktail", cascade="all, delete-orphan", back_populates="bar")

    def serialize(self):
        return {
            "name": self.name,
            "address": self.address
        }

    def deserialize(self, doc):
        self.name = doc["name"]
        self.address = doc["address"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["name", "address"]
        }
        props = schema["properties"] = {}
        props["name"] = {
            "description": "The name of the bar",
            "type": "string",
        }
        props["address"] = {
            "description": "The address for the bar",
            "type": "string"
        }

        return schema


class Tapdrink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_name = db.Column(db.String(64), db.ForeignKey(
        "bar.name", ondelete="CASCADE"))
    drink_type = db.Column(db.String(64), unique=False, nullable=True)
    drink_name = db.Column(db.String(64), unique=False, nullable=False)
    drink_size = db.Column(db.Float, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    table_args_ = (UniqueConstraint('bar_name', 'drink_name',
                   'drink_size', name='No duplicates in a bar'))
    bar = db.relationship(
        "Bar", back_populates="tapdrink")

    def serialize(self):
        return {
            "bar_name": self.bar_name,
            "drink_type": self.drink_type,
            "drink_name": self.drink_name,
            "drink_size": self.drink_size,
            "price": self.price
        }

    def deserialize(self, doc):
        self.bar_name = doc["bar_name"]
        self.drink_type = doc.get("drink_type")
        self.drink_name = doc["drink_name"]
        self.drink_size = doc["drink_size"]
        self.price = doc["price"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["bar_name",  "drink_name", "drink_size", "price"]
        }
        props = schema["properties"] = {}
        props["bar_name"] = {
            "description": "The name of the bar",
            "type": "string",
        }
        props["drink_name"] = {
            "description": "The name of the drink (Karhu, Koff etc.)",
            "type": "string"
        }
        props["drink_size"] = {
            "description": "The size of the drink in liters",
            "type": "number",
            "minimum": 0
        }
        props["price"] = {
            "description": "The price of the drink in euros",
            "type": "number",
            "minimum": 0
        }
        return schema


class Cocktail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bar_name = db.Column(db.String(64), db.ForeignKey(
        "bar.name", ondelete="CASCADE"))
    cocktail_name = db.Column(db.String(64), unique=False, nullable=False)
    price = db.Column(db.Float, nullable=False)
    table_args_ = (UniqueConstraint(
        'bar_name', 'cocktail_name', name='No duplicates in a bar'))
    bar = db.relationship(
        "Bar", back_populates="cocktail")

    def serialize(self):
        return {
            "bar_name": self.bar_name,
            "cocktail_name": self.cocktail_name,
            "price": self.price
        }

    def deserialize(self, doc):
        self.bar_name = doc["bar_name"]
        self.cocktail_name = doc["cocktail_name"]
        self.price = doc["price"]

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["bar_name", "cocktail_name", "price"]
        }
        props = schema["properties"] = {}
        props["bar_name"] = {
            "description": "The name of the bar",
            "type": "string",
        }
        props["name"] = {
            "description": "The name of the cocktail",
            "type": "string",
        }
        props["price"] = {
            "description": "The price of the cocktail",
            "type": "number",
            "minimum": 0
        }

        return schema


class BarCollection(Resource):

    def get(self):
        body = {
            "bars": []
        }
        bars = Bar.query.all()

        for bar in bars:
            body["bars"].append(
                {
                    "name": bar.name,
                    "address": bar.address
                }
            )

        return Response(json.dumps(body), 200, mimetype=JSON)

    def post(self):
        if not request.json:
            raise UnsupportedMediaType
        try:
            validate(request.json, Bar.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        bar = Bar()
        bar.deserialize(request.json)

        try:
            db.session.add(bar)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Bar with the same name already exists."
            )
        except Exception as e:
            print(e)

        return Response(status=201, headers={'Location': api.url_for(BarItem, bar=bar)})


class BarItem(Resource):

    def get(self, bar):
        body = bar.serialize()
        return Response(json.dumps(body), 200, mimetype=JSON)

    def put(self, bar):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, bar.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        bar.deserialize(request.json)

        try:
            db.session.add(bar)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Bar with the same name already exists."
            )

        return Response(status=204)

    def delete(self, bar):
        db.session.delete(bar)
        db.session.commit()
        return Response(status=204)


class TapdrinkCollection(Resource):

    def get(self, bar):
        # db_bar = Bar.query.filter_by(name=bar).first()
        # if db_bar is None:
        #     raise NotFound

        body = {
            "bar": bar.name,
            "tapdrinks": []
        }
        tapdrinks = Tapdrink.query.filter_by(bar_name=bar.name).all()

        for tapdrink in tapdrinks:
            body["tapdrinks"].append(
                {
                    "bar_name": tapdrink.bar_name,
                    "drink_type": tapdrink.drink_type,
                    "drink_name": tapdrink.drink_name,
                    "drink_size": tapdrink.drink_size,
                    "price": tapdrink.price
                }
            )

        return Response(json.dumps(body), 200, mimetype=JSON)

    def post(self, bar=None):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Tapdrink.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        tapdrink = Tapdrink()
        tapdrink.deserialize(request.json)

        try:
            db.session.add(tapdrink)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Tapdrink with the same name and size already exists."
            )
        header = {'Location': api.url_for(
            TapdrinkItem, bar=tapdrink.bar, drinkname=tapdrink.drink_name, drinksize=tapdrink.drink_size)}
        return Response(status=201, headers=header)


class TapdrinkItem(Resource):

    def get(self, bar, drinkname, drinksize):
        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name, drink_name=drinkname, drink_size=drinksize).first()
        if tapdrink is None:
            raise NotFound
        body = tapdrink.serialize()
        return Response(json.dumps(body), 200, mimetype=JSON)

    def put(self, bar, drinkname, drinksize):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Tapdrink.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name, drink_name=drinkname, drink_size=drinksize).first()
        tapdrink.deserialize(request.json)

        try:
            db.session.add(tapdrink)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Tapdrink with the same name and size already exists."
            )

        return Response(status=204)

    def delete(self, bar, drinkname, drinksize):
        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name, drink_name=drinkname, drink_size=drinksize).first()
        if tapdrink is None:
            raise NotFound
        db.session.delete(tapdrink)
        db.session.commit()
        return Response(status=204)


class CocktailCollection(Resource):

    def get(self, bar):
        # db_bar = Bar.query.filter_by(name=bar.).first()
        # if db_bar is None:
        #     raise NotFound
        body = {
            "bar": bar.name,
            "cocktails": []
        }
        cocktails = Cocktail.query.filter_by(bar_name=bar.name).all()

        for cocktail in cocktails:
            body["cocktails"].append(
                {
                    "bar_name": cocktail.bar_name,
                    "cocktail_name": cocktail.cocktail_name,
                    "price": cocktail.price
                }
            )

        return Response(json.dumps(body), 200, mimetype=JSON)

    def post(self, bar=None):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Cocktail.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        cocktail = Cocktail()
        cocktail.deserialize(request.json)

        try:
            db.session.add(cocktail)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Tapdrink with the same name and size already exists."
            )
        header = {'Location': api.url_for(
            CocktailItem, bar=cocktail.bar, cocktailname=cocktail.cocktail_name)}
        return Response(status=201, headers=header)


class CocktailItem(Resource):

    def get(self, bar, cocktailname):
        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name, cocktail_name=cocktailname).first()
        if cocktail is None:
            raise NotFound
        body = cocktail.serialize()
        return Response(json.dumps(body), 200, mimetype=JSON)

    def put(self, bar, cocktailname):
        if not request.json:
            raise UnsupportedMediaType

        try:
            validate(request.json, Cocktail.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name, cocktail_name=cocktailname).first()
        cocktail.deserialize(request.json)

        try:
            db.session.add(cocktail)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="Cocktail with the same name already exists."
            )

        return Response(status=204)

    def delete(self, bar, cocktailname):
        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name, cocktail_name=cocktailname).first()
        if cocktail is None:
            raise NotFound
        db.session.delete(cocktail)
        db.session.commit()
        return Response(status=204)


class BarConverter(BaseConverter):
    def to_python(self, name):
        db_bar = Bar.query.filter_by(name=name).first()
        if db_bar is None:
            raise NotFound
        return db_bar

    def to_url(self, db_bar):
        return db_bar.name


@ click.command("init-db")
@ with_appcontext
def init_db_command():
    """
    Initializes the database. If already initialized, nothing happens.
    """
    db.create_all()


@ click.command("populate-db")
@ with_appcontext
def populate_db_command():
    """
    Populates the database with products
    """
    tap_drink_types = ["Beer", "Long Drink", "Cider"]
    tap_drink_names = ['Karhu', "Koff", "CrowMoor"]
    drink_prices = [4.5, 5.5, 6.5]
    cocktail_names = ["Coctail", "Shot", "Drink"]
    for i in range(1, 5):
        bar = Bar(
            name=f"Bar {i}",
            address=f"Address Ave #{i}",
        )
        db.session.add(bar)
    db.session.commit()
    for i in range(3):
        drink = Tapdrink(
            bar_name=f"Bar {i + 1}",
            drink_type=tap_drink_types[i],
            drink_name=tap_drink_names[i],
            drink_size=0.5,
            price=drink_prices[i % 3]
        )
        db.session.add(drink)
        coctail = Cocktail(
            bar_name=f"Bar {i + 1}",
            cocktail_name=cocktail_names[i],
            price=drink_prices[i]
        )
        db.session.add(coctail)
    db.session.commit()


@ click.command("test-document")
@ with_appcontext
def test_document_command():
    """
    Prints the bars available in the database
    """
    with app.app_context():
        bars = Bar.query.all()
        print("\nBars:")
        for bar in bars:
            print(bar.serialize())
        tapdrinks = Tapdrink.query.all()
        print("\nTapdrinks:")
        for tapdrink in tapdrinks:
            print(tapdrink.serialize())
        cocktails = Cocktail.query.all()
        print("\nCocktails:")
        for cocktail in cocktails:
            print(cocktail.serialize())


app.url_map.converters["bar"] = BarConverter

api.add_resource(BarCollection, "/api/bars/")
api.add_resource(BarItem, "/api/bars/<bar:bar>/")
api.add_resource(TapdrinkCollection, "/api/bars/<bar:bar>/tapdrinks/")
api.add_resource(
    TapdrinkItem, "/api/bars/<bar:bar>/tapdrinks/<drinkname>/<drinksize>/")
api.add_resource(CocktailCollection, "/api/bars/<bar:bar>/cocktails/")
api.add_resource(CocktailItem, "/api/bars/<bar:bar>/cocktails/<cocktailname>/")

# Add cli commands to the app
app.cli.add_command(init_db_command)
app.cli.add_command(populate_db_command)
app.cli.add_command(test_document_command)
