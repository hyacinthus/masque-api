import os


class AliConfig:
    IKEY = os.getenv("ALI_IKEY", "")
    AKEY = os.getenv("ALI_AKEY", "")
    HOST = os.getenv("ALI_STS_SERVER", "sts.aliyuncs.com")
    API_VERSION = os.getenv("ALI_API_VERSION", "2015-04-01")
    ROLEARN = os.getenv(
        "ALI_ROLEARN",
        'acs:ram::1521619666563483:role/aliyunosstokengeneratorrole'
    )
    # 阿里大鱼参数
    SMS_IKEY = os.getenv("SMS_IKEY", "")
    SMS_AKEY = os.getenv("SMS_AKEY", "")
    SMS_TTL = os.getenv("SMS_TTL", 10)
    SMS_TEMPLATE_CODE = os.getenv("SMS_TEMPLATE_CODE", "SMS_6775282")
    SMS_FREE_SIGN_NAME = os.getenv("SMS_FREE_SIGN_NAME", "注册验证")
    SMS_TYPE = os.getenv("SMS_TYPE", "normal")
    APP_NAME = os.getenv("SMS_APP_NAME", "假面")
    REGIONID = os.getenv("REGION_ID", "cn-beijing")


class FlaskConfig:
    DEBUG = os.getenv("FLASK_DEBUG", "0") in ("True", "TRUE", "true", "1")
    OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 864000


class DebugConfig:
    HOST = os.getenv("DEBUG_HOST", "0.0.0.0")
    PORT = int(os.getenv("DEBUG_PORT", "5000"))


class LogConfig:
    PATH = os.getenv("LOG_PATH", None)
    ROOT_LEVEL = os.getenv("LOG_ROOT_LEVEL", "INFO")
    SCREEN_LEVEL = os.getenv("LOG_SCREEN_LEVEL", None)
    FILE_LEVEL = os.getenv("LOG_FILE_LEVEL", None)
    DB_LEVEL = os.getenv("LOG_DB_LEVEL", "INFO")
    PUBU_LEVEL = os.getenv("LOG_PUBU_LEVEL", "WARN")


class MongoConfig:
    HOST = os.getenv("MONGO_HOST", "localhost")
    PORT = int(os.getenv("MONGO_PORT", "27017"))
    DB = os.getenv("MONGO_DB", "test")
    USER = os.getenv("MONGO_USER", None)
    PASS = os.getenv("MONGO_PASS", None)


class RedisConfig:
    HOST = os.getenv("REDIS_HOST", "localhost")
    PORT = int(os.getenv("REDIS_PORT", "6379"))
    DB = int(os.getenv("REDIS_DB", "8"))


class APIConfig:
    AMAP_AKEY = os.getenv("AMAP_AKEY", "ab158f36829f810346ef3526727f1aa4")
    MAX_SCAN = 1000  # set int(0) to query all
    PAGESIZE = 50  # set int(0) to return all query results


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
    NOTIFICATIONS = "notifications"
    USER_TRACE = "user_trace"
    SCHOOLS = "schools"
    FEEDBACK = "feedback"
    REPORT_POSTS = "report_posts"
    REPORT_COMMENTS = "report_comments"
