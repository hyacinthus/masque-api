from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from model import connection


class ThemesList(Resource):
    def get(self):  # get all theme
        cursor = connection.Themes.find()
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def post(self):  # add a new theme
        resp = request.get_json(force=True)
        doc = connection.Themes()
        for item in resp:
            if item == "_id":
                continue  # skip if theme have an _id item
            doc[item] = resp[item]
        doc.save()
        return {
                   "status": "ok",
                   "message": "",
                   "data": doc
               }, 201


class Theme(Resource):
    def get(self, theme_id):  # get a theme by its ID or full_name
        parser = reqparse.RequestParser()
        parser.add_argument('category', type=str)
        args = parser.parse_args()
        if not args['category']:
            if ObjectId.is_valid(theme_id):
                cursor = connection.Themes.find_one({"_id": ObjectId(theme_id)})
            elif isinstance(theme_id, str):
                cursor = connection.Themes.find_one({"_id": theme_id})
            else:
                return {
                           'status': "error",
                           'message': '输入错误, 请确认数据类型是str或者ObjectId'
                       }, 400
        elif args['category'] in ("school", "district", "virtual",
                                  "private", "system"):
            cursor = connection.Themes.find_one(
                {
                    "full_name": theme_id,
                    "category": args['category']
                }
            )
        else:
            return {'message': 'A invalid category provided!'}, 400
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, theme_id):  # update a theme by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.Themes.find_and_modify(
            {"_id": ObjectId(theme_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, theme_id):  # delete a theme by its ID
        connection.Themes.find_and_modify(
            {"_id": ObjectId(theme_id)}, remove=True)
        # TODO: delete related data
        return '', 204
