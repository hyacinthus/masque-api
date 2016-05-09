import logging

import top.api
from config import AliConfig
from model import redisdb
from tasks import app
from util import generate_random_number

log = logging.getLogger("masque.task.sms")


@app.task
def send_sms(phone):
    """发送验证码"""
    resp = None
    verify_code = generate_random_number(4)
    req = top.api.AlibabaAliqinFcSmsNumSendRequest()
    req.set_app_info(top.appinfo(AliConfig.SMS_IKEY, AliConfig.SMS_AKEY))
    req.sms_type = AliConfig.SMS_TYPE
    req.rec_num = phone
    req.sms_template_code = AliConfig.SMS_TEMPLATE_CODE
    req.sms_free_sign_name = AliConfig.SMS_FREE_SIGN_NAME
    req.sms_param = {
        "code": verify_code,
        "product": AliConfig.APP_NAME,
        "ttl": str(AliConfig.SMS_TTL)
    }
    try:
        resp = req.getResponse()
    except Exception as e:
        log.error(e)
    if resp and resp["alibaba_aliqin_fc_sms_num_send_response"]["result"][
        "err_code"] == "0":
        if redisdb.lpush(
                "sms_verify:{}".format(phone),
                verify_code
        ):
            if redisdb.ttl("sms_verify:{}".format(phone)) == -1:
                # 设置超时时间
                redisdb.expire("sms_verify:{}".format(phone),
                               AliConfig.SMS_TTL * 60)
        log.info(
            "sms verify_code {} for {} has been saved".format(verify_code,
                                                              phone))
    else:
        log.error("something wrong with the sms server")
