# Jinja2 对象链速查

> 这页是“思路速查”，不是保证环境通杀的万能链。重点看每条链在做什么。

## 入口对象优先级
1. `config`
2. `request`
3. `url_for`
4. `get_flashed_messages`
5. `self`
6. `cycler` / `joiner` / `namespace`

## 常见探路 payload
```jinja2
{{ url_for.__globals__ }}
{{ get_flashed_messages.__globals__ }}
{{ request.application }}
{{ config.items() }}
```

## 常见桥接目标
- `__globals__`
- `__builtins__`
- `current_app`
- `os`
- `open`

## 类层级遍历思路
```jinja2
{{ ''.__class__ }}
{{ ''.__class__.__mro__ }}
{{ ''.__class__.__mro__[1].__subclasses__() }}
```

## 读文件方向
- 目标文件：
  - `/flag`
  - `/app/app.py`
  - `/proc/self/environ`
- 思路：
  - 找能到 `open` 的路径
  - 或找到可用文件类

## 命令执行方向
- 目标命令：
  - `id`
  - `whoami`
  - `cat /flag`
- 思路：
  - 找 `os.popen`
  - 找 `subprocess`
  - 找能间接执行命令的工具对象

## 绕过时的替代动作
- `obj.attr` 换 `obj|attr("attr")`
- 敏感属性名拆分后拼接
- 先拿短对象，再局部展开

## 使用提醒
- 子类索引不稳定，不要把编号当常量。
- 如果一条链太长，拆成多步测试，确认死在哪一层。
