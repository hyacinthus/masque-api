import logging
from datetime import datetime
from urllib.parse import quote

from bson.objectid import ObjectId
from mongokit import IS, OR, Document, Connection
from mongokit.schema_document import CustomType
from redis import StrictRedis

from config import MongoConfig, CollectionName, RedisConfig

redisdb = StrictRedis(host=RedisConfig.HOST,
                      port=RedisConfig.PORT,
                      db=RedisConfig.DB,
                      decode_responses=True)
log = logging.getLogger("masque.model")


def get_host():
    if MongoConfig.USER and MongoConfig.PASS:
        _user = quote(MongoConfig.USER)
        _pass = quote(MongoConfig.PASS)
        _auth = '{}:{}@'.format(_user, _pass)
    else:
        _auth = ''
    _host = 'mongodb://{}{}:{}/{}'.format(
        _auth,
        MongoConfig.HOST,
        MongoConfig.PORT,
        MongoConfig.DB,
    )
    log.debug(_host)
    return _host


connection = Connection(host=get_host())


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


# Oauth2 model
class Client():
    """A client is the app which want to use the resource of a user.
    It is suggested that the client is registered by a user on your site,
    but it is not required.
    If client exists, get it, if not, create it."""

    def __init__(self, client_id):
        if client_id:
            self.client_id = client_id
            device = connection.Devices.find_one({"_id": client_id})
            if not device:
                new_device = connection.Devices()
                new_device._id = client_id
                new_device.save()

    @property
    def client_secret(self):
        return None

    @property
    def client_type(self):
        return None

    @property
    def redirect_uris(self):
        return None

    @property
    def default_redirect_uri(self):
        return None

    @property
    def default_scopes(self):
        return []

    @property
    def allowed_grant_types(self):
        return ("password", "refresh_token")


# Oauth2 model in redis
class Grant():
    """A grant token is created in the authorization flow,
    and will be destroyed when the authorization finished.
    new empty grant: Grant()
    get exist grant: Grant(client_id,code)"""
    client_id = None
    code = None
    redirect_uri = None
    scopes = None
    user_id = None
    expires = None
    saved = False

    def __init__(self, client_id=None, code=None):
        if client_id and code:
            if redisdb.exists("oauth:grant:%s:%s:user_id" %
                                      (client_id, code)):
                self.client_id = client_id
                self.code = code
                self.redirect_uri = self._get("redirect_uri")
                self.scopes = self._get("scopes")
                self.user_id = self._get("user_id")
                self.expires = self._get("expires")
                self.saved = True

    def _get(self, key):
        return redisdb.get("oauth:grant:%s:%s:%s" % (self.client_id,
                                                     self.code,
                                                     key))

    def _set(self, key, value):
        redisdb.set("oauth:grant:%s:%s:%s" % (self.client_id,
                                              self.code,
                                              key),
                    value)

    def _del(self, key):
        redisdb.delete("oauth:grant:%s:%s:%s" % (self.client_id,
                                                 self.code, key))

    def save(self):
        if self.client_id and self.code:
            self._set("redirect_uri", self.redirect_uri)
            self._set("scopes", self.scopes)
            self._set("user_id", self.user_id)
            self._set("expires", self.expires)
            self.saved = True

    def delete(self):
        if self.client_id and self.code:
            self._del("redirect_uri")
            self._del("scopes")
            self._del("user_id")
            self._del("expires")
            self.saved = False

    @property
    def user(self):
        if self.user_id:
            return connection.Users.find_one({"_id": ObjectId(self.user_id)})


