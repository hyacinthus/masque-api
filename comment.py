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


class GeoCommentList(Resource):
    def get(self):  # get all comments
        cursor = db.geo_comments.find({})
        return check_content(cursor)

    def post(self):  # add a new comment
        resp = request.get_json(force=True)
        resp["_created"] = datetime.utcnow()
        db.geo_comments.insert(resp)
        return "", 201


class GeoComment(Resource):
    def get(self, comment_id):  # get a comment by its ID
        cursor = db.geo_comments.find({"_id": ObjectId(comment_id)})
        return check_content(cursor)

    def put(self, comment_id):  # update a comment by its ID
        resp = request.get_json(force=True)
        cursor = db.geo_comments.update_one(
            {"_id": ObjectId(comment_id)},
            {
                "$set": resp
            }
        )
        return "", 204

    def delete(self, comment_id):  # delete a comment by its ID
        cursor = db.geo_comments.remove({"_id": ObjectId(comment_id)})
        return "", 204
