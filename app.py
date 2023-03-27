import json
from flask import Flask, Response, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, Api
from jsonschema import validate, ValidationError
from sqlalchemy.engine import Engine
from sqlalchemy import event, UniqueConstraint
from sqlalchemy.exc import IntegrityError
from werkzeug.routing import BaseConverter
from flasgger import Swagger

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///Database/bar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SWAGGER"] = {
    "title": "Oulu Bars API",
    "openapi": "3.0.3",
    "uiversion": 3,
    "doc_dir": "./doc",
}

JSON = "application/json"
MASON = "application/vnd.mason+json"

ERROR_PROFILE = "/profiles/error/"
LINK_RELATIONS_URL = "/alcoholmeta/link-relations/"
BAR_PROFILE = "/profiles/bar/"
TAPDRINK_PROFILE = "/profiles/tapdrink/"
COCKTAIL_PROFILE = "/profiles/cocktail/"

api = Api(app)
db = SQLAlchemy(app)
swagger = Swagger(app, template_file="doc/base.yml")


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
        "Tapdrink",
        cascade="all, delete-orphan",
        back_populates="bar")
    cocktail = db.relationship(
        "Cocktail",
        cascade="all, delete-orphan",
        back_populates="bar")

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
    bar_name = db.Column(
        db.String(64),
        db.ForeignKey(
            "bar.name",
            ondelete="CASCADE"))
    drink_type = db.Column(db.String(64), unique=False, nullable=True)
    drink_name = db.Column(db.String(64), unique=False, nullable=False)
    drink_size = db.Column(db.Float, unique=False, nullable=False)
    price = db.Column(db.Float, unique=False, nullable=False)
    table_args_ = (
        UniqueConstraint(
            'bar_name',
            'drink_name',
            'drink_size',
            name='No duplicates in a bar'),
    )
    bar = db.relationship("Bar", back_populates="tapdrink")

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
    bar_name = db.Column(
        db.String(64),
        db.ForeignKey(
            "bar.name",
            ondelete="CASCADE"))
    cocktail_name = db.Column(db.String(64), unique=False, nullable=False)
    price = db.Column(db.Float, nullable=False)
    table_args_ = (
        UniqueConstraint(
            'bar_name',
            'cocktail_name',
            name='No duplicates in a bar'),
    )
    bar = db.relationship("Bar", back_populates="cocktail")

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


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href


class InventoryBuilder(MasonBuilder):

    def add_control_delete_bar(self, bar):
        self.add_control(
            "almeta:delete-bar",
            api.url_for(BarItem, bar=bar),
            method="DELETE",
            title="Delete this bar"
        )

    def add_control_add_bar(self):
        self.add_control(
            "almeta:add-bar",
            api.url_for(BarCollection),
            method="POST",
            encoding="json",
            schema=Bar.json_schema(),
            title="Add a bar"
        )

    def add_control_edit_bar(self, bar):
        self.add_control(
            "almeta:edit-bar",
            api.url_for(BarItem, bar=bar),
            method="PUT",
            encoding="json",
            schema=Bar.json_schema(),
            title="Edit this bar"

        )

    def add_control_in_bar(self, bar):
        self.add_control(
            "almeta:in-bar",
            api.url_for(BarItem, bar=bar),
            method="GET",
            encoding="json",
            title="Return to the bar where the drink is sold"
        )

    def add_control_delete_tapdrink(self, bar, drink_name, drink_size):
        self.add_control(
            "almeta:delete-tapdrink",
            api.url_for(
                TapdrinkItem,
                bar=bar,
                drink_name=drink_name,
                drink_size=drink_size),
                method="DELETE",
                title="Delete this tapdrink"
        )

    def add_control_add_tapdrink(self, bar):
        self.add_control(
            "almeta:add-tapdrink",
            api.url_for(TapdrinkCollection, bar=bar),
            method="POST",
            encoding="json",
            schema=Tapdrink.json_schema(),
            title="Add a tapdrink"
        )

    def add_control_edit_tapdrink(self, bar, drink_name, drink_size):
        self.add_control(
            "edit-tapdrink",
            api.url_for(
                TapdrinkItem,
                bar=bar,
                drink_name=drink_name,
                drink_size=drink_size),
            method="PUT",
            encoding="json",
            schema=Tapdrink.json_schema(),
            title="Edit this tapdrink")

    def add_control_delete_cocktail(self, bar, cocktail_name):
        self.add_control(
            "almeta:delete-cocktail",
            api.url_for(CocktailItem, bar=bar, cocktail_name=cocktail_name),
            method="DELETE",
            title="Delete this cocktail"
        )

    def add_control_add_cocktail(self, bar):
        self.add_control(
            "almeta:add-cocktail",
            api.url_for(CocktailCollection, bar=bar),
            method="POST",
            encoding="json",
            schema=Cocktail.json_schema(),
            title="Add a cocktail"
        )

    def add_control_edit_cocktail(self, bar, cocktail_name):
        self.add_control(
            "edit-cocktail",
            api.url_for(CocktailItem, bar=bar, cocktail_name=cocktail_name),
            method="PUT",
            encoding="json",
            schema=Cocktail.json_schema(),
            title="Edit this cocktail"
        )


