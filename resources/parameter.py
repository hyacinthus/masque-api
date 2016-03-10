from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    return obj


class ParametersList(Resource):
    def get(self):  # get all posts
        cursor = connection.Parameters.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Parameters()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Parameters(Resource):
    def get(self, parameter_id):  # get a post by its ID
        cursor = connection.Parameters.find({"_id": ObjectId(parameter_id)})
        return check_content(cursor)

    def put(self, parameter_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Parameters()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = parameter_id
        doc.save()
        return None, 204

    def delete(self, parameter_id):  # delete a post by its ID
        connection.Parameters.find_and_modify(
            {"_id": ObjectId(parameter_id)}, remove=True)
        # TODO: delete related data
        return None, 204
