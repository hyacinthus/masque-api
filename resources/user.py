from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

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
        parser = reqparse.RequestParser()
        parser.add_argument('device_id',
                            type=str,
                            help='page number must be a string')
        args = parser.parse_args()
        if args['device_id'] is None:
            # 如果没有传参数, 则视为存在此用户, 返回 user_id 对应用户信息
            result = connection.Users.find_one({"_id": ObjectId(user_id)})
        else:
            device_id = args['device_id']
            # 有参数传入, 先在设备表里查询有无 device_id 对应信息
            cursor = connection.Devices.find_one({"_id": device_id})
            if cursor is None:
                # 没有查到 device_id 对应信息, 视为新用户, 为其初始化devices/users信息
                dev = connection.Devices()
                user_id = str(ObjectId())
                dev['_id'] = device_id
                dev['user_id'] = user_id
                dev['origin_user_id'] = user_id
                dev.save()
                user = connection.Users()
                user['_id'] = user_id
                user.save()
                result = connection.Users.find_one({"_id": ObjectId(user_id)})
            else:
                # 查到 device_id 对应信息, 返回对应用户信息
                result = connection.Users.find_one(
                    {"_id": ObjectId(cursor['user_id'])})
        return result

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
