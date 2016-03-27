# 假面API文档

> `json2md.py`可以将postman备份文档输出为md格式,需要mongodb的依赖

## DEL 删除公告帖评论

- 方法 **DELETE**

- URI `/board_comments/56d92bad7fe9e30ec00a535a`

## GET 获取帖子列表

- 方法 **GET**

- URI `/theme/56d59bd4294d90ac3d8749d8/posts`

参数
`?page=1` 默认显示第一页, 每页 10 条内容, 无参数默认显示第一页

endpoints
```
/theme/<string:theme_id>/posts/
/theme/<string:theme_id>/posts
```
输入: 无
输出: 当前主题下按时间顺序排列的最新`10`个帖子
状态码: 200

- 加密请求方法

可以以参数方式放在URI中,
如`?access_token=xxx`这种形式(不建议)

另外可以放在Headers里, 如

```
key=Authorization
value=Bearer xxx  # Bearer是这个授权框架的名字, 后面需要留一个半角空格再加access_token
```


## POST 新增普通帖

- 方法 **POST**

- URI `/theme/56d59bd4294d90ac3d8749d8/posts`

默认返回帖子`_id`, 状态码`201`

`_created`和`_updated`两个字段不需要传, 服务器会自动创建, 日后有更新只需要给`_update`填`""`或者不传即可, 服务器会自动生成当前时间填充

- Body: 

```
{}

```

## GET 获取反馈页面信息

- 方法 **GET**

- URI `/theme/用户反馈?category=system`

默认endpoint

```
/theme/用户反馈?category=system
```

## DEL 删除主题

- 方法 **DELETE**

- URI `/themes/56d922da7fe9e30ec00a52d2`

## PUT 更新一个普通帖

- 方法 **PUT**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56d9a8a84b33d510e7ad18a1`

有更新只需要给`_update`填`""`或者不传即可, 服务器会自动生成当前时间填充

输入

返回值: 无

状态码: 204

- Body: 

```
{
    "author": ""
}

```

## POST 收藏/标记一个普通帖子

- 方法 **POST**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56df88ab7fe9e310478b934e/star`

endpoint
```
/theme/<theme_id>/post/<post_id>/star
```
输入
```
?user_id=<user_id>
```
输出

  正常 返回201状态码

  已收藏过 返回200, 并带有提示信息
  
  自己不能收藏自己 返回400


- Body: 

```
{
    "user_id" : "56df88ab7fe9e310478b9312"
}

```

## POST 获取授权码

- 方法 **POST**

- URI `/token`

- http测试样例

```
POST /token HTTP/1.1
Host: 127.0.0.1:5000
Content-Type: application/x-www-form-urlencoded
# 受限于框架, client_id 和 username 必须一致且必须为设备id
grant_type=password&
client_id=super&
username=super&
password=%242b%2412%24q3UwMyIw4OBo5SPMgbGqqeNOAa5Hyq4FhgScW5Qf8%2FjK41ALoj1yK
```

- password生成方式

password 为 username 加密后的值

```
import bcrypt
password = b"username"
bcrypt.hashpw(password, bcrypt.gensalt())
# 结果就可以当成是与username对应的密码
```

- 返回结果

```
{
    "token_type": "Bearer", 
    "scope": "", 
    "expires_in": 864000, 
    "access_token": "fvzc7tYXI4aC4yApfX2lBb6FPkigfH",
    "refresh_token": "LWpMcVXrsFb6AnmMZfqTQOxUt1NHCX"
}
```

## GET 验证手机验证码

- 方法 **GET**

- URI `/verify_sms_code/15399481600?code=327145`

- endpoint

```
/verify_sms_code/<cellphone>?code=xxxxxx
```

- 返回值

正常

```
{
    "statu": "ok"
}
```

异常(不匹配或者超时)

```
{
    "statu": "error",
    "message": "xxx"
}
```

## GET 获取一个普通帖

- 方法 **GET**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56d9a8a84b33d510e7ad18a1`

参数包含在uri里面

endpoints
```
    /theme/<string:theme_id>/post/<string:post_id>
    /theme/<string:theme_id>/post/<string:post_id>/
