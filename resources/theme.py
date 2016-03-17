from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class ThemesList(Resource):
    def get(self):  # get all theme
        cursor = connection.Themes.find()
        return cursor

    def post(self):  # add a new theme
        resp = request.get_json(force=True)
        doc = connection.Themes()
        for item in resp:
            if item == "_id":
                continue  # skip if theme have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Theme(Resource):
    def get(self, theme_id):  # get a theme by its ID
        cursor = connection.Themes.find_one({"_id": ObjectId(theme_id)})
        return cursor

    def put(self, theme_id):  # update a theme by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        connection.Themes.find_and_modify(
            {"_id": ObjectId(theme_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, theme_id):  # delete a theme by its ID
        connection.Themes.find_and_modify(
            {"_id": ObjectId(theme_id)}, remove=True)
        # TODO: delete related data
        return None, 204
