# 监控系统
显示客户端的系统信息，并自动更新

## 详细流程
- 服务器端等待客户端连接
- 客户端连接上服务器
- 服务器端发送校验通知，客户端手动通知之后，发送用户名和密码
- 服务器校验密码之后，发送校验结果
- 客户端校验成功之后，将系统相关的信息[包括：CPU占用率，磁盘信息，内存信息，网络信息，流量信息等]发送给服务器
- 服务器接收到上述信息之后，将数据写入web根目录下的json文件夹中的stat.json文件
- 前端页面根据这个文件内容，将客户端的信息显示在web网页中

## 各模块的功能描述

### server
校验客户端，将客户端的信息写入到web根目录下的json文件夹中的stat.json文件

### client
客户端，获取系统信息，并发送给服务器

### web
根据web根目录下的json文件夹中的stat.json文件，显示客户端信息

## 其他
客户端连接的信息[用户名和密码]保存在server目录下的config.json文件中。

如：需要增加新的客户端，请自行在config.json文件中手动添加，后续可以考虑通过web页面添加

# TODO
