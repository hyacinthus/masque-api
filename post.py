from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import Resource, abort, request
from pymongo import MongoClient

import config

client = MongoClient(config.MONGO_URI)
db = client[config.MONGO_DB]


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    return obj


class GeoPostList(Resource):
    def get(self):  # get all posts
        cursor = db.geo_posts.find({})
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        resp["_created"] = datetime.utcnow()
        db.geo_posts.insert(resp)
        return "", 201


class GeoPost(Resource):
    def get(self, post_id):  # get a post by its ID
        cursor = db.geo_posts.find({"_id": ObjectId(post_id)})
        return check_content(cursor)

    def put(self, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        cursor = db.geo_posts.update_one(
            {"_id": ObjectId(post_id)},
            {
                "$set": resp
            }
        )
        return "", 204

    def delete(self, post_id):  # delete a post by its ID
        cursor = db.geo_posts.remove({"_id": ObjectId(post_id)})
        # delete related comments
        cursor = db.geo_comments.remove({"post_id": post_id})
        return "", 204
