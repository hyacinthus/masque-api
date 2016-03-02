from datetime import datetime

from bson.objectid import ObjectId
from mongokit import IS, OR, Document, Connection
from mongokit.schema_document import CustomType

from config import MongoConfig, CollectionName

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
        "post_id": CustomObjectId(),
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


@connection.register
class Theme(Document):
    __collection__ = CollectionName.THEMES
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "district", "virtual", "private"),
        "short_name": str,
        "full_name": str,
        "locale": {
            "nation": str,
            "province": str,
            "city": str,
            "county": str
        }
    }


@connection.register
class Device(Document):
    __collection__ = CollectionName.DEVICES
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "name": str,
        "user_id": CustomObjectId(),
        "origin_user_id": CustomObjectId(),
    }


@connection.register
class UserLevel(Document):
    __collection__ = CollectionName.USER_LEVELS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "exp": str,
        "post_limit": int,
        "report_limit": int,
        "message_limit": int,
        "text_post": bool,
        "vote_post": bool,
        "photo_post": bool,
        "colors": list,
        "heart_limit": int
    }
    # default_values = {
    #     "text_post": False,
    #     "vote_post": False,
    #     "photo_post": False
    # }


@connection.register
class Mask(Document):
    __collection__ = CollectionName.MASKS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "name": str,
        "mask_url": str,
    }


@connection.register
class BoardPost(Document):
    __collection__ = CollectionName.BOARD_POSTS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": CustomObjectId(),
        "hearts": {
            "mask_id": CustomObjectId(),
            "user_id": CustomObjectId()
        },
        "content": str,
        "author": CustomObjectId()
    }


@connection.register
class BoardComment(BoardPost):
    __collection__ = CollectionName.BOARD_COMMENTS
    __database__ = MongoConfig.DB


@connection.register
class Parameter(Document):
    __collection__ = CollectionName.PARAMETERS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "default_masks": [CustomObjectId()]
    }


@connection.register
class DeviceTrace(Document):
    __collection__ = CollectionName.DEVICE_TRACE
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "serial": str,
        "carrier": str,
        "cellphone": int,
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point")
        }
    }


@connection.register
class Message(Document):
    __collection__ = CollectionName.MESSAGES
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "to": CustomObjectId(),
        "from": CustomObjectId(),
        "content": str,
        "_created": CustomDate(),
        "archived": bool
    }


@connection.register
class UserTrace(Document):
    __collection__ = CollectionName.USER_TRACE
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "user_id": CustomObjectId(),
        "_created": CustomDate(),
        "_updated": CustomDate(),
        "thanks": int,
        "footprint": [
            {
                "coordinates": [
                    OR(int, float),
                    OR(int, float)
                ],
                "type": IS("Point")
            }
        ]
    }
