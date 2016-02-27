from datetime import datetime

from bson.objectid import ObjectId
from mongokit import IS, OR, Document, Connection
from mongokit.schema_document import CustomType

import config


class CustomDate(CustomType):
    mongo_type = datetime  # optional, just for more validation
    python_type = str
    init_type = None  # optional, fill the first empty value

    def to_bson(self, value):
        """convert type to a mongodb type"""
        if value == "" or value is None:  # update time if not received.
            value = datetime.strftime(datetime.utcnow(), '%Y-%m-%d %H:%M:%S')
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')

    def to_python(self, value):
        """convert type to a python type"""
        return datetime.strftime(value, '%Y-%m-%d %H:%M:%S')

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


connection = Connection(host=config.MONGO_HOST, port=config.MONGO_PORT)


@connection.register
class GeoPost(Document):
    __collection__ = 'geo_posts'
    __database__ = config.MONGO_DB
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
            "type": IS("Point", "MultiPoint", "LineString", "MultiLineString",
                       "Polygon", "MultiPolygon", "GeometryCollection")
        },
        "content": str,
        "author": str
    }
    # required_fields = [
    #     'mask_id', 'hearts.mask_id', 'hearts.user_id'
    # ]
    # default_values = {
    #     "location.type": "Point"
    # }


@connection.register
class GeoComment(Document):
    __collection__ = 'geo_comments'
    __database__ = config.MONGO_DB
    structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": CustomObjectId(),
        "hearts": {
            "mask_id": CustomObjectId(),
            "user_id": CustomObjectId()
        },
        "post_id": CustomObjectId(),
        "author": str,
        "content": str
    }
