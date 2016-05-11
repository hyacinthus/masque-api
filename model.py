import logging
import uuid
from datetime import datetime
from urllib.parse import quote

from bson.objectid import ObjectId
from flask_restful import Resource, reqparse
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
        if not value:  # update time if not received.
            return datetime.utcnow()
        return datetime.fromtimestamp(value)

    def to_python(self, value):
        """convert type to a python type"""
        return datetime.timestamp(value) // 1  # 输出去掉小数部分

    def validate(self, value, path):
        """OPTIONAL : useful to add a validation layer"""
        if value is not None:
            pass  # ... do something here


class CustomObjectId(CustomType):
    mongo_type = ObjectId  # optional, just for more validation
    python_type = str
    init_type = None  # optional, fill the first empty value

    def to_bson(self, value):
        """convert type to a mongodb type
        只有符合 ObjectId 类型的才转换
        """
        if not value or ObjectId.is_valid(value):
            return ObjectId(value)
        else:
            return value

    def to_python(self, value):
        """convert type to a python type
        已经是 str 类型的直接输出, 不转换
        """
        if isinstance(value, str):
            return value
        else:
            return str(value)

    def validate(self, value, path):
        """OPTIONAL : useful to add a validation layer"""
        if value is not None:
            pass  # ... do something here


class CustomMaskList(CustomType):
    mongo_type = list  # optional, just for more validation
    python_type = list
    init_type = None  # optional, fill the first empty value

    def to_bson(self, value):
        """convert type to a mongodb type"""
        if not value:
            # 随机抽取8个头像id填入mask字段
            sample = connection[MongoConfig.DB][CollectionName.MASKS].aggregate(
                [{"$sample": {"size": 8}}]
            )
            return [str(i['_id']) for i in sample['result']]
        return value

    def to_python(self, value):
        """convert type to a python type"""
        return value

    def validate(self, value, path):
        """OPTIONAL : useful to add a validation layer"""
        if value:
            pass  # ... do something here


class TokenResource(Resource):
    """从 Authorization Headers 中取得用户信息
    - 输入: 无
    - 输出: user_info (包含 user 对象和 device_id), 权限限制信息 limit_info
    """

    def __init__(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'authorization',
            type=str,
            location='headers'
        )
        args = parser.parse_args()
        token = args["authorization"]
        if token.startswith("Bearer "):
            self.user_info = UserInfo(token.split()[1])
        else:
            log.error("unsupported authorization header")

    @property
    def limit_info(self):
        """获取用户权限信息"""

        if self.user_info.user.user_level_id:
            user_level = connection.UserLevels.find_one(
                {"_id": self.user_info.user.user_level_id}
            )
            return user_level if user_level else None
        else:
            log.error("level information does not exist.")


class UserInfo:
    """根据 Authorization Headers 传递的 token 取得 device_id 和对应 user \n
    - 输入: Bearer Token \n
    - 输出: device_id 和对应 user
    """

    def __init__(self, token):
        if token:
            if redisdb.exists(
                    "oauth:access_token:{}:client_id".format(token)
            ):
                self.device_id = redisdb.get(
                    "oauth:access_token:{}:client_id".format(token)
                )
        else:
            log.error("{} is not a valid string".format(token))

    @property
    def user(self):
        device = connection.Devices.find_one({"_id": self.device_id})
        if not device:
            log.error("device {} not found".format(self.device_id))
        else:
            return connection.Users.find_one({"_id": ObjectId(device.user_id)})


