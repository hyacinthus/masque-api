import logging

from bson.objectid import ObjectId
from flask_restful import reqparse

from config import APIConfig
from model import connection, TokenResource, redisdb
from paginate import Paginate

log = logging.getLogger("masque.resources.notification")


class Notifications(TokenResource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type',
                            type=str,
                            help='all/new 选其一, 默认为new')
        parser.add_argument('page',
                            type=int,
                            help='page number must be int')
        parser.add_argument('count',
                            type=int,
                            help='count must be int')
        args = parser.parse_args()
        notifi_type = args['type'] if args['type'] else "new"
        page = 1 if not args['page'] else args['page']
        if not args['count']:
            limit = APIConfig.PAGESIZE
        else:
            limit = args['count']
        if notifi_type == "all":
            # 返回全部通知
            cursor = connection.Notifications.find(
                {"user_id": self.user_info.user._id},
                max_scan=APIConfig.MAX_SCAN,
                sort=[("_created", -1)]
            )
            if cursor.count() == 0:
                return {
                           'status': 'error',
                           'message': '暂时没有新的通知消息哦'
                       }, 404
        else:
            # 仅返回新通知(如果有的话)
            key = "user:{}:notifications".format(self.user_info.user._id)
            if not redisdb.exists(key):
                return {
                           'status': 'error',
                           'message': '暂时没有新的通知消息哦'
                       }, 404
            keys = redisdb.lrange(key, 0, -1)
            for i in keys:
                if not redisdb.exists("notification:{}".format(i)):
                    # 删除过期的key
                    redisdb.lrem(key, 0, i)
            keys = redisdb.lrange(key, 0, -1)
            if len(keys) == 0:
                return {
                           'status': 'error',
                           'message': '暂时没有新的通知消息哦'
                       }, 404
            cursor = [redisdb.hgetall("notification:{}".format(i)) for i in keys
                      if redisdb.exists("notification:{}".format(i))]
        paged_cursor = Paginate(cursor, page, limit)
        return paged_cursor.data

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('type',
                            type=str,
                            help='all/new 选其一, 默认为new')
        args = parser.parse_args()
        notifi_type = args['type'] if args['type'] else "new"
        if notifi_type == "all":
            connection.Notifications.collection.remove(
                {"user_id": self.user_info.user._id}
            )
        else:
            key = "user:{}:notifications".format(self.user_info.user._id)
            if redisdb.exists(key):
                for i in redisdb.lrange(key, 0, -1):
                    if redisdb.exists("notification:{}".format(i)):
                        redisdb.delete("notification:{}".format(i))
                redisdb.delete(key)
        return '', 204


class Notification(TokenResource):
    def delete(self, notifi_id):
        parser = reqparse.RequestParser()
        parser.add_argument('type',
                            type=str,
                            help='all/new 选其一, 默认为new')
        args = parser.parse_args()
        notifi_type = args['type'] if args['type'] else "new"
        if notifi_type == "all":
            connection.Notifications.collection.remove(
                {"_id": ObjectId(notifi_id)}
            )
        else:
            key = "user:{}:notifications".format(self.user_info.user._id)
            if redisdb.exists(key) and notifi_id in redisdb.lrange(key, 0, -1):
                redisdb.lrem(key, 0, notifi_id)
            if redisdb.exists("notification:{}".format(notifi_id)):
                redisdb.delete("notification:{}".format(notifi_id))
        return '', 204