class Token():
    """ bearer token is the final token
    that could be used by the client.
    new empty token: Token()
    get exist token: Token(access_token)
    get by refresh token: Token(refresh_token=refresh_token)"""
    access_token = None
    refresh_token = None
    client_id = None
    scopes = None
    user_id = None
    expires = None
    saved = False

    def __init__(self, access_token=None, refresh_token=None):
        if access_token:
            if redisdb.exists("oauth:access_token:%s:user_id" %
                                      access_token):
                self.access_token = access_token
                self.refresh_token = self._geta("refresh_token")
                self.client_id = self._geta("client_id")
                self.scopes = self._geta("scopes")
                self.user_id = self._geta("user_id")
                self.expires = datetime.strptime(self._geta("expires"),
                                                 "%Y-%m-%d %H:%M:%S.%f")
                self.saved = True
        elif refresh_token:
            if redisdb.exists("oauth:refresh_token:%s:access_token" %
                                      refresh_token):
                self.refresh_token = refresh_token
                self.access_token = self._getr("access_token")
                self.client_id = self._getr("client_id")
                self.scopes = self._getr("scopes")
                self.user_id = self._getr("user_id")
                self.expires = datetime.strptime(self._getr("expires"),
                                                 "%Y-%m-%d %H:%M:%S.%f")
                self.saved = True

    def _geta(self, key):
        return redisdb.get("oauth:access_token:%s:%s" %
                           (self.access_token, key))

    def _getr(self, key):
        return redisdb.get("oauth:refresh_token:%s:%s" %
                           (self.refresh_token, key))

    def _dela(self, access_token):
        redisdb.delete("oauth:access_token:%s:refresh_token" %
                       access_token)
        redisdb.delete("oauth:access_token:%s:client_id" %
                       access_token)
        redisdb.delete("oauth:access_token:%s:scopes" %
                       access_token)
        redisdb.delete("oauth:access_token:%s:user_id" %
                       access_token)
        redisdb.delete("oauth:access_token:%s:expires" %
                       access_token)

    def _delr(self, refresh_token):
        redisdb.delete("oauth:refresh_token:%s:access_token" %
                       refresh_token)
        redisdb.delete("oauth:refresh_token:%s:client_id" %
                       refresh_token)
        redisdb.delete("oauth:refresh_token:%s:scopes" %
                       refresh_token)
        redisdb.delete("oauth:refresh_token:%s:user_id" %
                       refresh_token)
        redisdb.delete("oauth:refresh_token:%s:expires" %
                       refresh_token)

    def save(self):
        # one token per one client one user
        old_access = redisdb.get("oauth:user:%s:%s" %
                                 (self.user_id, self.client_id))
        if old_access and old_access != self.access_token:
            old_refresh = redisdb.get(
                "oauth:access_token:%s:refresh_token" %
                old_access)
            if old_refresh:
                self._delr(old_refresh)
            self._dela(old_access)
        # save user index
        if self.client_id and self.user_id:
            redisdb.set("oauth:user:%s:%s" %
                        (self.user_id, self.client_id),
                        self.access_token)
        # save access token
        redisdb.set("oauth:access_token:%s:refresh_token" %
                    self.access_token, self.refresh_token)
        redisdb.set("oauth:access_token:%s:client_id" %
                    self.access_token, self.client_id)
        redisdb.set("oauth:access_token:%s:scopes" %
                    self.access_token, self.scopes)
        redisdb.set("oauth:access_token:%s:user_id" %
                    self.access_token, self.user_id)
        redisdb.set("oauth:access_token:%s:expires" %
                    self.access_token, self.expires)
        # save refresh token
        redisdb.set("oauth:refresh_token:%s:access_token" %
                    self.refresh_token, self.access_token)
        redisdb.set("oauth:refresh_token:%s:client_id" %
                    self.refresh_token, self.client_id)
        redisdb.set("oauth:refresh_token:%s:scopes" %
                    self.refresh_token, self.scopes)
        redisdb.set("oauth:refresh_token:%s:user_id" %
                    self.refresh_token, self.user_id)
        redisdb.set("oauth:refresh_token:%s:expires" %
                    self.refresh_token, self.expires)
        self.saved = True

    def delete(self):
        if self.refresh_token:
            self._delr(self.refresh_token)
        if self.access_token:
            self._dela(self.access_token)
        redisdb.delete("oauth:user:%s:%s" %
                       (self.user_id, self.client_id))
        self.saved = False

    @property
    def user(self):
        if self.user_id:
            return connection.Users.find_one({"_id": ObjectId(self.user_id)})

    @property
    def client(self):
        if self.client_id:
            return Client(self.client_id)


class RootDocument(Document):
    __database__ = MongoConfig.DB
    structure = {}
    skip_validation = True
    use_dot_notation = True


class Common(RootDocument):
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
class Posts(Common):
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
class Comments(Common):
    structure = {
        "content": str,
        "post_id": str,
    }
    required_fields = [
        "post_id"
    ]


@connection.register
class Users(RootDocument):
    __collection__ = CollectionName.USERS

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
class Themes(RootDocument):
    __collection__ = CollectionName.THEMES

    structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "district", "virtual", "private", "system"),
        "short_name": str,
        "full_name": str,
        "locale": {
            "nation": str,
            "province": str,
            "city": str,
            "district": str
        }
    }
    default_values = {
        "category": "school",
        "short_name": "",
        "full_name": "",
        "locale.nation": "中国",
        "locale.province": "",
        "locale.city": "",
        "locale.district": ""
    }


@connection.register
class Devices(RootDocument):
    __collection__ = CollectionName.DEVICES
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
class UserLevels(RootDocument):
    __collection__ = CollectionName.USER_LEVELS
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
class Masks(RootDocument):
    __collection__ = CollectionName.MASKS
    structure = {
        "_id": CustomObjectId(),
        "name": str,
        "mask_url": str,
    }


@connection.register
class BoardPosts(RootDocument):
    __collection__ = CollectionName.BOARD_POSTS
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


@connection.register
class Parameters(RootDocument):
    __collection__ = CollectionName.PARAMETERS
    structure = {
        "_id": CustomObjectId(),
        "default_masks": list
    }


@connection.register
class DeviceTrace(RootDocument):
    __collection__ = CollectionName.DEVICE_TRACE
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
class Messages(RootDocument):
    __collection__ = CollectionName.MESSAGES
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
class Notifications(RootDocument):
    __collection__ = CollectionName.NOTIFICATIONS
    structure = {
        "_id": CustomObjectId(),
        "user_id": str
        "type": str
        "theme_id": str
        "post_id": str
        "message_id": str
    }


@connection.register
class UserTraces(RootDocument):
    __collection__ = CollectionName.USER_TRACE
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
class UserPosts(RootDocument):
    __collection__ = CollectionName.USER_POSTS
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
class UserComments(RootDocument):
    __collection__ = CollectionName.USER_COMMENTS
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
class UserStars(UserPosts):
    __collection__ = CollectionName.USER_STARS


@connection.register
class Schools(RootDocument):
    __collection__ = CollectionName.SCHOOLS
