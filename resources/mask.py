import logging
import uuid

from bson.objectid import ObjectId
from flask_restful import request, reqparse

from config import MongoConfig, CollectionName
from model import connection, TokenResource
from tasks import notification

log = logging.getLogger("masque.mask")


class MasksList(TokenResource):
    def get(self):
        cursor = connection.Masks.find()
        return cursor

    def post(self):
        resp = request.get_json(force=True)
        doc = connection.Masks()
        for item in resp:
            if item == "_id":
                continue
            doc[item] = resp[item]
        doc.save()
        return {
                   "status": "ok",
                   "message": "",
                   "data": doc
               }, 201


class Mask(TokenResource):
    def get(self, mask_id):
        cursor = connection.Masks.find_one({"_id": ObjectId(mask_id)})
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def put(self, mask_id):
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        cursor = connection.Masks.find_and_modify(
            {"_id": ObjectId(mask_id)},
            {
                "$set": resp
            }
        )
        return {
            "status": "ok",
            "message": "",
            "data": cursor
        }

    def delete(self, mask_id):
        connection.Masks.find_and_modify(
            {"_id": ObjectId(mask_id)}, remove=True)
        # TODO: delete related data 
        return '', 204


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
            [{"$match": {"category": "system"}}, {"$sample": {"size": mask_size}}]
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
        except ValueError:
            return {
                       'status': 'error',
                       'message': '%s is not a valid uuid.hex string'
                                  % resp["uuid"]
                   }, 400
        mask_uuid = resp["uuid"]
        current_user_id = self.user_info.user._id
        notification.check_image('mask', mask_uuid, current_user_id)
        # 将新传入的头像uuid加入masks
        mask = connection.Masks()
        mask._id = mask_uuid
        mask.category = "user"
        mask.save()
        return {
                   "status": "ok",
                   "message": "头像上传成功",
                   "data": mask
               }, 201
