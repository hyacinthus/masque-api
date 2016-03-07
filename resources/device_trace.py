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


class DeviceTraceList(Resource):
    def get(self):  # get all posts
        cursor = connection.DeviceTrace.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.DeviceTrace()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class DeviceTrace(Resource):
    def get(self, device_trace_id):  # get a post by its ID
        cursor = connection.DeviceTrace.find({"_id": ObjectId(device_trace_id)})
        return check_content(cursor)

    def put(self, device_trace_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.DeviceTrace()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = device_trace_id
        doc.save()
        return None, 204

    def delete(self, device_trace_id):  # delete a post by its ID
        connection.DeviceTrace.find_and_modify(
            {"_id": ObjectId(device_trace_id)}, remove=True)
        # TODO: delete related data 
        return None, 204
