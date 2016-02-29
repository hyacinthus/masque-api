from flask_restful import Resource, abort, request

from model import *


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class GeoCommentList(Resource):
    def get(self):  # get all comments
        cursor = connection.GeoComment.find()
        return check_content(cursor)

    def post(self):  # add a new comment
        resp = request.get_json(force=True)
        doc = connection.GeoComment()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return "", 201


class GeoComment(Resource):
    def get(self, comment_id):  # get a comment by its ID
        cursor = connection.GeoComment.find({"_id": ObjectId(comment_id)})
        return check_content(cursor)

    def put(self, comment_id):  # update a comment by its ID
        resp = request.get_json(force=True)
        doc = connection.GeoComment()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = comment_id
        doc.save()
        return "", 204

    def delete(self, comment_id):  # delete a comment by its ID
        cursor = connection.GeoComment.find_and_modify(
            {"_id": ObjectId(comment_id)}, remove=True)
        return "", 204
