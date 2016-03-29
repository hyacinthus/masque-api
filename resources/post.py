from datetime import datetime

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse
from marshmallow import Schema, fields, ValidationError

from config import MongoConfig, APIConfig
from model import connection, redisdb


# Custom validator
def must_not_be_blank(data):
    if not data:
        raise ValidationError('Data not provided.')
    if not ObjectId(data):
        raise ValidationError('Data is not a valid ObjectId')


class HeartSchema(Schema):
    mask_id = fields.Str(required=True, validate=must_not_be_blank)
    user_id = fields.Str(required=True, validate=must_not_be_blank)


class FavorSchema(Schema):
    user_id = fields.Str(required=True, validate=must_not_be_blank)


class PostsList(Resource):
    def get(self, theme_id):  # get all posts
        parser = reqparse.RequestParser()
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')
        args = parser.parse_args()
        if args['page'] is None:
            args['page'] = 1
        index = args['page'] - 1
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find(
            skip=(index * APIConfig.PAGESIZE),
            limit=APIConfig.PAGESIZE,
            max_scan=APIConfig.MAX_SCAN,
            sort=[("_updated", -1)])  # sorted by update time in reversed order
        return cursor

    def post(self, theme_id):  # add a new post
        utctime = datetime.timestamp(datetime.utcnow())
        resp = request.get_json(force=True)
        # save a post
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        doc = collection.Posts()
        for item in resp:
            doc[item] = resp[item]
        doc['_created'] = utctime
        doc['_updated'] = utctime
        doc.save()
        # save a record
        user_posts = connection.UserPosts()
        user_posts['user_id'] = doc['author']
        user_posts['theme_id'] = theme_id
        user_posts['post_id'] = doc['_id']
        user_posts['_created'] = utctime
        user_posts.save()
        return {"_id": doc['_id']}, 201  # return post_id generated by system


class Post(Resource):
    def get(self, theme_id, post_id):  # get a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
        return cursor

    def put(self, theme_id, post_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, theme_id, post_id):  # delete a post by its ID
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)}, remove=True)
        # delete related comments
        collection.Comments.find_and_modify(
            {"post_id": ObjectId(post_id)}, remove=True)
        return None, 204


class FavorPost(Resource):
    def post(self, theme_id, post_id):
        resp = request.get_json(force=True)
        # 输入验证
        if not resp:
            return {'message': 'No input data provided!'}, 400
        data, errors = FavorSchema().load(resp)
        if errors:
            return errors, 422
        cursor = connection.UserStars.find_one(
            {
                "post_id": post_id,
                "user_id": data['user_id'],
                "theme_id": theme_id
            }
        )
        # 检测帖子是否已被收藏
        if cursor is None:  # do nothing if repeatedly submits happened
            connection.UserStars.find_and_modify(
                {
                    "post_id": post_id,
                    "user_id": data['user_id'],
                    "theme_id": theme_id
                },
                {
                    "post_id": post_id,
                    "user_id": data['user_id'],
                    "theme_id": theme_id
                },
                upsert=True
            )
            return None, 201
        else:
            return {'message': 'Record Exists!'}, 200

    def delete(self, theme_id, post_id):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id',
                            type=str,
                            required=True,
                            help='user_id not found')
        args = parser.parse_args()
        connection.UserStars.find_and_modify(
            {
                "post_id": post_id,
                "user_id": args['user_id'],
                "theme_id": theme_id
            },
            remove=True
        )
        return None, 204


class Hearts(Resource):
    def post(self, theme_id, post_id):
        resp = request.get_json(force=True)
        # 输入验证
        if not resp:
            return {'message': 'No input data provided!'}, 400
        data, errors = HeartSchema().load(resp)
        if errors:
            return errors, 422
        collection = connection[MongoConfig.DB]["posts_" + theme_id]
        cursor = collection.Posts.find_one({"_id": ObjectId(post_id)})
        # 发帖人不能自己评论自己
        if cursor['author'] == data['user_id']:
            return None, 204
        # 查找用户是否已经感谢过这个帖子
        for item in cursor['hearts']:
            if item['user_id'] == data['user_id']:
                return None, 204
        # 更新 hearts 列表
        collection.Posts.find_and_modify(
            {"_id": ObjectId(post_id)},
            {
                "$addToSet": {
                    "hearts": data
                }
            }
        )
        # 给帖子作者 hearts_received 加一
        connection.Users.find_and_modify(
            {"_id": ObjectId(cursor['author'])},
            {
                "$inc": {
                    "hearts_received": 1
                }
            }
        )
        return None, 201


class Feedback(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            'authorization',
            type=str,
            location='headers'
        )
        args = parser.parse_args()
        token = args["authorization"]
        access_token = token[token.find(" ") + 1:]
        if redisdb.exists(
                "oauth:access_token:{}:client_id".format(access_token)
        ):
            device_id = redisdb.get(
                "oauth:access_token:{}:client_id".format(access_token)
            )
        else:
            return {
                       'status': "error",
                       'message': 'Device not found'
                   }, 404
        resp = request.get_json(force=True)
        cursor = connection.Devices.find_one({"_id": device_id})
        doc = connection.Feedback()
        for item in resp:
            doc[item] = resp[item]
        doc.author = cursor.user_id
        doc.save()
        return None, 201
