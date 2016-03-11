from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class UserTracesList(Resource):
    def get(self):  # get all posts
        cursor = connection.UserTraces.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.UserTraces()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class UserTraces(Resource):
    def get(self, user_trace_id):  # get a post by its ID
        cursor = connection.UserTraces.find({"_id": ObjectId(user_trace_id)})
        return cursor

    def put(self, user_trace_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.UserTraces()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_trace_id
        doc.save()
        return None, 204

    def delete(self, user_trace_id):  # delete a post by its ID
        connection.UserTraces.find_and_modify(
            {"_id": ObjectId(user_trace_id)}, remove=True)
        # TODO: delete related data
        return None, 204
