from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class MessagesList(Resource):
    def get(self):
        cursor = connection.Messages.find()
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def post(self):
        resp = request.get_json(force=True)
        doc = connection.Messages()
        for item in resp:
            if item == "_id":
                continue
            doc[item] = resp[item]
        doc.save()
        return {
                   "status": "ok",
                   "message": "",
                   "data": doc
               }, 201


class Message(Resource):
    def get(self, message_id):  # get a post by its ID
        cursor = connection.Messages.find_one({"_id": ObjectId(message_id)})
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, message_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.Messages.find_and_modify(
            {"_id": ObjectId(message_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, message_id):  # delete a post by its ID
        connection.Messages.find_and_modify(
            {"_id": ObjectId(message_id)}, remove=True)
        # TODO: delete related data
        return '', 204
