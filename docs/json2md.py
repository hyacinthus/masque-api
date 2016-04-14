import logging
import subprocess

from mongokit import Connection

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("run")
# 导入备份文档到mongodb
subprocess.call(
    'mongoimport '
    '-d check '
    '-c postman '
    '--file=./masque-api-test.json.postman_collection '
    '--drop',
    shell=True)
# 连接mongodb取出需要内容
connection = Connection()
collection = connection["check"]["postman"]
cursor = collection.find()
req = [i["requests"] for i in cursor][0]
white_list = {
    "url": "URI",
    "method": "方法",
    "name": "名称",
    "description": "描述",
    "rawModeData": "Body"
}

# 整理内容成README.md
file_path = "./README.md"
with open(file_path, "w") as f:
    f.write("# 假面API文档\n\n")
    f.write("> `json2md.py`可以将postman备份文档输出为md格式,需要mongodb的依赖\n\n")
for item in req:
    tmp = {i: item[i] for i in item if i in white_list}
    with open(file_path, "a") as f:
        f.write("## {}\n\n".format(tmp['name']))
        f.write("- {} **{}**\n\n".format(white_list['method'], tmp['method']))
        f.write("- {} `{}`\n\n".format(white_list['url'], tmp['url'][22:]))
        if 'description' in tmp and tmp['description']:
            f.write("{}\n\n".format(tmp['description']))
        if "rawModeData" in tmp and tmp["rawModeData"]:
            f.write(
                "- {}: \n\n```\n{}\n\n```\n\n".format(white_list['rawModeData'],
                                                      tmp['rawModeData']))
