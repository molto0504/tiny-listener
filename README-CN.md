# Tiny-listener

Tiny-listener 是一个基于 Python 3.6+ 的轻量事件框架, 

[中文](README-CN.md) / [English](README.md)

## 需求

Python 3.6+

## 安装

```shell
$ pip install tiny-listener
```

## 为什么使用 Tiny-listener:

- ✔ 纯 Python, 安装包非常小
- ✔ 轻量快速, 基于原生协程实现
- ✔ 简单易用

## Tiny-listener 如何工作:

1. 编写你的事件处理方法, 比如:

```python
@app.on_event("emergency")
def plan_B():
    # do something
    ...

@app.on_event()
def plan_A():
    # do something
    ...
```

2. 保持监听(如端口, 队列等) 直到发生事件, 比如:

```python
async def listen(self):
   while True:
       msg = await queue.get()  # msg 可能是 "emergency" 或其他状态
       self.fire(msg)  # fire event
```

3. Tiny-listener 会自动分发事件:
   当监听者收到一个 msg 时,
   Tiny-listener 就会默认调用 `plan_A`,  除非这个 msg 是 "emergency",
   这种情况下 Tiny-listener 会调用 `plan_B`.

## 例子

**example.py**

```python
from tiny_listener import Listener, Event

class App(Listener):
   async def listen(self):
      """监听事件"""
      self.fire("Say hi to Alice")
      self.fire("Say hi to Bob")
      self.fire("Say hi to Carol")


app = App()


@app.on_event("Say hi to {name}")
async def say_hi(event: Event):
   """处理事件"""
   print("Hi,", event.params["name"])

```

使用 tiny-listener 命令启动应用:

```shell
$ tiny-listener example:app
>>> Hi, Alice
>>> Hi, Bob
>>> Hi, Carol
```