def create_error_response(status_code, title, message=None):
    resource_url = request.path
    data = MasonBuilder(resource_url=resource_url)
    data.add_error(title, message)
    data.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(data), status_code, mimetype=MASON)


class BarCollection(Resource):

    def get(self):
        body = InventoryBuilder(items=[])
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control_add_bar()

        for bar in Bar.query.all():
            item = InventoryBuilder({
                "name": bar.name,
                "address": bar.address
            })
            item.add_control("self", href=api.url_for(BarItem, bar=bar))
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Tapdrink.json_schema())
        except ValidationError as e:
            raise create_error_response(400, "Invalid JSON document", str(e))

        bar = Bar()
        bar.deserialize(request.json)

        try:
            db.session.add(bar)
            db.session.commit()
        except:
            return create_error_response(500, "Database error")

        return Response(
            status=201, headers={
                'Location': api.url_for(
                    BarItem, bar=bar)})


class BarItem(Resource):

    def get(self, bar):
        body = InventoryBuilder(bar.serialize())
        body.add_control("self", href=api.url_for(BarItem, bar=bar))
        body.add_control_edit_bar(bar)
        body.add_control_delete_bar(bar)
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_namespace("profile", BAR_PROFILE)
        body.add_control("collection", href=api.url_for(BarCollection))
        body.add_control("almeta:tapdrinks-in",
                         href=api.url_for(TapdrinkCollection, bar=bar))
        body.add_control("almeta:cocktails-in",
                         href=api.url_for(CocktailCollection, bar=bar))

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, bar):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")
        try:
            validate(request.json, bar.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        bar.deserialize(request.json)

        try:
            db.session.add(bar)
            db.session.commit()
        except IntegrityError:
            return create_error_response(500, "Database error")

        return Response(status=204)

    def delete(self, bar):
        db.session.delete(bar)
        db.session.commit()
        return Response(status=204)


class TapdrinkCollection(Resource):

    def get(self, bar):
        body = InventoryBuilder(items=[])
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control_add_tapdrink(bar)
        body.add_control_in_bar(bar)

        for tapdrink in Tapdrink.query.filter_by(bar_name=bar.name).all():
            item = InventoryBuilder(
                {
                    "bar_name": tapdrink.bar_name,
                    "drink_type": tapdrink.drink_type,
                    "drink_name": tapdrink.drink_name,
                    "drink_size": tapdrink.drink_size,
                    "price": tapdrink.price
                }
            )
            item.add_control(
                "self",
                href=api.url_for(
                    TapdrinkItem,
                    bar=bar,
                    drink_name=tapdrink.drink_name,
                    drink_size=tapdrink.drink_size))
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Tapdrink.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        tapdrink = Tapdrink()
        tapdrink.deserialize(request.json)

        try:
            db.session.add(tapdrink)
            db.session.commit()
        except IntegrityError:
            return create_error_response(500, "Database error")
        header = {'Location': api.url_for(
            TapdrinkItem, bar=tapdrink.bar, drink_name=tapdrink.drink_name, drink_size=tapdrink.drink_size)}
        return Response(status=201, headers=header)


class TapdrinkItem(Resource):

    def get(self, bar, drink_name, drink_size):
        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name,
            drink_name=drink_name,
            drink_size=drink_size).first()
        if not tapdrink:
            return create_error_response(404, "Tapdrink not found")
        body = InventoryBuilder(tapdrink.serialize())
        body.add_control(
            "self",
            href=api.url_for(
                TapdrinkItem,
                bar=bar,
                drink_name=tapdrink.drink_name,
                drink_size=tapdrink.drink_size))
        body.add_control_edit_tapdrink(
            bar,
            tapdrink.drink_name,
            tapdrink.drink_size)
        body.add_control_delete_tapdrink(
            bar,
            tapdrink.drink_name,
            tapdrink.drink_size)
        body.add_control("collection", href=api.url_for(
            TapdrinkCollection, bar=bar))
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_namespace("profile", TAPDRINK_PROFILE)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, bar, drink_name, drink_size):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Tapdrink.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name,
            drink_name=drink_name,
            drink_size=drink_size).first()
        if not tapdrink:
            return create_error_response(404, "Tapdrink not found")
        tapdrink.deserialize(request.json)

        try:
            db.session.add(tapdrink)
            db.session.commit()
        except IntegrityError:
            return create_error_response(500, "Database error")

        return Response(status=204)

    def delete(self, bar, drink_name, drink_size):
        tapdrink = Tapdrink.query.filter_by(
            bar_name=bar.name,
            drink_name=drink_name,
            drink_size=drink_size).first()
        if not tapdrink:
            return create_error_response(404, "Tapdrink not found")
        db.session.delete(tapdrink)
        db.session.commit()
        return Response(status=204)


