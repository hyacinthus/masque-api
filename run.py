from datetime import datetime

from bson.json_util import dumps
from bson.objectid import ObjectId
from flask import Flask, request, make_response
from flask.ext.restful import Api, Resource, abort
from flask_pymongo import PyMongo


def creat_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py', silent=True)
    return app


app = creat_app()
mongo = PyMongo(app, config_prefix='MONGO')
api = Api(app)


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


def notFound(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    return obj


class Geo_postAPI(Resource):
    def get(self, post_id):  # get a post by its ID
        cursor = mongo.db.geo_posts.find({"_id": ObjectId(post_id)})
        return notFound(cursor)

    def delete(self, post_id):  # delete a post by its ID
        cursor = mongo.db.geo_posts.remove({"_id": ObjectId(post_id)})
        return "", 204

    def put(self, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        cursor = mongo.db.geo_posts.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": resp
            }
        )
        return "", 204


class Geo_postListAPI(Resource):
    def get(self):  # get all geo_posts
        cursor = mongo.db.geo_posts.find({})
        return notFound(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        if "_created" in resp:
            # turn an ISO 8601 string like: 2016-02-23T23:41:54.000Z into datetime object
            resp["_created"] = datetime.utcnow()
        mongo.db.geo_posts.insert(resp)
        return "", 201


api.add_resource(Geo_postListAPI, '/geo_posts', endpoint='geo_posts')
api.add_resource(Geo_postAPI, '/geo_posts/<string:post_id>', endpoint='geo_post')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
