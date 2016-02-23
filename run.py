import json
from datetime import datetime

from bson import ObjectId
from flask import Flask, request, jsonify
from flask.ext.restful import reqparse, abort, Api, Resource
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


app = creat_app()
api = Api(app)

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


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    elif isinstance(obj, str):
        return obj
    raise TypeError("Type not serializable")


def initDB(samples):
    geo_postsCol.drop()
    for row in samples:
        print("inserting into SAMPLES DB: " + str(row))
        geo_postsCol.insert(row)


def abortIfPostDoesNotExist(post_id):
    pass


def allPosts():
    cursor = geo_postsCol.find({})
    results = []
    for post in cursor:
        post["_created"] = json_serial(post["_created"])
        post["_id"] = JSONEncoder().encode(post["_id"])[1:-1]  # 去掉首尾多余的引号
        results.append(post)
    return results


def addPost(post):
    geo_postsCol.insert(post)
    return jsonify(status="ok", response=201)


class JSONEncoder(json.JSONEncoder):
    """Make ObjectId JSON serializable"""

    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


class Geo_post(Resource):
    def get(self, post_id):  # get a post by its ID
        print("   get post")
        abortIfPostDoesNotExist(post_id)
        pass

    def delete(self, post_id):  # delete a post by its ID
        print("   delete post")
        abortIfPostDoesNotExist(post_id)
        pass

    def post(self, post_id):  # update a particular post by its ID
        print("   Update post")
        abortIfPostDoesNotExist(post_id)
        pass


class Geo_postsList(Resource):
    def get(self):  # get all geo_posts
        print("fetch all geo_posts")
        return allPosts()

    def post(self):  # add a new post
        print("Add geo_post")
        json_data = request.get_json(force=True)
        # author = json_data['author']
        # print(author)
        # qID = addPost(post)
        # return [{"post_id": qID, "post": post}]  # return the post ID
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
