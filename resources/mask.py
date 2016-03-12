from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class MasksList(Resource):
    def get(self):  # get all posts
        cursor = connection.Masks.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Masks()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Mask(Resource):
    def get(self, mask_id):  # get a post by its ID
        cursor = connection.Masks.find({"_id": ObjectId(mask_id)})
        if cursor.count() == 0:
            return None, 404
        return list(cursor)[0]  # 单个查询只返回字典

    def put(self, mask_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Masks()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = mask_id
        doc.save()
        return None, 204

    def delete(self, mask_id):  # delete a post by its ID
        connection.Masks.find_and_modify(
            {"_id": ObjectId(mask_id)}, remove=True)
        # TODO: delete related data 
        return None, 204
