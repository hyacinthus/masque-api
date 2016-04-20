import json
from config import AliConfig
from aliyunsdkcore import client
from aliyunsdkgreen.request.v20160308 import ImageDetectionRequest

clt = client.AcsClient('IuZZE8uphLHbbo7e', 'EcYS7y4K7MfJtzHfNVuxVpUaK4lXn0', 'cn-shenzhen')


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
        print(result)
        raise Exception('Code: %s' % result["Code"],
                        'Message: %s' % result["Msg"])
