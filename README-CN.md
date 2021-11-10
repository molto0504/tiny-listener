# Tiny-listener

Tiny-listener 是一个基于 Python 3.6+ 的轻量/高速事件处理框架, 

[中文](README-CN.md) / [English](README.md)

## 需求

Python 3.6+

## 安装

```shell
$ pip3 install tiny-listener
```

## 使用

Tiny-listener 能帮助你什么:

    - 快速实现
    - 高并发
    - 可扩展

Tiny-listener 处理事件的方式是:

    监听(listen) -> 触发(fire) -> 执行(do)

一个典型的场景:

    监听一个消息队列(message queue), 并为每个收到的消息(message)定义处理方法(handler)

**example.py**

```python
from tiny_listener import Listener

class App(Listener):
    async def listen(self, fire):
        # 通常情况下, 你会通过监听一些消息队列如 Redis 或 RabbitMQ 等触发事件
        # 这里我们省略这个过程, 直接触发事件
        fire("/event/1")  # 触发事件 1
        fire("/event/2")  # 触发事件 2

app = App()

@app.do("/event/1")
async def do_something():
    print("* event 1 done!")

@app.do("/event/2", parents=["/event/1"])
async def do_something():
    print("* event 2 done!")
```

使用 tiny-listener 命令启动你的应用

```shell
$ tiny-listener example:app
>> event 1 done!
>> event 2 done!
```

可以看到 tiny-listener 按照 `fire` 函数定义的顺序依次触发了两个事件, 如果你将两个 `fire` 函数调换位置:

```python
from tiny_listener import Listener

class App(Listener):
    async def listen(self, fire):
        fire("/event/2")  # 触发事件 2
        fire("/event/1")  # 触发事件 1
...
```

再次运行你的代码, 你会发现事件触发的顺序并没有改变.

这是因为 `app.do` 方法的 parents 参数可以指定事件触发顺序,
无论 `fire` 何时被调用, */event/2* 总会在 */event/1* 后执行.
