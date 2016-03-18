import logging
from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import Resource, request

from config import MongoConfig
from model import connection

log = logging.getLogger("masque.user")


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


class DeviceUser(Resource):
    def get(self, device_id):
        cursor = connection.Devices.find_one({"_id": device_id})
        if not cursor:
            # 没有查到 device_id 对应信息, 视为新用户, 为其初始化devices/users信息
            user_id = str(ObjectId())
            dev = connection.Devices()
            dev['_id'] = device_id
            dev['user_id'] = user_id
            dev['origin_user_id'] = user_id
            dev.save()
            user = connection.Users()
            user['_id'] = user_id
            user.save()
            result = connection.Users.find_one({"_id": ObjectId(user_id)})
        else:
            # 查到 device_id 对应信息, 返回对应用户信息并刷新用户登录时间
            result = connection.Users.find_and_modify(
                {"_id": ObjectId(cursor['user_id'])},
                {
                    "$set": {
                        "_updated": datetime.utcnow()
                    }
                }
            )
        return result


class User(Resource):
    def get(self, user_id):  # get user info by its ID
        # 返回用户信息同时刷新登录时间记录
        cursor = connection.Users.find_and_modify(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "_updated": datetime.utcnow()
                }
            }
        )
        return cursor

    def put(self, user_id):  # update user info by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        # 更新登录时间记录
        resp["_updated"] = datetime.utcnow()
        connection.Users.find_and_modify(
            {"_id": ObjectId(user_id)},
            {
                "$set": resp
            }
        )
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
            cur = collection.Posts.find_one({"_id": ObjectId(doc["post_id"])})
            if cur:
                cur["theme_id"] = doc["theme_id"]
                result.append(cur)
        return sorted(result, key=lambda k: k["_updated"], reverse=True)


class UserCommentsList(Resource):
    def get(self, user_id):
        """get user's comments"""
        result = []
        cursor = connection.UserComments.find({"user_id": user_id})
        if cursor.count() == 0:
            return {'message': 'Not found'}, 404
        for doc in cursor:
            collection = connection[MongoConfig.DB][
                "comments_" + doc['theme_id']]
            cur = collection.Comments.find_one(
                {"_id": ObjectId(doc["comment_id"])})
            if cur:
                cur["theme_id"] = doc["theme_id"]
                result.append(cur)
        return sorted(result, key=lambda k: k["_created"], reverse=True)


class UserStarsList(Resource):
    def get(self, user_id):
        """get user's favor posts"""
        result = []
        cursor = connection.UserStars.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB]["posts_" + doc['theme_id']]
            cur = collection.Posts.find_one({"_id": ObjectId(doc["post_id"])})
            if cur:
                cur["theme_id"] = doc["theme_id"]
                result.append(cur)
        return sorted(result, key=lambda k: k["_updated"], reverse=True)
