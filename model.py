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
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point")
        },
        "author": str
    }
    required_fields = [
        "author"
    ]
    default_values = {
        "location.coordinates": [0, 0],
        "location.type": "Point"
    }


@connection.register
class Posts(Root):
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
    default_values = {
        "content.type": "text",
        "comment_count": 0,
    }


@connection.register
class Comments(Root):
    structure = {
        "content": str,
        "post_id": str,
    }


@connection.register
class Users(Document):
    __collection__ = CollectionName.USERS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "cellphone": str,
        "exp": int,
        "user_level_id": str,
        "hearts_received": int,
        "hearts_owned": int,
        "_updated": CustomDate(),
        "masks": list,
        "home": str,
        "subscribed": list
    }
    default_values = {
        "exp": 0,
        "hearts_received": 0,
        "hearts_owned": 0,
    }


@connection.register
class Themes(Document):
    __collection__ = CollectionName.THEMES
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "district", "virtual", "private", "system"),
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
class Devices(Document):
    __collection__ = CollectionName.DEVICES
    __database__ = MongoConfig.DB
    structure = {
        "_id": str,
        "name": str,
        "user_id": str,
        "origin_user_id": str,
    }
    required_fields = [
        '_id',
    ]


@connection.register
class UserLevels(Document):
    __collection__ = CollectionName.USER_LEVELS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "exp": int,
        "post_limit": int,
        "report_limit": int,
        "message_limit": int,
        "text_post": bool,
        "vote_post": bool,
        "photo_post": bool,
        "colors": list,
        "heart_limit": int
    }
    default_values = {
        "text_post": False,
        "vote_post": False,
        "photo_post": False,
        "exp": 0,
        "post_limit": 0,
        "report_limit": 0,
        "message_limit": 0,
        "colors": [],
        "heart_limit": 0
    }


@connection.register
class Masks(Document):
    __collection__ = CollectionName.MASKS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "name": str,
        "mask_url": str,
    }


@connection.register
class BoardPosts(Document):
    __collection__ = CollectionName.BOARD_POSTS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }


@connection.register
class BoardComments(BoardPosts):
    __collection__ = CollectionName.BOARD_COMMENTS
    __database__ = MongoConfig.DB


@connection.register
class Parameters(Document):
    __collection__ = CollectionName.PARAMETERS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "default_masks": list
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
    default_values = {
        "cellphone": 18000000000,
        "location.coordinates": [0, 0],
        "location.type": "Point"
    }


@connection.register
class Messages(Document):
    __collection__ = CollectionName.MESSAGES
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "to": str,
        "from": str,
        "content": str,
        "_created": CustomDate(),
        "archived": bool
    }
    default_values = {
        "archived": False
    }


@connection.register
class UserTraces(Document):
    __collection__ = CollectionName.USER_TRACE
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "user_id": str,
        "_created": CustomDate(),
        "_updated": CustomDate(),
        "thanks": int,
        "footprint":
            {
                "coordinates": [
                    OR(int, float),
                    OR(int, float)
                ],
                "type": IS("Point")
            }
    }
    default_values = {
        "footprint.coordinates": [0, 0],
        "footprint.type": "Point"
    }


@connection.register
class UserPosts(Document):
    __collection__ = CollectionName.USER_POSTS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "user_id": str,
        "theme_id": str,
        "post_id": str,
        "_created": CustomDate()
    }
    required_fields = [
        'user_id', 'theme_id', 'post_id'
    ]


@connection.register
class UserComments(Document):
    __collection__ = CollectionName.USER_COMMENTS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "user_id": str,
        "theme_id": str,
        "comment_id": str,
        "_created": CustomDate()
    }
    required_fields = [
        'user_id', 'theme_id', 'comment_id'
    ]


@connection.register
class UsersStars(Document):
    __collection__ = CollectionName.USER_STARS
    __database__ = MongoConfig.DB
    structure = {
        "_id": CustomObjectId(),
        "user_id": str,
        "theme_id": str,
        "post_id": str,
        "_created": CustomDate()
    }
    required_fields = [
        'user_id', 'theme_id', 'post_id'
    ]
