[[ctfshow_web应用安全与防护核心节点]]

### TLS 密钥日志 + PCAP 抓包题

这类题的典型特征是同时给你两样东西：

- 一个抓包文件，比如 `xxx.pcap` / `xxx.pcapng`
- 一个密钥日志文件，比如 `sslkey.log` / `keylog.txt`

如果你看见 `sslkey.log` 里是这种格式：

```text
CLIENT_HANDSHAKE_TRAFFIC_SECRET ...
CLIENT_TRAFFIC_SECRET_0 ...
SERVER_HANDSHAKE_TRAFFIC_SECRET ...
SERVER_TRAFFIC_SECRET_0 ...
EXPORTER_SECRET ...
```

那基本就不是让你去爆破 TLS，也不是让你分析证书，而是让你直接用这个密钥日志把抓包里的 HTTPS 流量解出来。

---

### 先判断这题是不是这一类

拿到题目目录后，先做最小化侦察：

```bash
file *
strings -a *.pcap | head
sed -n '1,20p' sslkey.log
```

如果出现下面这些信号，就基本可以直接定类：

- `pcap capture file`
- `sslkey.log` 是纯文本
- 日志里有 `CLIENT_TRAFFIC_SECRET_0` / `SERVER_TRAFFIC_SECRET_0`
- 抓包里有 `443` 端口通信

像我这次看到的样子就是：

- `target..pcap` 是标准 pcap 文件
- `sslkey.log` 是 TLS 1.3 key log
- 流量只有一组本地 `127.0.0.1:48908 -> 127.0.0.1:443`

这已经足够说明题目的核心是“解密 HTTPS 会话内容”，不是 Web 漏洞利用本身。

---

### 这个文件到底是干什么用的

`sslkey.log` 不是私钥文件，也不是证书文件。

它是浏览器、客户端或测试环境导出的 TLS 会话密钥日志。只要抓包中的 TLS 握手与这个日志匹配，Wireshark 或 tshark 就能直接把加密的 HTTPS 还原成明文 HTTP。

也就是说：

- `target..pcap` 负责提供网络流量
- `sslkey.log` 负责提供解密所需的会话密钥

两者配合后，你就能直接看到：

- HTTP 请求路径
- 请求参数
- Cookie
- POST body
- 响应内容
- 可能藏着 flag、口令、接口返回、跳转提示

---

### 最常用的做法：Wireshark

直接打开抓包：

```bash
wireshark target..pcap
```

然后在 Wireshark 里配置 key log 文件：

1. `Edit` -> `Preferences`
2. 打开 `Protocols` -> `TLS`
3. 在 `(Pre)-Master-Secret log filename` 里选择 `sslkey.log`
4. 确认后重新加载抓包

如果配置成功，原本看不懂的 TLS Application Data 就会被解析出明文 HTTP。

这时候重点看：

- `http`
- `tls`
- `Follow TCP Stream`
- `Follow HTTP Stream`

最常见的拿 flag 路径有几种：

- 请求参数里直接带 flag
- 某个响应包返回了 flag
- 返回页面提示你继续访问某个路径
- 登录请求里泄露口令，后续再去访问目标页面

---

### 命令行做法：tshark

如果你不想开图形界面，可以直接用 `tshark`：

```bash
tshark -r target..pcap -o tls.keylog_file:sslkey.log
```

只看 HTTP：

```bash
tshark -r target..pcap -o tls.keylog_file:sslkey.log -Y http
```

看请求方法、主机和路径：

```bash
tshark -r target..pcap \
  -o tls.keylog_file:sslkey.log \
  -Y http.request \
  -T fields \
  -e http.request.method \
  -e http.host \
  -e http.request.uri
```

看响应内容时，可以先筛：

```bash
tshark -r target..pcap -o tls.keylog_file:sslkey.log -Y http.response
```

如果要进一步提取对象，也可以在 Wireshark 里用：

- `File` -> `Export Objects` -> `HTTP`

---

### 实战思路

做这种题时，不要一上来就盯着 TLS 细节。正确思路通常是：

1. 先确认有没有配套 key log
2. 直接尝试解密 HTTPS
3. 解密后按普通 Web 流量分析
4. 关注响应里的提示、跳转、接口返回和认证信息

很多题目外表看起来像“Web 安全题”，但给了 `sslkey.log` 之后，真正考点已经变成“你知不知道怎么恢复 HTTPS 明文”。

---

### 常见坑

#### 1. 把 `sslkey.log` 当成证书或私钥

这是最常见误区。  
它不是 `server.key`，不是 `pem`，不用配到证书位置，也不用 `openssl rsa` 去读。

#### 2. 明明有 key log，但还是看不到明文

优先检查：

- 抓包和 `sslkey.log` 是否是一套对应数据
- 路径是不是配错了
- Wireshark 是否重新加载了 pcap
- 过滤器是不是把包过滤没了

#### 3. 解密出来后还在盯着 TLS 包

一旦解密成功，后面就应该把它当普通 HTTP 题来做，重点转到：

- URL
- 参数
- Header
- Cookie
- Body
- 响应内容

#### 4. 只看请求，不看响应

很多 flag、密码、下一步提示都在响应正文里，不在请求里。

---

### 看到这种目录时的标准操作

目录类似这样：

```text
target..pcap
sslkey.log
web4.zip
```

可以直接这样理解：

- `web4.zip` 多半只是打包附件
- 真正有用的是 `target..pcap` 和 `sslkey.log`
- 题目目标通常是还原 HTTPS 中的 Web 交互内容

第一步可以直接做：

```bash
unzip -l web4.zip
file target..pcap sslkey.log
sed -n '1,20p' sslkey.log
```

第二步直接进 Wireshark 配 key log。

---

### 可以直接复用的排查命令

```bash
file *
strings -a target..pcap | head
sed -n '1,20p' sslkey.log
```

如果本机有 tshark：

```bash
tshark -r target..pcap -o tls.keylog_file:sslkey.log
tshark -r target..pcap -o tls.keylog_file:sslkey.log -Y http
tshark -r target..pcap -o tls.keylog_file:sslkey.log -Y http.request -T fields -e http.host -e http.request.uri
```

---

### 一句话总结

这类题本质上是：

**题目已经把 HTTPS 的门钥匙给你了，你的任务不是破门，而是开门进去看明文。**

以后只要在题目附件里同时看到 `pcap` 和 `sslkey.log`，就优先想到：

**Wireshark + TLS key log 解密。**
