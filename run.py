from datetime import datetime

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, request
from flask import make_response
from flask.ext.restful import Api, Resource, abort
from flask_pymongo import PyMongo


def creat_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')
    return app


app = creat_app()
mongo = PyMongo(app, config_prefix='MONGO')
api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


def abortIfPostDoesNotExist(post_id):
    if len(dataForPostID(post_id)) <= 0:
        abort(404, message="Post {} doesn't exist.".format(post_id))


def allPosts():
    cursor = mongo.db.geo_posts.find({})
    return cursor


def addPost(post):
    if "_created" in post:
        # turn an ISO 8601 string like: 2016-02-23T23:41:54.000Z into datetime object
        #
        post["_created"] = datetime.utcnow()
    mongo.db.geo_posts.insert(post)
    return "", 201


def dataForPostID(post_id):
    cursor = mongo.db.geo_posts.find({"_id": ObjectId(post_id)})
    results = []
    for item in cursor:
        results.append(item)
    return results


def deletePost(post_id):
    cursor = mongo.db.geo_posts.remove({"_id": ObjectId(post_id)})
    return "", 204


def putPost(post_id, json_data):
    cursor = mongo.db.geo_posts.update_one(
        {"_id": ObjectId(post_id)},
        {
            "$set": json_data
        }
    )
    return "", 204


class Geo_postAPI(Resource):
    def get(self, post_id):  # get a post by its ID

        abortIfPostDoesNotExist(post_id)
        return dataForPostID(post_id)

    def delete(self, post_id):  # delete a post by its ID

        abortIfPostDoesNotExist(post_id)
        return deletePost(post_id)

    def put(self, post_id):  # update a post by its ID

        abortIfPostDoesNotExist(post_id)
        json_data = request.get_json(force=True)
        return putPost(post_id, json_data)


class Geo_postListAPI(Resource):
    def get(self):  # get all geo_posts
        return allPosts()

    def post(self):  # add a new post

        json_data = request.get_json(force=True)
        return addPost(json_data)


api.add_resource(Geo_postListAPI, '/geo_posts', endpoint='geo_posts')
api.add_resource(Geo_postAPI, '/geo_posts/<string:post_id>', endpoint='geo_post')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
