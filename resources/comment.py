from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from config import MongoConfig
from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    return obj


class CommentsList(Resource):
    def get(self, theme_id):  # get all comments
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find()
        return check_content(cursor)

    def post(self, theme_id):  # add a new comment
        resp = request.get_json(force=True)
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        doc = collection.Comments()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Comments(Resource):
    def get(self, theme_id, comment_id):  # get a comment by its ID
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        cursor = collection.Comments.find({"_id": ObjectId(comment_id)})
        return check_content(cursor)

    def put(self, theme_id, comment_id):  # update a comment by its ID
        resp = request.get_json(force=True)
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        doc = collection.Comments()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = comment_id
        doc.save()
        return None, 204

    def delete(self, theme_id, comment_id):  # delete a comment by its ID
        collection = connection[MongoConfig.DB]["comments_" + theme_id]
        collection.Comments.find_and_modify(
            {"_id": ObjectId(comment_id)}, remove=True)
        return None, 204
