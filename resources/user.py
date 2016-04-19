import logging

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from config import MongoConfig, APIConfig
from model import connection, TokenResource, CheckPermission
from paginate import Paginate
from util import add_exp

log = logging.getLogger("masque.user")


class UsersList(Resource):
    def get(self):  # get all posts
        cursor = connection.Users.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Users()
        for item in resp:
            if item == "_id":
                continue
            doc[item] = resp[item]
        doc.save()
        return {"_id": doc['_id']}, 201


class DeviceUser(Resource):
    def get(self, device_id):
        cursor = connection.Devices.find_one({"_id": device_id})
        if not cursor:
            # 没有查到 device_id 对应信息, 视为新用户, 为其初始化devices/users信息
            user = connection.Users()
            user.save()
            user_id = user['_id']
            dev = connection.Devices()
            dev['_id'] = device_id
            dev['user_id'] = user_id
            dev['origin_user_id'] = user_id
            dev.save()
            result = connection.Users.find_one({"_id": ObjectId(user_id)})
        else:
            # 查到 device_id 对应信息, 返回对应用户信息并刷新用户登录时间
            result = connection.Users.find_one(
                {"_id": ObjectId(cursor['user_id'])}
            )
            if CheckPermission(result._id).is_first_login:
                # 当天初次登录随机加 1-5 经验
                add_exp(result)
            result._updated = None
            result.save()
        return result


class User(TokenResource):
    def get(self, user_id):  # get user info by its ID
        return self.user_info.user

    def put(self, user_id):  # update user info by its ID
        # 处理客户端请求数据
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        # 更新数据库
        cursor = connection.Users.find_one(
            {"_id": ObjectId(self.user_info.user._id)}
        )
        for item in resp:
            if item in ('_created', '_id', '_updated'):
                continue
            cursor[item] = resp[item]
        cursor._updated = None  # 更新登录时间记录
        cursor.save()
        return "", 204

    def delete(self, user_id):  # delete a post by its ID
        connection.Users.find_and_modify(
            {"_id": ObjectId(self.user_info.user._id)}, remove=True)
        # TODO: delete related data
        return "", 204


class UserPostsList(Resource):
    def get(self, user_id):
        """get user's posts"""
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')

        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
        result = []
        cursor = connection.UserPosts.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB]["posts_" + doc['theme_id']]
            cur = collection.Posts.find_one({"_id": ObjectId(doc["post_id"])})
            if cur:
                cur["theme_id"] = doc["theme_id"]
                result.append(cur)
        sorted_list = sorted(result, key=lambda k: k["_updated"], reverse=True)
        return Paginate(sorted_list, page, limit).data


class UserCommentsList(Resource):
    def get(self, user_id):
        """get user's comments"""
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')

        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
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
        sorted_list = sorted(result, key=lambda k: k["_created"], reverse=True)
        return Paginate(sorted_list, page, limit).data


class UserStarsList(Resource):
    def get(self, user_id):
        """get user's favor posts"""
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')

        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
        result = []
        cursor = connection.UserStars.find({"user_id": user_id})
        for doc in cursor:
            collection = connection[MongoConfig.DB]["posts_" + doc['theme_id']]
            cur = collection.Posts.find_one({"_id": ObjectId(doc["post_id"])})
            if cur:
                cur["theme_id"] = doc["theme_id"]
                result.append(cur)
        sorted_list = sorted(result, key=lambda k: k["_updated"], reverse=True)
        return Paginate(sorted_list, page, limit).data
