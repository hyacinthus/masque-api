from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class UserTracesList(Resource):
    def get(self):
        cursor = connection.UserTraces.find()
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def post(self):
        resp = request.get_json(force=True)
        doc = connection.UserTraces()
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


class UserTrace(Resource):
    def get(self, user_trace_id):  # get a post by its ID
        cursor = connection.UserTraces.find_one(
            {"_id": ObjectId(user_trace_id)})
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, user_trace_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.UserTraces.find_and_modify(
            {"_id": ObjectId(user_trace_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, user_trace_id):  # delete a post by its ID
        connection.UserTraces.find_and_modify(
            {"_id": ObjectId(user_trace_id)}, remove=True)
        # TODO: delete related data
        return '', 204