class CheckPermission:
    """权限检测 \n
    - 输入: 当前 user_id 类型 str \n
    - 输出: 当天发帖/举报/感谢/消息次数 类型 int \n
    - Optional: 支持写入操作, 每次赋值即给对应次数加指定的 value, 可以是负值, 即表示减
    """

    def __init__(self, user_id):
        if user_id:
            # 检查 redis 数据库
            self.user_id = user_id
            self.is_first_login = self._day()
        else:
            log.error("user_id missed.")

    def _day(self):
        hash_map = {
            "day": datetime.now().date(),
            "post": 0,
            "comment": 0,
            "report": 0,
            "message": 0,
            "heart": 0,
            "exp": 0
        }
        if not redisdb.hexists(
                "user:{}:daily_count".format(self.user_id), "day"
        ):
            # 不存在记录则初始化
            redisdb.hmset(
                "user:{}:daily_count".format(self.user_id), hash_map
            )
            return True

        else:
            old_day = redisdb.hget(
                "user:{}:daily_count".format(self.user_id), "day"
            )
            old_day = datetime.strptime(old_day, "%Y-%m-%d").date()
            day_delta = (hash_map["day"] - old_day).days
            if day_delta:
                # 超过一天, 归档并重置数据
                log.debug("%s" % day_delta)
                # TODO HASH 数据归档
                redisdb.hmset(
                    "user:{}:daily_count".format(self.user_id), hash_map
                )
                return True
            return False

    @property
    def post(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "post"))

    @post.setter
    def post(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "post", value
        )

    @property
    def comment(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "comment"))

    @comment.setter
    def comment(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "comment", value
        )

    @property
    def report(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "report"))

    @report.setter
    def report(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "report", value
        )

    @property
    def message(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "message"))

    @message.setter
    def message(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "message", value
        )

    @property
    def heart(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "heart"))

    @heart.setter
    def heart(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "heart", value
        )

    @property
    def exp(self):
        return int(
            redisdb.hget("user:{}:daily_count".format(self.user_id), "exp"))

    @exp.setter
    def exp(self, value):
        redisdb.hincrby(
            "user:{}:daily_count".format(self.user_id), "exp", value
        )


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
    use_schemaless = True
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
            "type": IS("Point", "None")
        },
        "author": str
    }
    required_fields = [
        "author",
        "mask_id"
    ]
    default_values = {
        "location.coordinates": [108.947001, 34.259458],
        "location.type": "None",
        "hearts": [],
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
        "label": {
            "name": str,
            "color": str
        },
        "comment_count": int,
        "_updated": CustomDate(),
        "school": str
    }
    # required_fields = [
    #     "content.text"
    # ]
    default_values = {
        "content.type": "text",
        "content.text": "",
        "content.photo": "",
        "content.options": [],
        "label.name": "",
        "label.color": "",
        "comment_count": 0,
        "school": ""
    }


@connection.register
class Comments(Common):
    structure = {
        "content": str,
        "post_id": str,
        "index": int,
        "deleted": bool
    }
    required_fields = [
        "post_id",
        "content",
    ]
    default_values = {
        "index": 1,
        "deleted": False
    }


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
        "masks": CustomMaskList(),
        "home": {
            "full_name": str,
            "short_name": str,
            "theme_id": str
        },
        "subscribed": list,
        "options": {
            "new_comment": bool,
            "star_comment": bool,
            "post_hearted": bool,
            "comment_hearted": bool,
        }
    }
    # required_fields = [
    #     "content.text"
    # ]
    default_values = {
        "user_level_id": "level1",
        "exp": 1,
        "hearts_received": 0,
        "hearts_owned": 0,
        "cellphone": "",
        "home.short_name": "",
        "home.full_name": "",
        "home.theme_id": "",
        "options.new_comment": True,
        "options.star_comment": True,
        "options.post_hearted": True,
        "options.comment_hearted": True,
    }


@connection.register
class Themes(RootDocument):
    __collection__ = CollectionName.THEMES

    structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "city", "district", "virtual", "private",
                       "system"),
        "subcate": str,
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
        "subcate": "",
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
    default_values = {
        "name": ""
    }


@connection.register
class UserLevels(RootDocument):
    __collection__ = CollectionName.USER_LEVELS
    structure = {
        "_id": str,
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
    required_fields = [
        "_id"
    ]
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
        "_id": str,
        "category": IS("system", "user")
    }
    default_values = {
        "_id": uuid.uuid1().hex,
        "category": "user"
    }


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
        "cellphone": str,
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point")
        }
    }
    default_values = {
        "cellphone": str,
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
        "_created": CustomDate(),
        "current_user": str,
        "user_id": str,
        "mask_id": str,
        "title": str,
        "type": str,
        "content": str,
        "mask_id": str,
        "theme_id": str,
        "comment_id": str,
        "post_id": str,
        "message_id": str,
        "index": int,
    }
    default_values = {
        "user_id": '',
        "current_user": '',
        "mask_id": "",
        "title": '',
        "type": '',
        "content": '',
        "theme_id": '',
        "post_id": '',
        "message_id": '',
        "comment_id": '',
        "index": 1,
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
    indexes = [
        {
            'fields': 'user_id',
        },
        {
            'fields': 'theme_id',
        },
        {
            'fields': 'comment_id',
        }
    ]


@connection.register
class UserStars(UserPosts):
    __collection__ = CollectionName.USER_STARS


@connection.register
class Schools(RootDocument):
    __collection__ = CollectionName.SCHOOLS


@connection.register
class Feedback(RootDocument):
    __collection__ = CollectionName.FEEDBACK
    structure = {
        "_id": CustomObjectId(),
        "author": str,
        "category": IS("error", "none"),
        "_created": CustomDate(),
        "full_name": str,
        "short_name": str,
        "archived": bool,
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point")
        }
    }
    required_fields = [
        "full_name",
        "short_name",
        "location.coordinates"
    ]
    default_values = {
        "archived": False,
        "category": "error",
        "location.type": "Point",
        "location.coordinates": [108.947001, 34.259458],
    }


