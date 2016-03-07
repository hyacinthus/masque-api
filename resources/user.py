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


class UserList(Resource):
    def get(self):  # get all posts
        cursor = connection.User.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.User()
        for item in resp:
            doc[item] = resp[item]
        doc['_id'] = str(ObjectId())
        doc.save()
        extra = connection.ExtraUserField()
        extra['_id'] = doc['_id']
        extra.save()  # create an extra document with the same user _id
        return {"_id": doc['_id']}, 201


class User(Resource):
    def get(self, user_id):  # get a post by its ID
        cursor = connection.User.find({"_id": ObjectId(user_id)})
        return check_content(cursor)

    def put(self, user_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.User()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_id
        doc.save()
        return None, 204

    def delete(self, user_id):  # delete a post by its ID
        connection.User.find_and_modify(
            {"_id": ObjectId(user_id)}, remove=True)
        # TODO: delete related data 
        return None, 204