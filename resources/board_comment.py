from bson.objectid import ObjectId
from flask_restful import Resource, request

from model import connection


class BoardCommentsList(Resource):
    def get(self):  # get all posts
        cursor = connection.BoardComments.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.BoardComments()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class BoardComment(Resource):
    def get(self, board_comment_id):  # get a post by its ID
        cursor = connection.BoardComments.find(
            {"_id": ObjectId(board_comment_id)})
        if cursor.count() == 0:
            return None, 404
        return list(cursor)[0]  # 单个查询只返回字典

    def put(self, board_comment_id):  # update a post by its ID
        resp = request.get_json(force=True)
        doc = connection.BoardComments()
        for item in resp:
            doc[item] = resp[item]
        doc["_id"] = board_comment_id
        doc.save()
        return None, 204

    def delete(self, board_comment_id):  # delete a post by its ID
        connection.BoardComments.find_and_modify(
            {"_id": ObjectId(board_comment_id)}, remove=True)
        # TODO: delete related data 
        return None, 204
