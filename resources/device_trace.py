from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class DeviceTraceList(Resource):
    def get(self):  # get all posts
        cursor = connection.DeviceTrace.find()
        return cursor

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
        cursor = connection.DeviceTrace.find_one(
            {"_id": ObjectId(device_trace_id)})
        return cursor

    def put(self, device_trace_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        connection.DeviceTrace.find_and_modify(
            {"_id": ObjectId(device_trace_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, device_trace_id):  # delete a post by its ID
        connection.DeviceTrace.find_and_modify(
            {"_id": ObjectId(device_trace_id)}, remove=True)
        # TODO: delete related data 
        return None, 204
