import json
import logging
from config import AliConfig
from aliyunsdkcore import client
from aliyunsdkgreen.request.v20160308 import ImageDetectionRequest

clt = client.AcsClient(AliConfig.GREEN_IKEY, AliConfig.GREEN_AKEY, AliConfig.REGIONID)
log = logging.getLogger("masque.detection")


def detect(image_url, async=False, scene=['porn']):
    # 每次调用请重新生成一个request， 否则会抛出signatureNotMatch异常
    request = ImageDetectionRequest.ImageDetectionRequest()
    request.set_accept_format('json')
    request.set_Async(json.dumps(async))
    request.set_ImageUrl(
        json.dumps([image_url]))
    # 设置要检测的服务场景
    # porn: 黄图检测
    # ocr: ocr检测
    request.set_Scene(json.dumps(list(x for x in scene)))
    response = clt.do_action(request)

    result = json.loads(response.decode('utf-8'))

    if result["Code"] == "Success":
        imageDetectResult = result["ImageResults"]["ImageResult"][0]
        pornResult = imageDetectResult["PornResult"]
        label, rate = pornResult["Label"], pornResult["Rate"]
        return label, rate
    else:
        try:
            message = result['Message']
        except KeyError:
            message = result['Msg']
        raise Exception('Code: %s' % result["Code"],
                        'Message: %s' % message)
