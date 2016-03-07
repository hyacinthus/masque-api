from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class UserLevelList(Resource):
    def get(self):  # get all posts
        cursor = connection.UserLevel.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.UserLevel()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class UserLevel(Resource):
    def get(self, user_level_id):  # get a post by its ID
        cursor = connection.UserLevel.find({"_id": ObjectId(user_level_id)})
        return check_content(cursor)

    def put(self, user_level_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.UserLevel()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_level_id
        doc.save()
        return None, 204

    def delete(self, user_level_id):  # delete a post by its ID
        connection.UserLevel.find_and_modify(
            {"_id": ObjectId(user_level_id)}, remove=True)
        # TODO: delete related data
        return None, 204
