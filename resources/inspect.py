import logging

from json import dumps
from datetime import datetime
from bson.objectid import ObjectId
from flask_restful import reqparse, request

from config import MongoConfig
from model import connection, TokenResource
from tasks import logger, notification
from util import add_exp, lock_user

log = logging.getLogger("masque.inspect")


class Inspection(TokenResource):
    def post(self, report_id):
        parser = reqparse.RequestParser()
        parser.add_argument('category',
                            type=str,
                            help='post/comment 选其一, 默认为post')

        parser.add_argument('exp_reduce',
                            type=int,
                            help='exp_reduce must be int, 默认为5')
        parser.add_argument('ban_days',
                            type=int,
                            help='ban_days must be int, 默认为1')
        args = parser.parse_args()
        resp = request.get_json(force=True)
        for item in ['admin', 'reason']:
            if not resp.get(item):
                return {
                           'status': 'error',
                           'message': 'missing required field: %s' % item
                       }, 400

        admin = resp.get('admin')
        reason = resp.get('reason')

        if not args['category']:
            category = 'post'
        else:
            category = args['category']
        if not args['exp_reduce']:
            exp_reduce = 5
        else:
            exp_reduce = args['exp_reduce']
        if not args['ban_days']:
            ban_days = 1
        else:
            ban_days = args['ban_days']
        if category == 'post':
            cursor = connection.ReportPosts.find_one({'_id': ObjectId(report_id)})
            if not cursor:
                return {
                           'status': 'error',
                           'message': 'report_posts这个表中不存在ObjectId(%s)' % report_id
                       }, 404
            else:
                # 处理规则: 删原帖并将记录存入posts_delete_log,以及惩罚用户

                # 降颜值
                user = connection.Users.find_one({"_id": ObjectId(cursor.author)})
                add_exp(user, -exp_reduce)

                # 禁言,并提醒用户发了违规帖子
                lock_user(cursor, reason, exp_reduce, ban_days, category)

                # 奖励举报人
                for reporter in cursor.reporters:
                    notification.valid_report_post.delay(reporter,
                                                         cursor.theme_id,
                                                         cursor.post_id,
                                                         exp_reduce)

                # 删原帖至垃圾箱
                collection = connection[MongoConfig.DB]["posts_" + cursor.theme_id]
                post = collection.find_one({"_id": ObjectId(cursor.post_id)})
                trash = connection.TrashPosts()
                for (key, value) in post.items():
                    trash[key] = value
                trash._id = "{}:{}".format(cursor.theme_id, cursor.post_id)
                trash._created = datetime.timestamp(trash._created)
                trash._updated = datetime.timestamp(datetime.utcnow())
                trash.save()
                collection.Posts.find_and_modify(
                    {"_id": ObjectId(cursor.post_id)}, remove=True)

                # 删用户发帖记录
                connection.UserPosts.find_and_modify(
                    {"user_id": cursor.author, "post_id": cursor.post_id}, remove=True)

                # 改帖子相关评论属性
                collection = connection[MongoConfig.DB]["comments_" + cursor.theme_id]
                collection.Comments.find_and_modify(
                    query={"post_id": cursor.post_id}, update={"$set": {"deleted": True}})

                # 存日志
                logger.posts_delete_log.delay(dumps(cursor), exp_reduce, ban_days, admin, reason)

                # 归档
                cursor.archived = True
                cursor.save()

        elif category == 'comment':
            cursor = connection.ReportComments.find_one({'_id': ObjectId(report_id)})
            if not cursor:
                return {
                           'status': 'error',
                           'message': 'report_comments这个表中不存在ObjectId(%s)' % report_id
                       }, 404
            else:
                # 处理规则: 删原帖并将记录存入comments_delete_log,以及惩罚用户
                collection = connection[MongoConfig.DB]["comments_" + cursor.theme_id]
                comment = collection.find_one({"_id": ObjectId(cursor.comment_id)})

                # 降颜值
                user = connection.Users.find_one({"_id": ObjectId(cursor.author)})
                add_exp(user, -exp_reduce)

                # 禁言,并提醒用户发了违规帖子
                if not hasattr(cursor, "post_id"):
                    cursor["post_id"] = comment["post_id"]
                lock_user(cursor, reason, exp_reduce, ban_days, category)

                # 奖励举报人
                for reporter in cursor.reporters:
                    notification.valid_report_comment.delay(reporter,
                                                            cursor.theme_id,
                                                            cursor.comment_id,
                                                            exp_reduce)

                # 改评论属性并扔进垃圾箱
                trash = connection.TrashComments()
                for (key, value) in comment.items():
                    trash[key] = value
                trash._id = "{}:{}".format(cursor.theme_id, cursor.comment_id)
                trash._created = datetime.timestamp(datetime.utcnow())
                trash.save()
                collection.Comments.find_and_modify(
                    query={"_id": ObjectId(cursor.comment_id)}, update={"$set": {"deleted": True}})

                # 删用户评论记录
                connection.UserComments.find_and_modify(
                    {"user_id": cursor.author, "comment_id": cursor.comment_id}, remove=True)

                # 存日志
                logger.comments_ban_log.delay(dumps(cursor), exp_reduce, ban_days, admin, reason)

                # 归档
                cursor.archived = True
                cursor.save()
        else:
            return {
                       'status': 'error',
                       'message': '%s, the value of category is wrong' % category
                   }, 400

        return {
                   'status': 'ok',
                   'message': '审查成功'
               }, 201
