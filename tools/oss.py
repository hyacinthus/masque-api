import oss2
import bcrypt
import requests
import datetime
from model import redisdb


class OssConnection:
    def __init__(self):
        self._bucket = None
        self._extime = None

    # 获得api_token
    def get_api_token(self):
        params = {
            'grant_type': 'password',
            'client_id': 'admin',
            'username': 'admin',
            'password': bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()}
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        response = requests.post("http://localhost/token", data=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            expire_time = data['expires_in']
            redisdb.setex('admin:{%s}:api_access_token' % 'admin',
                          expire_time, data['access_token'])
            redisdb.set('admin:{%s}:api_refresh_token' % 'admin',
                        data['refresh_token'])
        else:
            raise Exception('Status: {0}, Reason: {1}'.format(response.status_code, response.reason))
        return data['access_token']

    # 获得oss_token
    def get_auth(self):
        access_token = redisdb.get("admin:{admin}:api_access_token")
        access_token = self.get_api_token() if access_token is None else access_token
        headers = {'authorization': "Bearer " + access_token}
        res = requests.get("http://localhost/image_token", headers=headers)
        if res.status_code == 200:
            token = res.json()
            if token.get('Credentials'):
                _time = token['Credentials']['Expiration']
                self._extime = datetime.datetime.strptime(_time, "%Y-%m-%dT%H:%M:%SZ")
            else:
                raise Exception(token.get('message'))
        else:
            raise Exception('Status: {0}, Reason: {1}'.format(res.status_code, res.reason))
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
