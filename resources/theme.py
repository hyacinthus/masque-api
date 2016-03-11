from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class ThemesList(Resource):
    def get(self):  # get all posts
        cursor = connection.Themes.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Themes()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Theme(Resource):
    def get(self, theme_id):  # get a post by its ID
        cursor = connection.Themes.find({"_id": ObjectId(theme_id)})
        return cursor

    def put(self, theme_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.Themes()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = theme_id
        doc.save()
        return None, 204

    def delete(self, theme_id):  # delete a post by its ID
        connection.Themes.find_and_modify(
            {"_id": ObjectId(theme_id)}, remove=True)
        # TODO: delete related data
        return None, 204
