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


app = creat_app()
api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


@app.before_request
def before_request():
    if request.endpoint is not None:
        db = conMongo()[config.DB_NAME]
        geo_postsCol = db['geo_posts']


@app.teardown_request
def teardown_request(exception):
    if request.endpoint is not None:
        conMongo().close()


# to parse incoming data fields
# parser = reqparse.RequestParser()
# parser.add_argument('geo_post')

db = conMongo()[config.DB_NAME]
geo_postsCol = db.geo_posts


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


def putPost(post_id, json_data):
    cursor = geo_postsCol.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": json_data
        }
    )
    return "", 204


class Geo_postAPI(Resource):
    def get(self, post_id):  # get a post by its ID
        print("get post")
        abortIfPostDoesNotExist(post_id)
        return dataForPostID(post_id)

    def delete(self, post_id):  # delete a post by its ID
        print("delete post")
        abortIfPostDoesNotExist(post_id)
        return deletePost(post_id)

    def put(self, post_id):  # update a post by its ID
        print("Update post")
        abortIfPostDoesNotExist(post_id)
        json_data = request.get_json(force=True)
        return putPost(post_id, json_data)


class Geo_postListAPI(Resource):
    def get(self):  # get all geo_posts
        return allPosts()

    def post(self):  # add a new post
        print("Add geo_post")
        json_data = request.get_json(force=True)
        return addPost(json_data)


api.add_resource(Geo_postListAPI, '/geo_posts', endpoint='geo_posts')
api.add_resource(Geo_postAPI, '/geo_posts/<string:post_id>', endpoint='geo_post')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
