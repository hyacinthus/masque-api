import logging
from datetime import datetime
from json import dumps

from bson.objectid import ObjectId
from flask_restful import Resource, request, reqparse

from config import MongoConfig, APIConfig
from model import connection, TokenResource, CheckPermission
from paginate import Paginate
from tasks import notification
from util import add_exp, is_chinese

log = logging.getLogger("masque.inspect")


class Inspect(TokenResource):
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
            cursor = connection.ReportPost.find_one({'_id': ObjectId(report_id)})
            if not cursor:
                return {
                           'status': 'error',
                           'message': 'report_posts这个表中不存在ObjectId(%s)' % report_id
                       }, 404
            else:
                # 处理规则: 删原帖并将记录存入posts_delete_log,以及惩罚用户

                pdl = connection.PostsDeleteLog()
                pdl.theme_id = cursor.theme_id
                pdl.post_id = cursor.post_id
                pdl.author = cursor.author
                pdl.exp_reduce = exp_reduce
                pdl.ban_days = ban_days
                pdl.save()

        else:
            cursor = connection.ReportComments.find_one({'_id': ObjectId(report_id)})
            if not cursor:
                return {
                           'status': 'error',
                           'message': 'report_comments这个表中不存在ObjectId(%s)' % report_id
                       }, 404
            else:
                # 处理规则: 删原帖并将记录存入posts_delete_log,以及惩罚用户
                cbl = connection.CommentsBanLog()
                cbl.theme_id = cursor.theme_id
                cbl.post_id = cursor.post_id
                cbl.comment_id = cursor.post_id
                cbl.author = cursor.author
                cbl.exp_reduce = exp_reduce
                cbl.ban_days = ban_days
                cbl.save()
        return {
                   'status': 'ok',
                   'message': '审查成功'
               }, 201

