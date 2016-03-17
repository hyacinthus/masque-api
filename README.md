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
### 启动应用
克隆项目到本地, 进入虚拟python运行环境, 在项目根目录执行
```
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