```
输入: 无

输出: 帖子信息

状态码: 200

- Body: 

```
{
    "_updated": 1456811105.953,
    "hearts": {
        "user_id": "56cd77557fe9e32f0439e4f7",
        "mask_id": "56cd77557fe9e32f0439e4fa"
    },
    "comment_count": 123,
    "_created": 1456811105.953,
    "author": "56cd77557fe9e32f0439e4f7",
    "_id": "56d59ce17fe9e3493aa291f4",
    "content": {
        "type": "text",
        "options": ["不知道填啥"],
        "photo": "测试",
        "text": "开始懂得生活就是生活"
    },
    "location": {
        "coordinates": [
            100,
            5.5
        ],
        "type": "Point"
    },
    "mask_id": "56cd77557fe9e32f0439e4f7"
}

```

## POST 新建一个参数表项

- 方法 **POST**

- URI `/parameters`

- Body: 

```
{}


```

## DEL 删除用户

- 方法 **DELETE**

- URI `/users/56d3b1c07fe9e3165feb1e40`

## GET 根据设备ID获得对应用户信息

- 方法 **GET**

- URI `/device/9be0511311672634/user`

/device/<device_id>/user

返回

  用户信息, 并刷新用户登录时间记录

## PUT 更新主题

- 方法 **PUT**

- URI `/theme/56d922da7fe9e30ec00a52d2`

- 数据结构

```
structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "district", "virtual", "private"),
        "short_name": str,
        "full_name": str,
        "locale": {
            "nation": str,
            "province": str,
            "city": str,
            "county": str
        }
    }
```

- Body: 

```
{
  "_id": "56d922da7fe9e30ec00a52d2",
  "short_name": null,
  "category": null,
  "full_name": null,
  "locale": {
    "county": "大理",
    "city": "昆明",
    "nation": "中国",
    "province": "云南"
  }
}

```

## GET 获取普通帖评论列表

- 方法 **GET**

- URI `/theme/56d59bd4294d90ac3d8749d8/comments`

参数: 可以加`page=`指定页码

endpoints
```
/theme/<string:theme_id>/comments/
/theme/<string:theme_id>/comments
```
输入: 无
输出: 当前主题下的评论,默认只显示第一页
状态码: 200


## DEL 获取参数列表

- 方法 **GET**

- URI `/parameters`

-- 数据结构

```
default_masks[]:系统头像 用来给新用户随机分配

```

## POST 添加主题

- 方法 **POST**

- URI `/themes`

- 数据结构

```
structure = {
        "_id": CustomObjectId(),
        "category": IS("school", "district", "virtual", "private"),
        "short_name": str,
        "full_name": str,
        "locale": {
            "nation": str,
            "province": str,
            "city": str,
            "county": str
        }
    }
default_values = {
        "category": "school",
        "short_name": "",
        "full_name": "",
        "locale.nation": "中国",
        "locale.province": "",
        "locale.city": "",
        "locale.district": ""
    }
```

- Body: 

```
{}

```

## DEL 删除一条评论

- 方法 **DELETE**

- URI `/comments_56d59bd4294d90ac3d8749d8/56d3a2de7fe9e311d9ed1312`

## GET 根据坐标获取附近学校/地区信息

- 方法 **GET**

- URI `/location/schools?lon=108.92983&lat=34.246592`

输入
  参数分别是经度和纬度, 最多允许不超过6位小数点
输出
  附近学校/地区信息, 列表形式

## POST 添加公告帖

- 方法 **POST**

- URI `/board_posts`

- 数据结构

```
_id
作者：author (user._id)
内容：content
感谢：hearts[]
    用户：user_id
    面具：mask_id
时间：_created
面具：mask_id（发帖时的用户面具_id）

structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }
```

- Body: 

```
{}

```

## GET 获取所有公告帖评论列表

- 方法 **GET**

- URI `/board_comments`

- 数据结构

```
_id
原帖：post_id（帖子id）
作者：author
内容：content
感谢：hearts[]
    用户：user_id
    面具：mask_id
时间：_created
面具：mask_id
`
structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }
```

## POST 添加一条普通帖评论

- 方法 **POST**

- URI `/theme/56d59bd4294d90ac3d8749d8/comments`

- Body: 

```
{"author": "56dd48d77fe9e31a5a4abfe3"}

```

## POST 新建一个公告帖评论

- 方法 **POST**

- URI `/board_comments`

- 数据结构

```
_id
原帖：post_id（帖子id）
作者：author
内容：content
感谢：hearts[]
    用户：user_id
    面具：mask_id
时间：_created
面具：mask_id
`
structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }
```

- Body: 

```
{}

