import logging
import uuid

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from model import connection, redisdb

log = logging.getLogger("masque.mask")


class MasksList(Resource):
    def get(self):  # get all posts
        cursor = connection.Masks.find()
        return cursor

    def post(self):  # add a new post
        resp = request.get_json(force=True)
        doc = connection.Masks()
        for item in resp:
            if item == "_id":
                continue  # skip if post have an _id item
            doc[item] = resp[item]
        doc.save()
        return None, 201


class Mask(Resource):
    def get(self, mask_id):  # get a post by its ID
        cursor = connection.Masks.find_one({"_id": ObjectId(mask_id)})
        return cursor

    def put(self, mask_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        connection.Masks.find_and_modify(
            {"_id": ObjectId(mask_id)},
            {
                "$set": resp
            }
        )
        return None, 204

    def delete(self, mask_id):  # delete a post by its ID
        connection.Masks.find_and_modify(
            {"_id": ObjectId(mask_id)}, remove=True)
        # TODO: delete related data 
        return None, 204


class RandomMask(Resource):
    """随机取一个 mask_id 放在原列表第一位, 删掉原列表最末位"""

    def find_random(self):
        """
        return one random document from the masks collection
        """
        import random
        # TODO: 现在数据库都是 "user" 类型, 等改回 "system" 后需要去掉 "user"
        count = connection.Masks.find(
            {
                "category": {
                    "$in": ["user", "system"]
                }
            }
        ).count()
        if max:
            num = random.randint(0, count - 1)
            return connection.Masks.find(
                {
                    "category": {
                        "$in": ["user", "system"]
                    }
                }
            ).skip(num).next()

    def get(self):
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
        # 根据device_id查找对应user_id
        cursor = connection.Devices.find_one({"_id": device_id})
        if cursor:
            current_user_id = cursor.user_id
        else:
            return {'message': 'user_id not found'}, 404
        user_info = connection.Users.find_one(
            {"_id": ObjectId(current_user_id)}
        )
        mask_list = user_info.masks
        first_item = self.find_random()._id
        # 随机一个原列表里没有的项
        while first_item in mask_list:
            first_item = self.find_random()._id
        # 拼装新头像列表
        new_mask_list = [first_item] + mask_list
        # 写入数据库
        connection.Users.find_and_modify(
            {"_id": ObjectId(current_user_id)},
            {
                "$set": {
                    "masks": new_mask_list[:-1]
                }
            }
        )
        return {
            "status": "ok",
            "message": "头像排序完毕",
            "data": {
                "masks": new_mask_list[:-1]
            }
        }


class UploadMask(Resource):
    def post(self):
        """
        将上传完成的头像uuid传入用户头像列表
        """
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        try:
            uuid.UUID(resp["uuid"])
        except:
            return {
                       'status': 'error',
                       'message': '%s is not a valid uuid.hex string'
                                  % resp["uuid"]
                   }, 400
        mask_uuid = resp["uuid"]
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
        # 根据device_id查找对应user_id
        cursor = connection.Devices.find_one({"_id": device_id})
        if cursor:
            current_user_id = cursor.user_id
        else:
            return {'message': 'user_id not found'}, 404
        user_info = connection.Users.find_one(
            {"_id": ObjectId(current_user_id)}
        )
        mask_list = user_info.masks
        new_mask_list = [mask_uuid] + mask_list
        # 将新传入的头像uuid加入用户头像列表
        connection.Users.find_and_modify(
            {"_id": ObjectId(current_user_id)},
            {
                "$set": {
                    "masks": new_mask_list[:-1]
                }
            }
        )
        # 将新传入的头像uuid加入masks
        mask = connection.Masks()
        mask._id = mask_uuid
        mask.save()
        return None, 201
