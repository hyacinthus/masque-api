import os

class FlaskConfig:
    _host = os.getenv("FLASK_HOST", "localhost")
    _port = os.getenv("FLASK_PORT", "5000")
    SERVER_NAME = "%s:%s" % (_host, _port)
    DEBUG = os.getenv("FLASK_DEBUG","0") in ("True","TRUE","true","1")


class MongoConfig:
    HOST = os.getenv("MONGO_HOST", "localhost")
    PORT = int(os.getenv("MONGO_PORT", "27017"))
    DB = os.getenv("MONGO_DB", "test")
    USER = os.getenv("MONGO_USER", "marvin")
    PASS = os.getenv("MONGO_PASS", "tarsbot.702")


class RedisConfig:
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", "6379"))
    DB = int(os.getenv("REDIS_DB", "8"))


class APIConfig:
    MAX_SCAN = 100  # set int(0) to query all
    PAGESIZE = 10  # set int(0) to return all query results


class CollectionName:
    USERS = "users"
    USER_POSTS = "user_posts"
    USER_COMMENTS = "user_comments"
    USER_STARS = "user_stars"
    THEMES = "themes"
    DEVICES = "devices"
    USER_LEVELS = "user_levels"
    MASKS = "masks"
    BOARD_POSTS = "board_posts"
    BOARD_COMMENTS = "board_comments"
    PARAMETERS = "parameters"
    DEVICE_TRACE = "device_trace"
    MESSAGES = "messages"
    USER_TRACE = "user_trace"
    SCHOOLS = "schools"
