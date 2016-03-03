from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from config import MongoConfig, CollectionName
from model import connection

collection = connection[MongoConfig.DB][CollectionName.USERS]


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class UserList(Resource):
    def get(self):  # get all posts
        cursor = collection.User.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = collection.User()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = str(ObjectId())
        doc.save()
        return doc, 201


class User(Resource):
    def get(self, user_id):  # get a post by its ID
        cursor = collection.User.find({"_id": ObjectId(user_id)})
        return check_content(cursor)

    def put(self, user_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = collection.User()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_id
        doc.save()
        return 204

    def delete(self, user_id):  # delete a post by its ID
        collection.User.find_and_modify(
            {"_id": ObjectId(user_id)}, remove=True)
        # TODO: delete related data 
        return 204
