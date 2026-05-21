**不一定**，有几种情况会导致漏掉或无法利用：

### ① 沙箱删除/覆盖了 `__subclasses__`

python

```python
# 防御方可以这样做：
object.__subclasses__ = lambda self: []
# 或直接 del
del object.__subclasses__
```

### ② 类在调用时尚未被导入

`__subclasses__()` 只返回**已加载到内存**的子类。如果 `subprocess`、`os` 等模块在你触发 SSTI 的时间点还没有被任何代码 `import`，对应的类就**不会出现**在列表里。

python

```python
# 如果应用根本没有 import subprocess，列表里就没有 subprocess.Popen
```

> 这就是为什么有时候需要先"触发"某些模块加载，比如利用 `importlib` 或 `__import__` 先导入，再去扫子类。

### ③ 自定义 `__init_subclass__` 或 metaclass 干扰

某些框架会用 metaclass 管理子类注册，使得 `__subclasses__()` 的返回结果与实际不一致。

### ④ Python 版本差异

不同版本的 CPython 内置类和第三方库版本不同，子类列表的**索引会变化**。CTF 环境和真实渗透环境需要重新枚举，不能硬编码索引。

### ⑤ 真实渗透中还要考虑

- WAF 可能过滤了 `__subclasses__`、`__globals__`、`__builtins__` 等关键词 → 需要用字符串拼接、`|attr()` 过滤器、`getattr` 等绕过
- 模板引擎沙箱（如 Jinja2 的 `SandboxedEnvironment`）会限制属性访问
- 某些部署用 `seccomp` 限制了 `execve` 系统调用，即使拿到 `Popen` 也执行不了