```

## DEL 取消一个普通帖的收藏/标记

- 方法 **DELETE**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56df88ab7fe9e310478b934e/star?user_id=56df88ab7fe9e310478b9312`

endpoint
```
/theme/<theme_id>/post/<post_id>/star?user_id=<user_id>
```
return
  均返回 204 状态码

## GET 获取某一主题

- 方法 **GET**

- URI `/theme/用户反馈?category=system`

默认endpoint

```
/theme/<theme_id>
```

不加参数接受一个ObjectId, 返回对应id的主题信息

- 参数

category表示主题类型, 可以取的值只有
```
"school", "district", "virtual", "private", "system"
```
带参数的情况下, 上面的theme_id被当做是fullname传入, 根据fullname和category可以得到一个对应的主题信息并返回


## GET 获取某用户发的帖子

- 方法 **GET**

- URI `/user/56dd48d77fe9e31a5a4abfe3/posts`

endpoint:
```
/user/<user_id>/posts
/user/<suer_id>/posts/
```

## GET 列出所有用户

- 方法 **GET**

- URI `/users`

## PUT 更新一条评论

- 方法 **PUT**

- URI `/theme/56d59bd4294d90ac3d8749d8/comment/56de57d67fe9e316bba45c6d`

- Body: 

```
{
  "author": null,
  "post_id": null,
  "content": null,
  "_created": 1457383254.126,
  "location": {
    "type": "Point",
    "coordinates": [
      100,
      0
    ]
  },
  "hearts": [],
  "mask_id": null,
  "_id": "56de57d67fe9e316bba45c6d"
}

```

## GET 发送手机验证码

- 方法 **GET**

- URI `/request_sms_code/15399481600`

- endpoint

```
/request_sms_code/<cellphone>
```

- 返回值

正常

```
{
    "statu": "ok"
}
```

异常

```
{
    "statu": "error",
    "message": "xxx"
}
```


## PUT 更新公告帖

- 方法 **PUT**

- URI `/board_post/56d92a4d7fe9e30ec00a52d5`

- 数据结构

```
_id
作者：author (user._id)
内容：content
感谢：hearts[]
    用户：user_id
    面具：mask_id
时间：_created
面具：mask_id（发帖时的用户面具_id）

structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }
```

- Body: 

```
{
  "content": "测试",
  "author": null,
  "hearts": [],
  "_id": "56d92a4d7fe9e30ec00a52d5",
  "_created": 1457043917.529,
  "mask_id": null
}

```

## POST 新建一条用户规则信息

- 方法 **PUT**

- URI `/user_levels/56d92fb27fe9e30ec00a535c`

- Body: 

```
{
  "report_limit": 100,
  "colors": [],
  "text_post": null,
  "photo_post": null,
  "exp": null,
  "vote_post": null,
  "_id": "56d92fb27fe9e30ec00a535c",
  "heart_limit": null,
  "message_limit": null,
  "post_limit": null
}

```

## GET 查看一个公告帖评论

- 方法 **GET**

- URI `/board_comment/56d92bad7fe9e30ec00a535a`

## GET 读取一条评论

- 方法 **GET**

- URI `/theme/56d59bd4294d90ac3d8749d8/comment/56de57d67fe9e316bba45c6d`

参数: 无

endpoints
```
/theme/<string:theme_id>/comment/<string:comment_id>/
/theme/<string:theme_id>/comment/<string:comment_id>
```
输入: 无
输出: 当前主题下指定评论
状态码: 200


## DEL 删除公告帖

- 方法 **DELETE**

- URI `/board_posts/56d92a4d7fe9e30ec00a52d5`

## DEL 删除一个普通帖

- 方法 **DELETE**

- URI `/theme/56d59bd4294d90ac3d8749d8/posts/56d59f197fe9e3493aa291f7`

对应的评论也会一并删除

## GET 查看公告帖

- 方法 **GET**

- URI `/board_post/56d92a4d7fe9e30ec00a52d5`

## GET 获取某用户发的评论

- 方法 **GET**

- URI `/user/56dd48d77fe9e31a5a4abfe3/comments`

endpoint:
```
/user/<user_id>/comments
/user/<suer_id>/comments/
```


## GET 根据设备号获取/新建用户

- 方法 **GET**

- URI `/device/9be0511311672634`

/device/<device_id>


## POST 新建一条用户等级规则

- 方法 **POST**

- URI `/user_levels`

- Body: 

