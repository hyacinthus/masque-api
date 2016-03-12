from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class MessagesList(Resource):
    def get(self):  # get all posts
        cursor = connection.Messages.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Messages()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Message(Resource):
    def get(self, message_id):  # get a post by its ID
        cursor = connection.Messages.find({"_id": ObjectId(message_id)})
        if cursor.count() == 0:
            return None, 404
        return list(cursor)[0]  # 单个查询只返回字典

    def put(self, message_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Messages()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = message_id
        doc.save()
        return None, 204

    def delete(self, message_id):  # delete a post by its ID
        connection.Messages.find_and_modify(
            {"_id": ObjectId(message_id)}, remove=True)
        # TODO: delete related data
        return None, 204
