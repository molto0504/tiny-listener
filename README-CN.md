# Tiny-listener

Tiny-listener 是一个基于 Python 3.6+ 的轻量事件框架, 

[中文](README-CN.md) / [English](README.md)

## 需求

Python 3.6+

## 安装

```shell
$ pip install tiny-listener
```

## 特色

为什么使用 Tiny-listener:

    - 简单易用
    - 高性能

Tiny-listener 处理事件的方式是:

    监听(如端口, 队列, 文件等) -> 触发(事件) -> 执行(事件)

## 例子

**example.py**

```python
from tiny_listener import Listener, Params

class App(Listener):
    async def listen(self, fire):
        """listen event"""
        fire("Say hi to Alice") # fire event
        fire("Say hi to Bob")
        fire("Say hi to Carol")


app = App()


@app.do("Say hi to {name}")
async def say_hi(param: Params):
    """handle event"""
    print("Hi,", param["name"])

```

使用 tiny-listener 命令启动应用:

```shell
$ tiny-listener example:app
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```
