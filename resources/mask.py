import logging
import uuid

from bson.objectid import ObjectId
from flask_restful import request, reqparse

from config import MongoConfig, CollectionName
from model import connection, TokenResource

log = logging.getLogger("masque.mask")


class MasksList(TokenResource):
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


class Mask(TokenResource):
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


class RandomMask(TokenResource):
    """随机取一个 mask_id 放在原列表第一位, 删掉原列表最末位"""

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('size',
                            type=int,
                            help='可不填, 默认返回一个头像id')
        args = parser.parse_args()
        mask_size = args['size'] if args['size'] else 1
        sample = connection[MongoConfig.DB][CollectionName.MASKS].aggregate(
            [{"$sample": {"size": mask_size}}]
        )
        return {
            "status": "ok",
            "message": "成功生成随机头像列表",
            "data": {
                "masks": [str(i['_id']) for i in sample['result']]
            }
        }


class UploadMask(TokenResource):
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
        current_user_id = self.user_info.user._id
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
        return '', 201
