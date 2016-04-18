# masque-api 测试/部署说明

## 项目依赖

```
sudo apt-get install libpcre3 libpcre3-dev mongodb virtualenvwrapper \
    redis-server rabbitmq-server supervisor
```

> 注: MongoDB 如果是从官网软件源安装, 则包名为 mongodb-org

## Python Venv 环境准备

### virtualenvwrapper

```
sudo vi ~/.zshrc
# 添加下面这句
source /usr/local/bin/virtualenvwrapper.sh
# 保存退出, 应用环境变量
source ~/.zshrc
# 创建一个独立的python运行环境
mkvirtualenv -p python3 test
# 切换到上面新建的python运行环境
workon test
# 退出运行环境
deactivate
```

### 安装 Python 依赖

```
git clone git@github.com:Tarsbot/masque-api.git
cd masque-api
# 进入虚拟 Python 运行环境
workon test
pip install -r requirements.txt
```

> 注: 可以选用阿里云的 pip 镜像站加快 Python 软件包的下载速度
>> vi ~/.pip/pip.conf

```
[global]
index-url = http://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host=mirrors.aliyun.com
```

## 调试应用

```
# 进入虚拟python运行环境
workon test
# 保证mongodb redis rabbitmq都在正常运行
# 然后在一个终端执行
python masque.py
# 在另一个终端启动队列
sh celery.sh
```

## 生产部署

### 准备

* 在/run新建masque目录，并修改用户组`chown masque:www-data masque`，若要自定wsgi的socket路径，需要相应修改wsgi.ini文件
* 如有必要，修改wsgi.ini文件的并行数等参数。
* 将masque.conf.example复制到/etc/init目录，重命名为masque.conf，并修改其中的参数。
* masque.conf中，env为python venv的bin目录位置，chdir为项目目录。
* 使用`service masque start`即可启动wsgi服务
* 将nginx.example复制到/etc/nginx/sites-available，重命名为域名，并修改参数。比如证书位置。
* 在/etc/nginx/sites-enabled建立链接。
* `nginx -t`检查配置
* `service nginx reload`

### 持续部署

1. `git checkout product && git pull`
2. `sudo service masque restart`
