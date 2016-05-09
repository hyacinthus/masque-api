from bson.json_util import dumps
from flask import Flask, make_response, jsonify
from flask_restful import Api

from config import DebugConfig
from log import app_log
from model import connection
from oauth2 import oauth
from resources import *


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.FlaskConfig')
    app.config.from_pyfile('config.py', silent=True)
    return app


app = create_app()
app.logger.addHandler(app_log)
oauth.init_app(app)
api = Api(app, decorators=[oauth.require_oauth(), ])


@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(dumps(data, ensure_ascii=False), code)
    resp.headers.extend(headers or {})
    return resp


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(
        {
            'status': 'error',
            'message': '什么都没找到'
        }
    ), 404)


@app.teardown_request
def teardown_request(exception):  # close db connection after each api request
    connection.close()


@app.route('/token', methods=['POST'])
@oauth.token_handler
def access_token():
    return None


api.add_resource(PostsList, '/theme/<string:theme_id>/posts', endpoint='posts')
api.add_resource(Post, '/theme/<string:theme_id>/post/<string:post_id>',
                 endpoint='post')
# 举报帖子
api.add_resource(ReportPost,
                 '/theme/<string:theme_id>/post/<string:post_id>/report',
                 endpoint='report_post')

api.add_resource(Hearts,
                 '/theme/<string:theme_id>/post/<string:post_id>/hearts',
                 endpoint='hearts')
api.add_resource(FavorPost,
                 '/theme/<string:theme_id>/post/<string:post_id>/star',
                 endpoint='post_star')

api.add_resource(CommentsList, '/theme/<string:theme_id>/comments',
                 endpoint='comments')
api.add_resource(PostComments,
                 '/theme/<string:theme_id>/post/<string:post_id>/comments',
                 endpoint='post_comment')
api.add_resource(Comment,
                 '/theme/<string:theme_id>/comment/<string:comment_id>',
                 endpoint='comment')
# 举报评论
api.add_resource(ReportComment,
                 '/theme/<string:theme_id>/comment/<string:comment_id>/report',
                 endpoint='report_comment')

# 感谢某评论
api.add_resource(CommentHeart,
                 '/theme/<string:theme_id>/comment/<string:comment_id>/heart',
                 endpoint='heart_comment')

api.add_resource(UsersList, '/users', endpoint='users')
api.add_resource(User, '/user/<string:user_id>', endpoint='user')
api.add_resource(DeviceUser, '/device/<string:device_id>/user',
                 endpoint='device_user')

api.add_resource(UserPostsList, '/user/<string:user_id>/posts',
                 endpoint='user_posts')
api.add_resource(UserCommentsList, '/user/<string:user_id>/comments',
                 endpoint='user_comments')
api.add_resource(UserStarsList, '/user/<string:user_id>/stars',
                 endpoint='user_stars')

api.add_resource(ThemesList, '/themes', endpoint='themes')
api.add_resource(Theme, '/theme/<string:theme_id>', endpoint='theme')

api.add_resource(DevicesList, '/devices', endpoint='devices')
api.add_resource(Device, '/device/<string:device_id>', endpoint='device')

api.add_resource(UserLevelsList, '/user_levels', endpoint='user_levels')
api.add_resource(UserLevel, '/user_level/<string:user_level_id>',
                 endpoint='user_level')

api.add_resource(MasksList, '/masks', endpoint='masks')
# 在用户列表第一项随机插入一个系统头像
api.add_resource(RandomMask, '/masks/random', endpoint='random_mask')
# 用户上传头像
api.add_resource(UploadMask, '/mask/upload', endpoint='upload_mask')
api.add_resource(Mask, '/mask/<string:mask_id>', endpoint='mask')

api.add_resource(ParametersList, '/parameters', endpoint='parameters')
api.add_resource(Parameter, '/parameter/<string:parameter_id>',
                 endpoint='parameter')

api.add_resource(DeviceTraceList, '/device_traces', endpoint='device_traces')
api.add_resource(DeviceTrace, '/device_trace/<string:device_trace_id>',
                 endpoint='device_trace')

api.add_resource(MessagesList, '/messages', endpoint='messages')
api.add_resource(Message, '/message/<string:message_id>',
                 endpoint='message')

api.add_resource(UserTracesList, '/user_traces', endpoint='user_traces')
api.add_resource(UserTrace, '/user_trace/<string:user_trace_id>',
                 endpoint='user_trace')

api.add_resource(SchoolsList, '/location/schools',
                 endpoint='schools')

api.add_resource(GetToken, '/image_token', endpoint='image_token')
# 用户反馈
api.add_resource(Feedback, '/feedback', endpoint='feedback')
# 发送短信验证码
api.add_resource(RequestSmsCode, '/request_sms_code/<string:cellphone>',
                 endpoint='request_sms_code')
# 验证短信验证码
api.add_resource(VerifySmsCode, '/verify_sms_code/<string:cellphone>',
                 endpoint='verify_sms_code')
# 绑定手机
api.add_resource(BoundPhone, '/bound_phone/<string:cellphone>',
                 endpoint='bound_phone')
# 更换手机
api.add_resource(ChangePhone, '/change_phone/<string:cellphone>',
                 endpoint='change_phone')
# 注销设备
api.add_resource(DeRegister, '/deregister/<string:cellphone>',
                 endpoint='deregister')

# 通知列表
api.add_resource(Notifications, '/notifications', endpoint='notifications')

# 删除单个或多个通知
api.add_resource(DelNotification, '/notifications/multi',
                 endpoint='del_notifi')

if __name__ == '__main__':
    app.run(host=DebugConfig.HOST, port=DebugConfig.PORT)
