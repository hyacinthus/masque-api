from bson.objectid import ObjectId
from flask_restful import Resource, request

from config import MongoConfig
from model import connection


class UsersList(Resource):
    def get(self):  # get all posts
        cursor = connection.Users.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Users()
        for item in resp:
            doc[item] = resp[item]
        doc['_id'] = str(ObjectId())
        doc.save()
        return {"_id": doc['_id']}, 201


class User(Resource):
    def get(self, user_id):  # get a post by its ID
        cursor = connection.Users.find({"_id": ObjectId(user_id)})
        if cursor.count() == 0:
            return None, 404
        return list(cursor)[0]  # 单个查询只返回字典

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


class UserPostsList(Resource):
    def get(self, user_id):
        """get user's posts"""
        result = []
        cursor = connection.UserPosts.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB]["posts_" + doc['theme_id']]
            cur = collection.Posts.find({"author": user_id})
            new_cur = []
            for item in cur:  # add an extra "theme_id" item
                item['theme_id'] = doc['theme_id']
                new_cur.append(item)
            result += list(new_cur)
        return sorted(result, key=lambda k: k["_updated"], reverse=True)


class UserCommentsList(Resource):
    def get(self, user_id):
        """get user's comments"""
        result = []
        cursor = connection.UserComments.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB][
                "comments_" + doc['theme_id']]
            cur = collection.Comments.find({"author": user_id})
            new_cur = []
            for item in cur:  # add an extra "theme_id" item
                item['theme_id'] = doc['theme_id']
                new_cur.append(item)
            result += list(new_cur)
        return sorted(result, key=lambda k: k["_created"], reverse=True)


class UserStarsList(Resource):
    def get(self, user_id):
        """get user's favor posts"""
        result = []
        cursor = connection.UserStars.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB]["posts_" + doc['theme_id']]
            cur = collection.Posts.find({"_id": ObjectId(doc['post_id'])})
            new_cur = []
            for item in cur:  # add an extra "theme_id" item
                item['theme_id'] = doc['theme_id']
                new_cur.append(item)
            result += list(new_cur)
        return sorted(result, key=lambda k: k["_updated"], reverse=True)
