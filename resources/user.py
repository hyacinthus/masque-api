from bson.objectid import ObjectId
from flask_restful import Resource, abort, request

from config import MongoConfig
from model import connection


def check_content(obj):
    """if no content found return 404, else return cursor."""
    if obj.count() == 0:
        abort(404)
    elif obj.count() == 1:
        return obj[0]  # return a dict if obj has only one item
    return obj  # or return a list


class UsersList(Resource):
    def get(self):  # get all posts
        cursor = connection.Users.find()
        return check_content(cursor)

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Users()
        for item in resp:
            doc[item] = resp[item]
        doc['_id'] = str(ObjectId())
        doc.save()
        extra = connection.ExtraUserFields()
        extra['_id'] = doc['_id']
        extra.save()  # create an extra document with the same user _id
        return {"_id": doc['_id']}, 201


class Users(Resource):
    def get(self, user_id):  # get a post by its ID
        cursor = connection.Users.find({"_id": ObjectId(user_id)})
        return check_content(cursor)

    def put(self, user_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Users()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = user_id
        doc.save()
        return None, 204

    def delete(self, user_id):  # delete a post by its ID
        connection.Users.find_and_modify(
            {"_id": ObjectId(user_id)}, remove=True)
        # TODO: delete related data 
        return None, 204


class UsersPostsList(Resource):
    def get(self, user_id):
        """get a user's posts
        add theme_id to each post
        """
        cursor = connection.ExtraUserFields.find({"_id": ObjectId(user_id)})
        result = []
        for theme_id in cursor[0]["posts"]:
            collection = connection[MongoConfig.DB]["posts_" + theme_id]
            cur = collection.Posts.find({"author": user_id})
            for item in cur:
                item["theme_id"] = theme_id
                result.append(item)
        return sorted(result, key=lambda k: k["_updated"], reverse=True)


class UsersCommentsList(Resource):
    def get(self, user_id):
        pass
