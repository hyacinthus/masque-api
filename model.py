from datetime import datetime

from bson.objectid import ObjectId
from mongokit import IS, OR, Document, Connection
from mongokit.schema_document import CustomType

from config import MongoConfig

connection = Connection(host=MongoConfig.HOST, port=MongoConfig.PORT)


class CustomDate(CustomType):
    mongo_type = datetime  # optional, just for more validation
    python_type = float
    init_type = None  # optional, fill the first empty value

    def to_bson(self, value):
        """convert type to a mongodb type"""
        if value == "" or value is None:  # update time if not received.
            return datetime.utcnow()
        return datetime.fromtimestamp(value)

    def to_python(self, value):
        """convert type to a python type"""
        return datetime.timestamp(value)

    def validate(self, value, path):
        """OPTIONAL : useful to add a validation layer"""
        if value is not None:
            pass  # ... do something here


class CustomObjectId(CustomType):
    mongo_type = ObjectId  # optional, just for more validation
    python_type = str
    init_type = None  # optional, fill the first empty value

    def to_bson(self, value):
        """convert type to a mongodb type"""
        return ObjectId(value)

    def to_python(self, value):
        """convert type to a python type"""
        return str(value)

    def validate(self, value, path):
        """OPTIONAL : useful to add a validation layer"""
        if value is not None:
            pass  # ... do something here


class Root(Document):
    structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": CustomObjectId(),
        "hearts": {
            "mask_id": CustomObjectId(),
            "user_id": CustomObjectId()
        },
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point")
        },
        "author": CustomObjectId()
    }


@connection.register
class Post(Root):
    structure = {
        "content": {
            "type": IS("text", "vote", "photo"),
            "text": str,
            "photo": str,
            "options": list
        },
        "comment_count": int,
        "_updated": CustomDate()
    }
    # required_fields = [
    #     'mask_id', 'hearts.mask_id', 'hearts.user_id'
    # ]
    # default_values = {
    #     "location.type": "Point"
    # }


@connection.register
class Comment(Root):
    structure = {
        "content": str,
        "post_id": CustomObjectId()
    }


@connection.register
class User(Document):
    structure = {
        "_id": CustomObjectId(),
        "name": str,
        "_created": CustomDate(),
        "cellphone": str,
        "exp": int,
        "user_level_id": CustomObjectId(),
        "hearts_received": int,
        "hearts": int,
        "_updated": CustomDate(),
        "masks": list,
        "pinned": list,
        "themes": list
    }
