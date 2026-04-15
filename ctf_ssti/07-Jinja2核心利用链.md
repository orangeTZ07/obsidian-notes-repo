# Jinja2 核心利用链

## 为什么 Jinja2 在 CTF 里最重要
- Python Web 题里 Flask 很常见，Flask 默认模板引擎就是 Jinja2。
- Jinja2 的对象访问能力强，社区沉淀了大量可复用打法。
- 许多题并不是让你背固定链，而是让你沿着对象关系自己找到链。

## Jinja2 最基础的验证
```jinja2
{{7*7}}
{{"ab" * 3}}
{{config}}
{{request}}
```

如果这些内容能被求值或展示对象信息，就基本进入正题了。

## 常见入口对象
- `config`
- `request`
- `self`
- `cycler`
- `joiner`
- `namespace`
- `url_for`
- `get_flashed_messages`

这些对象的价值在于：它们要么本身带着应用上下文，要么能通往函数的 `__globals__`。

## 一条最值得理解的主线

### 主线思路
1. 从可访问对象出发
2. 找到函数对象
3. 从函数走到 `__globals__`
4. 从 `__globals__` 拿到 `__builtins__` 或已经导入的模块
5. 继续到 `os`、`subprocess` 或文件相关能力

### 示例思路
```jinja2
{{ url_for.__globals__ }}
{{ get_flashed_messages.__globals__ }}
```

如果这一步可用，后面就有机会继续拿到：
- `__builtins__`
- `current_app`
- `os`
- `open`

## 另一条常见主线：类层级遍历

### 主线思路
1. 找到一个对象
2. 拿到它的类
3. 再拿到父类链
4. 再枚举子类
5. 从子类里挑危险类或能触达模块的类

### 典型结构
```jinja2
obj.__class__
obj.__class__.__mro__
obj.__class__.__mro__[1].__subclasses__()
```

这条线在很多 writeup 中出现，但有两个问题：
- 子类索引不稳定，不同环境位置不同。
- 过滤器常会重点拦截 `class`、`mro`、`subclasses`。

所以要理解“为什么能走到这里”，不要死背某个编号。

## 读文件的常见目标
- `/flag`
- `app.py`
- `config.py`
- 环境变量文件
- 模板源码

## 命令执行的常见目标
- `id`
- `whoami`
- `cat /flag`
- `ls /`

## 什么时候优先读文件，什么时候优先 RCE
- 题目只要求拿 flag，优先读文件，链通常更短更稳。
- 过滤较少且上下文对象丰富时，可以直接尝试命令执行。
- 无回显题里，命令执行不一定比读文件更好用，得看输出通道。

## 你应该记住的不是“最终 payload”，而是这些问题
- 我现在有哪些对象能用？
- 哪个对象能通往函数？
- 哪个函数能通往 `__globals__`？
- 当前过滤限制了哪些字符，我能不能换访问方式？

## 打法建议
- 先尝试 [[payloads/常见探测payload]] 里的短链。
- 需要继续延展时，再参考 [[payloads/Jinja2对象链速查]]。
