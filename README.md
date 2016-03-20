# 大学城专线2实时公交

## 环境搭建

修改配置文件相应参数

    $ copy config.py.sample config.py
    $ vim config.py

python虚拟环境

    $ virtualenv /opt/virtualenv/gzbus
    $ source /opt/virtualenv/gzbus/bin/activate
    $ pip install -r requirements.txt

专线2实时位置抓取

    # 根据config.py设置，默认每隔5秒查询一次数据，保存到redis中
    $ python getbus.py

服务端接口

    # 测试,使用wsgi simple_serve
    $ python server.py
    # or, gunicorn + gevent 
    $ gunicorn server:app -c config.py

    # 默认监听localhost:9999
    $ curl -v "127.0.0.1:9999/positive"
    $ curl -v "127.0.0.1:9999/negative

Supervisor管理

    $ sudo apt-get install supervisor
    $ cp supervisor.conf /etc/supervisor/conf.d/gzbus.conf
    $ sudo supervisorctl
    > update

## 接口说明

* positive: 专线2正向；
* negative：专线2反向；
