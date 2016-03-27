import re
import random

from flask_restful import Resource, reqparse

import top.api
from config import AliConfig
from model import redisdb


def send_sms(phone, code):
    """发送验证码"""
    req = top.api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo(AliConfig.SMS_IKEY, AliConfig.SMS_AKEY))
    req.sms_type = AliConfig.SMS_TYPE
    req.rec_num = phone
    req.sms_template_code = AliConfig.SMS_TEMPLATE_CODE
    req.sms_free_sign_name = AliConfig.SMS_FREE_SIGN_NAME
    req.sms_param = {
        "code": code,
        "product": AliConfig.APP_NAME
    }
    try:
        resp = req.getResponse()
    except:
        return None
    return resp


def generate_verification_code(code_length=6):
    """随机生成6位数验证码"""
    code_list = random.sample([str(i) for i in range(10)], code_length)
    return "".join(code_list)


def verify_phone(phone):
    """正则匹配手机号码"""
    pattern = re.compile('^0\d{2,3}\d{7,8}$|^1[358]\d{9}$|^147\d{8}')
    return pattern.match(phone)


class RequestSmsCode(Resource):
    def get(self, cellphone):
        if not verify_phone(cellphone):
            return {'message': 'not a valid phone number'}, 400
        verify_code = generate_verification_code(6)
        resp = send_sms(cellphone, verify_code)
        if resp and resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
                "err_code"] == "0":
            if redisdb.setex(
                "sms_verify:{}".format(cellphone),
                AliConfig.SMS_TTL * 60,
                verify_code
            ):
                return {"status": "ok"}
            else:
                return {
                    "status": "error",
                    "message": "something wrong with the redis server"
                }
        else:
            return {
                "status": "error",
                "message": "something wrong with the sms service"
            }


class VerifySmsCode(Resource):
    def get(self, cellphone):
        parser = reqparse.RequestParser()
        parser.add_argument('code',
                            type=str,
                            required=True,
                            help='verify_code not found')
        args = parser.parse_args()
        user_code = args['code']
        if not redisdb.exists("sms_verify:{}".format(cellphone)):
            return {
                "status": "error",
                "message": "sms code out of date"
            }
        sys_code = redisdb.get("sms_verify:{}".format(cellphone))
        if sys_code == user_code:
            return {
                "status": "ok"
            }
        else:
            return {
                "status": "error",
                "message": "sms code doesn't match"
            }