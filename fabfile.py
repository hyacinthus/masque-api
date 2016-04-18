import sys
import json
import requests
from datetime import datetime

from fabric.api import local, task
from fabric.colors import blue, red

nowtime = datetime.utcnow()


def do_exit(msg):
    print(red(msg))
    print(blue('Exit!'))
    sys.exit()


def get_event():
    url = "https://api.github.com/repos/Tarsbot/masque-api/events"
    querystring = {"page": "1", "per_page": "1"}
    headers = {'authorization': 'Basic ZmVyc3Rhcjpxd2VydDEyMzQ1'}
    response = requests.request("GET", url, headers=headers, params=querystring)
    return json.loads(response.text)[0]


@task
def pull():
    resp = get_event()
    if resp['type'] != "PushEvent":
        do_exit('No Push Event')
    else:
        push_time = datetime.strptime(resp['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        deltime = nowtime - push_time
        if deltime.seconds > 330:
            do_exit('Nothing to be done')
        else:
            local('git fetch', capture=False)
            local('git pull', capture=False)
            local('sudo supervisorctl restart masque', capture=False)
            do_exit('Update Complete!')
