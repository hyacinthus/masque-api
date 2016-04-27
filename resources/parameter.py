from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class ParametersList(Resource):
    def get(self):
        cursor = connection.Parameters.find()
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def post(self):
        resp = request.get_json(force=True)
        doc = connection.Parameters()
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


class Parameter(Resource):
    def get(self, parameter_id):
        cursor = connection.Parameters.find_one({"_id": ObjectId(parameter_id)})
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, parameter_id):
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.Parameters.find_and_modify(
            {"_id": ObjectId(parameter_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, parameter_id):
        connection.Parameters.find_and_modify(
            {"_id": ObjectId(parameter_id)}, remove=True)
        # TODO: delete related data
        return '', 204