@connection.register
class ReportPosts(RootDocument):
    __collection__ = CollectionName.REPORT_POSTS
    structure = {
        "_id": CustomObjectId(),
        "author": str,
        "reporters": list,
        "theme_id": str,
        "post_id": str,
        "archived": bool,
        "_created": CustomDate(),
        "_updated": CustomDate(),
    }
    required_fields = [
        "author",
        "theme_id",
        "post_id",
    ]
    default_values = {
        "archived": False,
    }


@connection.register
class ReportComments(RootDocument):
    __collection__ = CollectionName.REPORT_COMMENTS
    structure = {
        "_id": CustomObjectId(),
        "author": str,
        "reporters": list,
        "theme_id": str,
        "post_id": str,
        "comment_id": str,
        "archived": bool,
        "_created": CustomDate(),
        "_updated": CustomDate(),
    }
    required_fields = [
        "author",
        "theme_id",
        "comment_id",
    ]
    default_values = {
        "archived": False,
    }


@connection.register
class TrashPosts(Posts):
    __collection__ = CollectionName.TRASH_POSTS
    structure = {
        "_id": str
    }


@connection.register
class TrashComments(Comments):
    __collection__ = CollectionName.TRASH_COMMENTS
    structure = {
        "_id": str
    }


@connection.register
class UserImages(RootDocument):
    __collection__ = CollectionName.USER_IMAGES
    structure = {
        "_id": str,
        "category": IS("mask", "post"),
        "author": str,
        "_created": CustomDate(),
    }
    default_values = {
        "_id": uuid.uuid1().hex,
    }


@connection.register
class Detections(RootDocument):
    __collection__ = CollectionName.DETECTIONS
    structure = {
        "_id": str,
        "bucket": str,
        "author": str,
        "archived": bool,
        "_created": CustomDate(),
    }
    required_fields = [
        "_id",
        "bucket",
        "author"
    ]
    default_values = {
        "archived": False,
    }


@connection.register
class PostLog(RootDocument):
    __collection__ = CollectionName.POST_LOG
    structure = {
        "_id": CustomObjectId(),
        "theme_id": str,
        "post_id": str,
        "user_id": str,
        "_created": CustomDate(),
    }
    required_fields = [
        'user_id', 'theme_id', 'post_id'
    ]
    default_values = {
        "user_id": '',
        "theme_id": '',
        "post_id": '',
    }


@connection.register
class CommentLog(RootDocument):
    __collection__ = CollectionName.COMMENT_LOG
    structure = {
        "_id": CustomObjectId(),
        "theme_id": str,
        "post_id": str,
        "comment_id": str,
        "user_id": str,
        "_created": CustomDate(),
    }
    required_fields = [
        'user_id', 'theme_id', 'post_id', 'comment_id'
    ]
    default_values = {
        "user_id": '',
        "theme_id": '',
        "post_id": '',
        "comment_id": ''
    }


@connection.register
class SignUpLog(RootDocument):
    __collection__ = CollectionName.SIGN_UP_LOG
    structure = {
        "_id": CustomObjectId(),
        "device_id": str,
        "user_id": str,
        "_created": CustomDate(),
    }
    required_fields = [
        'user_id', 'device_id'
    ]
    default_values = {
        "user_id": '',
        "device_id": '',
    }


@connection.register
class SignInLog(RootDocument):
    __collection__ = CollectionName.SIGN_IN_LOG
    structure = {
        "_id": CustomObjectId(),
        "device_id": str,
        "user_id": str,
        "_created": CustomDate(),
    }
    required_fields = [
        'user_id', 'device_id'
    ]
    default_values = {
        "user_id": '',
        "device_id": '',
    }


@connection.register
class GeoRequestLog(RootDocument):
    __collection__ = CollectionName.GEO_REQUEST_LOG
    structure = {
        "_id": CustomObjectId(),
        "user_id": str,
        "location": {
            "coordinates": [
                OR(int, float),
                OR(int, float)
            ],
            "type": IS("Point", "None")
        },
        "_created": CustomDate(),
        "schools": list
    }
    required_fields = [
        'user_id'
    ]
    default_values = {
        "location.coordinates": [108.947001, 34.259458],
        "location.type": "Point",
    }


@connection.register
class PostsDeleteLog(RootDocument):
    __collection__ = CollectionName.POSTS_DELETE_LOG
    structure = {
        "_id": CustomObjectId(),
        "theme_id": str,
        "post_id": str,
        "author ": str,
        "admin": str,
        "reason": str,
        "exp_reduce": int,
        "ban_days": int,
        "ban_account": int,
    }
    default_values = {
        "admin": "",
        "reason": ""
    }


@connection.register
class CommentsBanLog(RootDocument):
    __collection__ = CollectionName.COMMENTS_BAN_LOG
    structure = {
        "_id": CustomObjectId(),
        "theme_id": str,
        "post_id": str,
        "comment_id": str,
        "author ": str,
        "admin": str,
        "reason": str,
        "exp_reduce": int,
        "ban_days": int,
        "ban_account": int,
    }
    default_values = {
        "admin": "",
        "reason": ""
    }