class CocktailCollection(Resource):
    def get(self, bar):
        body = InventoryBuilder(items=[])
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_control("self", href=request.path)
        body.add_control_add_cocktail(bar)
        body.add_control_in_bar(bar)

        for cocktail in Cocktail.query.filter_by(bar_name=bar.name).all():
            item = InventoryBuilder(
                {
                    "bar_name": cocktail.bar_name,
                    "cocktail_name": cocktail.cocktail_name,
                    "price": cocktail.price
                }
            )
            item.add_control(
                "self",
                href=api.url_for(
                    CocktailItem,
                    bar=bar,
                    cocktail_name=cocktail.cocktail_name))
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, Cocktail.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        cocktail = Cocktail()
        cocktail.deserialize(request.json)

        try:
            db.session.add(cocktail)
            db.session.commit()
        except IntegrityError:
            return create_error_response(500, "Database error")
        header = {
            'Location': api.url_for(
                CocktailItem,
                bar_name=cocktail.bar_name,
                cocktail_name=cocktail.cocktail_name)}

        return Response(status=201, headers=header)


class CocktailItem(Resource):
    def get(self, bar, cocktail_name):
        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name,
            cocktail_name=cocktail_name).first()
        if not cocktail:
            return create_error_response(404, "Cocktail not found")
        body = InventoryBuilder(cocktail.serialize())
        body.add_namespace("almeta", LINK_RELATIONS_URL)
        body.add_namespace("profile", COCKTAIL_PROFILE)
        body.add_control(
            "self",
            href=api.url_for(
                CocktailItem,
                bar=bar,
                cocktail_name=cocktail.cocktail_name))
        body.add_control_edit_cocktail(
            bar,
            cocktail.cocktail_name)
        body.add_control_delete_cocktail(
            bar,
            cocktail.cocktail_name)
        body.add_control("collection", href=api.url_for(
            CocktailCollection, bar=bar))
        
        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, bar, cocktail_name):
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(request.json, cocktail.json_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name, cocktail_name=cocktail_name).first()
        if not cocktail:
            return create_error_response(404, "Cocktail not found")
        cocktail.deserialize(request.json)

        try:
            db.session.add(cocktail)
            db.session.commit()
        except IntegrityError:
            return create_error_response(500, "Database error")

        return Response(status=204)

    def delete(self, bar, cocktail_name):
        cocktail = Cocktail.query.filter_by(
            bar_name=bar.name, cocktail_name=cocktail_name).first()
        db.session.delete(cocktail)
        db.session.commit()
        return Response(status=204)


@app.route("/profiles/<resource>/")
def send_profile_html(resource):
    return send_from_directory(app.static_folder, "{}.html".format(resource))


@app.route("/almeta/link-relations/")
def send_link_relations_html():
    return send_from_directory(app.static_folder, "links-relations.html")


class BarConverter(BaseConverter):
    def to_python(self, name):
        db_bar = Bar.query.filter_by(name=name).first()
        if db_bar is None:
            return create_error_response(404, "Bar not found")
        return db_bar

    def to_url(self, db_bar):
        return db_bar.name


app.url_map.converters["bar"] = BarConverter

api.add_resource(BarCollection, "/api/bars/")
api.add_resource(BarItem, "/api/bars/<bar:bar>/")
api.add_resource(TapdrinkCollection, "/api/bars/<bar:bar>/tapdrinks/")
api.add_resource(
    TapdrinkItem,
    "/api/bars/<bar:bar>/tapdrinks/<drink_name>/<drink_size>/")
api.add_resource(CocktailCollection, "/api/bars/<bar:bar>/cocktails/")
api.add_resource(CocktailItem, "/api/bars/<bar:bar>/cocktails/<cocktail_name>/")