```
{}

```

## PUT 更新公告帖评论

- 方法 **PUT**

- URI `/board_comment/56d92bad7fe9e30ec00a535a`

- Body: 

```
{
  "content": "什么东西",
  "hearts": [],
  "_created": 1457044269.747,
  "author": null,
  "mask_id": null
}

```

## GET 获取指定帖子所有评论

- 方法 **GET**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56dd49587fe9e31a5a4abfe4/comments`

参数: `?page=数字` 可以不加,默认返回第一页,每页十项

endpoint
```
/theme/56d59bd4294d90ac3d8749d8/post/56dd49587fe9e31a5a4abfe4/comments
/theme/56d59bd4294d90ac3d8749d8/post/56dd49587fe9e31a5a4abfe4/comments/
```

输入: 无

输出: 指定帖子的评论

状态码: `200`

## DEL 删除设备信息

- 方法 **DELETE**

- URI `/devices/asdfsg`

## GET 读取主题列表

- 方法 **GET**

- URI `/themes`

## GET 获取某用户收藏的帖子

- 方法 **GET**

- URI `/user/56df88ab7fe9e310478b934e/stars`

endpoint
```
/user/<user_id>/stars
/user/<user_id>/stars/
```


## POST 给指定普通帖子添加感谢

- 方法 **POST**

- URI `/theme/56d59bd4294d90ac3d8749d8/post/56df88ab7fe9e310478b934e/hearts`

参数: 无

endpoints
```
/theme/<string:theme_id>/post/<string:post_id>/hearts
```
输入: 
```
{
    "user_id": str,
    "mask_id": str
}
```
输出: 无

状态码: 

  正常: 201
  异常: 重复感谢或者自己感谢自己, 返回码 204


- Body: 

```
{
    "user_id": "56e3b2b17fe9e3140bfb2623",
    "mask_id": "56e3b2b17fe9e3140bfb2623"
}

```

## GET 获取一个用户信息

- 方法 **GET**

- URI `/user/56e678167fe9e3315628da6e`

## GET 获取公告列表

- 方法 **GET**

- URI `/board_posts`

- 数据结构

```
_id
作者：author (user._id)
内容：content
感谢：hearts[]
    用户：user_id
    面具：mask_id
时间：_created
面具：mask_id（发帖时的用户面具_id）

structure = {
        "_id": CustomObjectId(),
        "_created": CustomDate(),
        "mask_id": str,
        "hearts": [
            {
                "mask_id": str,
                "user_id": str
            }
        ],
        "content": str,
        "author": str
    }
```

## GET 获取所有设备信息列表

- 方法 **GET**

- URI `/devices`

```
_id （这个_id主动插入，详见设计文档）
设备名称：name （没啥用，后台管理和测试的时候用做参考）
用户：user_id（users的_id)
原始用户：origin_user_id（第一次登陆时的设备用户）
```

## PUT 更新用户信息

- 方法 **PUT**

- URI `/user/56dd48d77fe9e31a5a4abfe3`

- Body: 

```
{
"name": ""
}

```

## PUT 修改设备信息

- 方法 **PUT**

- URI `/device/9be0511311672634`

## GET 获取具体等级信息

- 方法 **GET**

- URI `/user_levels/56d92fb27fe9e30ec00a535c`

## GET 获取用户等级列表

- 方法 **GET**

- URI `/user_levels`

```
_id
级别名称：name
所需颜值：exp
每日发帖上限：post_limit
每日举报上限：report_limit
每日纸条上限：message_limit
能否发文字帖：text_post
能否发投票贴：vote_post
能否发照片贴：photo_post
可用颜色：colors[]
感谢上限：heart_limit


structure = {
        "_id": CustomObjectId(),
        "exp": str,
        "post_limit": int,
        "report_limit": int,
        "message_limit": int,
        "text_post": bool,
        "vote_post": bool,
        "photo_post": bool,
        "colors": list,
        "heart_limit": int
    }
```

## DEL 删除一条用户等级规则记录

- 方法 **DELETE**

- URI `/user_levels/56d92fb27fe9e30ec00a535c`

- Body: 

```
{
  "report_limit": 100,
  "colors": [],
  "text_post": null,
  "photo_post": null,
  "exp": null,
  "vote_post": null,
  "_id": "56d92fb27fe9e30ec00a535c",
  "heart_limit": null,
  "message_limit": null,
  "post_limit": null
}

```

