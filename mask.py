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


class MaskList(Resource):
    def get(self):  # get all posts
        cursor = connection.Mask.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Mask()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return 201


class Mask(Resource):
    def get(self, mask_id):  # get a post by its ID
        cursor = connection.Mask.find({"_id": ObjectId(mask_id)})
        return check_content(cursor)

    def put(self, mask_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Mask()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = mask_id
        doc.save()
        return 204

    def delete(self, mask_id):  # delete a post by its ID
        connection.Mask.find_and_modify(
            {"_id": ObjectId(mask_id)}, remove=True)
        # TODO: delete related data 
        return 204
