import oss2
import bcrypt
import requests
import datetime
from model import redisdb

localhost = "http://localhost"


class OssConnection:
    def __init__(self):
        self._bucket = None
        self._extime = None

    # 获得api_token
    def get_api_token(self, username='admin'):
        params = {
            'grant_type': 'password',
            'client_id': username,
            'username': username,
            'password': bcrypt.hashpw(str.encode(username), bcrypt.gensalt()).decode()}
        headers = {"Content-type": "application/x-www-form-urlencoded"}
        response = requests.post("%s/token" % localhost, data=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            expire_time = data['expires_in']
            redisdb.setex('admin:{%s}:api_access_token' % username,
                          expire_time, data['access_token'])
            redisdb.set('admin:{%s}:api_refresh_token' % username,
                        data['refresh_token'])

        else:
            raise Exception('Status: {0}, Reason: {1}'.format(response.status_code, response.reason))
        return data['access_token']

    # 获得oss_token
    def get_auth(self):
        access_token = redisdb.get("admin:{admin}:api_access_token")
        access_token = self.get_api_token() if access_token is None else access_token
        headers = {'authorization': "Bearer " + access_token}
        res = requests.get("%s/image_token" % localhost, headers=headers)
        if res.status_code == 200:
            token = res.json()
            _time = token['Credentials']['Expiration']
            self._extime = datetime.datetime.strptime(_time, "%Y-%m-%dT%H:%M:%SZ")
        elif res.status_code == 401:
            headers = {'authorization': "Bearer " + self.get_api_token()}
            res = requests.get("%s/image_token" % localhost, headers=headers)
            if res.status_code == 200:
                token = res.json()
                _time = token['Credentials']['Expiration']
                self._extime = datetime.datetime.strptime(_time, "%Y-%m-%dT%H:%M:%SZ")
            else:
                raise Exception('Status: {0}, Reason: {1}'.format(res.status_code, res.reason))

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

    def token(self, username):
        access_token = redisdb.get("admin:{%s}:api_access_token" % username)
        access_token = self.get_api_token(username) if access_token is None else access_token
        return access_token
