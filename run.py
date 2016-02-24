from datetime import datetime

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, request
from flask import make_response
from flask.ext.restful import Api, Resource, abort
from pymongo import MongoClient

import config


def creat_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
    return app


def conMongo():
    client = MongoClient(config.DATABASE_URI)
    return client


def output_json(obj, code, headers=None):
    """
    This is needed because we need to use a custom JSON converter
    that knows how to translate MongoDB types to JSON.
    """
    resp = make_response(dumps(obj), code)
    resp.headers.extend(headers or {})

    return resp


DEFAULT_REPRESENTATIONS = {'application/json': output_json}

app = creat_app()
api = Api(app)
api.representations = DEFAULT_REPRESENTATIONS

SAMPLES = [
    {
        "_created": "2014-03-28T00:00:00",
        "author": "ferstar",
        "content": "Keep moving!",
        "hearts": {
            "mask_id": "abcdef",
            "user_id": "abcdef"
        },
        "location": {
            "coordinates": [
                100,
                0
            ],
            "type": "Point"
        },
        "mask_id": "abcdef"
    }
]

# to parse incoming data fields
# parser = reqparse.RequestParser()
# parser.add_argument('geo_post')

db = conMongo()[config.DB_NAME]
geo_postsCol = db.geo_posts


def initDB(samples):
    geo_postsCol.drop()
    for row in samples:
        print("inserting into SAMPLES DB: " + str(row))
        geo_postsCol.insert(row)


def abortIfPostDoesNotExist(post_id):
    if len(dataForPostID(post_id)) <= 0:
        abort(404, message="Post {} doesn't exist.".format(post_id))


def allPosts():
    cursor = geo_postsCol.find({})
    return cursor


def addPost(post):
    if "_created" in post:
        # turn an ISO 8601 string like: 2016-02-23T23:41:54.000Z into datetime object
        #
        post["_created"] = datetime.utcnow()
    geo_postsCol.insert(post)
    return "", 201


def dataForPostID(post_id):
    cursor = geo_postsCol.find({"_id": ObjectId(post_id)})
    results = []
    for item in cursor:
        results.append(item)
    return results


def deletePost(post_id):
    cursor = geo_postsCol.remove({"_id": ObjectId(post_id)})
    return "", 204


def patchPost(post_id, json_data):
    cursor = geo_postsCol.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": json_data
        }
    )
    return "", 204


class Geo_post(Resource):
    def get(self, post_id):  # get a post by its ID
        print("get post")
        abortIfPostDoesNotExist(post_id)
        return dataForPostID(post_id)

    def delete(self, post_id):  # delete a post by its ID
        print("delete post")
        abortIfPostDoesNotExist(post_id)
        return deletePost(post_id)

    def patch(self, post_id):  # update a particular post by its ID
        print("Update post")
        abortIfPostDoesNotExist(post_id)
        json_data = request.get_json(force=True)
        return patchPost(post_id, json_data)


class Geo_postsList(Resource):
    def get(self):  # get all geo_posts
        print("fetch all geo_posts")
        return allPosts()

    def post(self):  # add a new post
        print("Add geo_post")
        json_data = request.get_json(force=True)
        return addPost(json_data)


@app.before_request
def before_request():
    # print("before request " + str(request.endpoint) )
    if request.endpoint == "geo_postslist":
        print("\n\n>> connecting db >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        db = conMongo()[config.DB_NAME]
        geo_postsCol = db['geo_posts']


@app.teardown_request
def teardown_request(exception):
    # print("after request ") + str(request.endpoint)
    if request.endpoint == "geo_postslist":
        print(">> disconnect db >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n\n")
        conMongo().close()


api.add_resource(Geo_postsList, '/geo_posts')
api.add_resource(Geo_post, '/geo_posts/<string:post_id>')
# initDB(SAMPLES) #start with a clean DB


if __name__ == '__main__':
    app.run(host='0.0.0.0')
