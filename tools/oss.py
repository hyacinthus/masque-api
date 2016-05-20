import oss2
import datetime
import logging

from resources.image import GetOssToken
log = logging.getLogger("masque.oss")


class OssConnection:
    def __init__(self):
        self._bucket = None
        self._extime = None

    # 获得oss_token
    def get_auth(self):
        GT = GetOssToken()
        token = GT.get()[0]

        auth = oss2.StsAuth(token['Credentials']['AccessKeyId'],
                            token['Credentials']['AccessKeySecret'],
                            token['Credentials']['SecurityToken'])
        return auth

    @property
    def bucket(self):
        if self._bucket is None:
            auth = self.get_auth()
            self._bucket = oss2.Bucket(auth, 'oss-cn-beijing.aliyuncs.com', 'masque')
        elif datetime.datetime.utcnow() > self._extime - datetime.timedelta(minutes=2):
            auth = self.get_auth()
            self._bucket = oss2.Bucket(auth, 'oss-cn-beijing.aliyuncs.com', 'masque')
        else:
            pass
        return self._bucket
