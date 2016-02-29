class FlaskConfig:
    DEBUG = False
    PORT = 5000


class MongoConfig:
    HOST = "localhost"
    PORT = 27017
    DB = "test"


class APIConfig:
    MAX_SCAN = 100  # set int(0) to query all
    PAGESIZE = 10  # set int(0) to return all query results


class CollectionName:
    GEO_POSTS = "geo_posts"
    GEO_COMMENTS = "geo_comments"
    USERS = "users"
