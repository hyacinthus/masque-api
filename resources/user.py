import logging
from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from config import MongoConfig, APIConfig
from model import connection, UserInfo

log = logging.getLogger("masque.user")


def paging_list(sorted_list, page, limit):
    """列表分页"""
    if len(sorted_list) % limit != 0:
        num_pages = len(sorted_list) // limit + 1
    else:
        num_pages = len(sorted_list) // limit
    # 判断页码是否超出范围
    if page <= num_pages:
        return {
            "data": sorted_list[limit * (page - 1):limit * page],
            "paging": {
                "num_pages": num_pages,
                "current_page": page
            }
        }
    else:
        return {
                   "message": "page number out of range"
               }, 400


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
        # 根据token取得当前用户/设备_id
        parser = reqparse.RequestParser()
        parser.add_argument(
            'authorization',
            type=str,
            location='headers'
        )
        args = parser.parse_args()
        token = args["authorization"]
        user = UserInfo(token)
        # 处理客户端请求数据
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        # 更新数据库
        cursor = connection.Users.find_one({"_id": ObjectId(user.user._id)})
        for item in resp:
            if item in ('_created', '_id', '_updated'):
                continue
            cursor[item] = resp[item]
        cursor._updated = None  # 更新登录时间记录
        cursor.save()
        return "", 204

    def delete(self, user_id):  # delete a post by its ID
        connection.Users.find_and_modify(
            {"_id": ObjectId(user_id)}, remove=True)
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
        return paging_list(sorted_list, page, limit)


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
        return paging_list(sorted_list, page, limit)


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
        return paging_list(sorted_list, page, limit)
