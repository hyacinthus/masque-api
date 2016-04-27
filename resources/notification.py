import logging

from bson.objectid import ObjectId
from flask_restful import request, reqparse

from config import APIConfig
from model import connection, TokenResource, redisdb
from paginate import Paginate

log = logging.getLogger("masque.resources.notification")


class Notifications(TokenResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type',
                            type=str,
                            required=True,
                            help='类型不能为空, all/new 选其一')
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')
        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        notifi_type = args['type'] if args['type'] in ('new', 'all') else "new"
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
        if notifi_type == "all":
            cursor = connection.Notifications.find(
                {"user_id": ObjectId(self.user_info.user._id)},
                max_scan=APIConfig.MAX_SCAN,
                sort=[("_created", -1)]
            )
        else:
            keys = redisdb.keys(
                "notification:*:user:{}".format(self.user_info.user._id)
            )
            log.debug("{}".format(keys))
            log.debug("user:{}".format(self.user_info.user))
            cursor = [redisdb.hgetall(i) for i in keys]
        paged_cursor = Paginate(cursor, page, limit)
        return paged_cursor.data


class Notification(TokenResource):
    def get(self, device_id):  # get a post by its ID
        cursor = connection.Devices.find_one({"_id": device_id})
        return cursor

    def put(self, device_id):  # update a post by its ID
        resp = request.get_json(force=True)
        if not resp:
            return {'message': 'No input data provided!'}, 400
        elif ("_id" or "_created") in resp:
            resp = {i: resp[i] for i in resp if i not in ("_id", "_created")}
        connection.Devices.find_and_modify(
            {"_id": ObjectId(device_id)},
            {
                "$set": resp
            }
        )
        return '', 204

    def delete(self, device_id):  # delete a post by its ID
        connection.Devices.find_and_modify(
            {"_id": ObjectId(device_id)}, remove=True)
        # TODO: delete related data
        return '', 204
