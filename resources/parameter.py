from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class ParametersList(Resource):
    def get(self):  # get all posts
        cursor = connection.Parameters.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Parameters()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Parameter(Resource):
    def get(self, parameter_id):  # get a post by its ID
        cursor = connection.Parameters.find_one({"_id": ObjectId(parameter_id)})
        return cursor

    def put(self, parameter_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        connection.Parameters.find_and_modify(
            {"_id": ObjectId(parameter_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, parameter_id):  # delete a post by its ID
        connection.Parameters.find_and_modify(
            {"_id": ObjectId(parameter_id)}, remove=True)
        # TODO: delete related data
        return None, 204
