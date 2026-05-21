# ctfshow374：无回显 XXE 总览

这题的难点，不是“不会写 XXE payload”，而是**你写出来了，也没有地方把结果显示给你看**。

如果你是刚从 `ctfshow373` 过来，最容易懵的点就是：

- `373` 里，服务器会把你 XML 里的某个标签内容输出出来
- 你把 `&xxe;` 塞进那个标签，文件内容就直接显示了
- `374` 里，服务端依然会解析 XML，但**不再输出解析结果**

所以这题不是“XXE 失效了”，而是进入了 **Blind XXE（盲 XXE）** 的场景。

---

## 先看题目代码

```php
<?php
error_reporting(0);
libxml_disable_entity_loader(false);
$xmlfile = file_get_contents('php://input');
if(isset($xmlfile)){
    $dom = new DOMDocument();
    $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
}
highlight_file(__FILE__);
```

这里最关键的是两点：

- `LIBXML_NOENT`：会展开实体
- `LIBXML_DTDLOAD`：会加载 DTD

这说明：

- 外部实体仍然可以被解析
- 远程 DTD 仍然可能被拉取
- 服务端仍然可能去读文件、发请求

但是它**没有 `echo` 你的 XML 内容**，只会 `highlight_file(__FILE__)` 把源码高亮出来。

一句话理解这题：

> 解析器还在干活，只是它不把结果告诉你了。

---

## 为什么 373 的 payload 到这里不行了

你在 `373` 里常用的 payload 大概像这样：

```xml
<?xml version="1.0"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///flag">
]>
<root>
  <ctfshow>&xxe;</ctfshow>
</root>
```

这段 payload 在 `374` 里其实**很可能仍然成功读取了 `/flag`**，只是读取结果没有被打印到页面上。

也就是说：

- 不是“没读到”
- 而是“读到了，但你看不到”

这就是“无回显”的本质。

---

## 这题要换一种思路

既然页面不给你结果，就要想办法让目标服务器把结果送到**别的地方**。常见路线有三种：

### 1. [[ctfshow374OOB_HTTP外带]]

最常见、最适合入门理解的一条路。

核心思路：

- 让目标服务器先访问你放在 VPS 上的 `evil.dtd`
- 再让它把 `/flag` 的内容拼进 URL
- 最后访问你的服务器，把数据“带出来”

你在自己服务器的日志里就能看到 flag。

---

### 2. [[ctfshow374报错外带]]

如果应用会把 XML 解析错误返回出来，或者你能看到错误日志，就可以故意让解析器访问一个**不存在的路径**，并把敏感内容塞进这个路径里。

这样错误信息里就可能带出数据。

这条路线很经典，但在实际题目里要看前提是否满足。

---

### 3. [[ctfshow374本地DTD_Gadget]]

如果你不能轻松使用远程 DTD，或者想研究更进阶的 XML 解析技巧，可以尝试：

- 调用服务器上本来就存在的 DTD 文件
- 利用其中已定义的参数实体
- 做“重定义”或“拼接注入”

这类思路常被叫做 **本地 DTD Gadget**。

---

## 三种方法的区别

|方法|适合什么情况|优点|难点|
|---|---|---|---|
|[[ctfshow374OOB_HTTP外带]]|无回显，但目标能访问你的服务器|最好理解，最常见|要理解参数实体和远程 DTD|
|[[ctfshow374报错外带]]|能看到 XML 报错|不一定要自建完整回显链|依赖错误可见|
|[[ctfshow374本地DTD_Gadget]]|想绕过某些 DTD 限制，或无法方便使用远程 DTD|更灵活，偏进阶|对 DTD 机制要求更高|

---

## 推荐阅读顺序

如果你对 XML 很陌生，按这个顺序看：

1. [[xml基础]]
2. [[xxe的部分原理和利用面]]
3. [[ctfshow374xxe去除回显]]
4. [[ctfshow374无回显XXE总览]]
5. [[ctfshow374OOB_HTTP外带]]
6. [[ctfshow374报错外带]]
7. [[ctfshow374本地DTD_Gadget]]

---

## 先记住这一句

做 `ctfshow374` 时，脑子里最好一直有这句话：

> XXE 不一定非要“读出来给我看”，也可以“替我发请求”，或者“把内容塞进报错里”。

一旦你接受这个思路，这题就不会再卡在“为什么 payload 没反应”上。
