from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class DevicesList(Resource):
    def get(self):  # get all posts
        cursor = connection.Devices.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Devices()
        for item in resp:
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Device(Resource):
    def get(self, device_id):  # get a post by its ID
        cursor = connection.Devices.find_one({"_id": device_id})
        return cursor

    def put(self, device_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        connection.Devices.find_and_modify(
            {"_id": ObjectId(device_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, device_id):  # delete a post by its ID
        connection.Devices.find_and_modify(
            {"_id": ObjectId(device_id)}, remove=True)
        # TODO: delete related data 
        return None, 204
