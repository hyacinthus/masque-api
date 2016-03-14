from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class UserLevelsList(Resource):
    def get(self):  # get all posts
        cursor = connection.UserLevels.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.UserLevels()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class UserLevel(Resource):
    def get(self, user_level_id):  # get a post by its ID
        cursor = connection.UserLevels.find_one(
            {"_id": ObjectId(user_level_id)})
        return cursor

    def put(self, user_level_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.UserLevels()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_level_id
        doc.save()
        return None, 204

    def delete(self, user_level_id):  # delete a post by its ID
        connection.UserLevels.find_and_modify(
            {"_id": ObjectId(user_level_id)}, remove=True)
        # TODO: delete related data
        return None, 204
