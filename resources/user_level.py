from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class UserLevelsList(Resource):
    def get(self):  # get all posts
        cursor = connection.UserLevels.find()
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.UserLevels()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return {
                   "status": "ok",
                   "message": "",
                   "data": doc
               }, 201


class UserLevel(Resource):
    def get(self, user_level_id):  # get a post by its ID
        cursor = connection.UserLevels.find_one(
            {"_id": ObjectId(user_level_id)})
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, user_level_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.UserLevels.find_and_modify(
            {"_id": ObjectId(user_level_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, user_level_id):  # delete a post by its ID
        connection.UserLevels.find_and_modify(
            {"_id": ObjectId(user_level_id)}, remove=True)
        # TODO: delete related data
        return '', 204
