# masque-api

## 部署说明

### MongoDB
1. 官网安装说明
  <https://docs.mongodb.org/manual/tutorial/install-mongodb-on-ubuntu/>
2. 开启授权验证
  ```shell
  # 首先切换到test数据库下
  > use test;
  # 添加一个用户root, 密码是abc123
  > db.createUser({
    user: 'root',
    pwd: 'abc123',
    roles: [{role: 'dbOwner', db: 'test'}]
  });
  # 测试下是否正确
  > db.auth("root", "abc123");
   1 # 返回1表示正确
  # 接下来开启数据库授权验证
  sudo vi /etc/mongodb.conf
  auth = ture
  sudo service mongodb restart  # systemd 方式: sudo systemctl restart mongod.service
  
  ```
  
### virtualenvwrapper

```
sudo apt-get install virtualenvwrapper
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
### 调试启动应用
克隆项目到本地, 进入虚拟python运行环境, 在项目根目录执行
```
# uWSGI 的 internal routing 依赖于 pcre, 需要先安装之
sudo apt-get install libpcre3 libpcre3-dev
# 安装 python 依赖包
pip install -r requirements.txt
# 然后执行
python run.py

```
- 输出示例
  ```
   * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
   * Restarting with stat
   * Debugger is active!
   * Debugger pin code: 446-423-189
   
   ```

### 生产部署
Ubuntu  
* 在/run新建masque目录，并修改用户组`chown masque:www-data masque`，若要自定wsgi的socket路径，需要相应修改wsgi.ini文件
* 如有必要，修改wsgi.ini文件的并行数等参数。
* 将masque.conf.example复制到/etc/init目录，重命名为masque.conf，并修改其中的参数。
* masque.conf中，env为python venv的bin目录位置，chdir为项目目录。
* 使用`service masque start`即可启动wsgi服务
* 将nginx.example复制到/etc/nginx/sites-available，重命名为域名，并修改参数。比如证书位置。
* 在/etc/nginx/sites-enabled建立链接。
* `nginx -t`检查配置
* `service nginx reload`

升级部署流程:

1. `git checkout product && git pull`
2. `sudo service masque restart`
