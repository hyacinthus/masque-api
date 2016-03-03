from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class DeviceList(Resource):
    def get(self):  # get all posts
        cursor = connection.Device.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Device()
        for item in resp:
            doc[item] = resp[item]
        doc.save()
        return 201


class Device(Resource):
    def get(self, device_id):  # get a post by its ID
        cursor = connection.Device.find({"_id": device_id})
        return check_content(cursor)

    def put(self, device_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Device()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = device_id
        doc.save()
        return 204

    def delete(self, device_id):  # delete a post by its ID
        connection.Device.find_and_modify(
            {"_id": ObjectId(device_id)}, remove=True)
        # TODO: delete related data 
        return 204
