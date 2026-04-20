# PHP Filter Chain RCE

## 这是什么

`php://filter` 不只是拿来读源码。

在存在文件包含漏洞，但又：

- 不能上传文件
- 不能写日志投毒
- 不能直接用 `data://` / `php://input`

时，可以尝试 **filter chain**，让 PHP 在 `include()` 读取流的过程中，经过一连串 filter 变换，最终在内存里“拼”出一段 PHP 代码，再交给 Zend Engine 执行，从而拿到 RCE。

这类题本质上还是：

```php
include($_GET['file']);
```

只是利用点从“包含现成文件”变成了“构造一个会在读取过程中变成 PHP 代码的流”。

可以先配合阅读：[[fopen与include]]

---

## 和普通 `php://filter` 读源码的区别

最常见的 `php://filter` 用法是：

```php
php://filter/convert.base64-encode/resource=index.php
```

它的目标是：

- 把源码转成 base64
- 让 `include` 读到的内容不再是合法 PHP
- 最终以纯文本形式回显

而 **filter chain RCE** 的目标正好相反：

- 经过多轮编码/转码/清洗
- 让流中的最终结果变成一段合法 PHP
- 再被 `include` 编译执行

一句话概括：

```text
源码读取：想办法让内容“不像 PHP”
RCE：想办法让内容“最后变成 PHP”
```

---

## 利用前提

通常需要满足下面几条：

- 存在可控的 `include` / `require` / `include_once` / `require_once`
- 目标环境支持 `php://filter`
- 目标环境有 `iconv` 相关转换能力可用
- 没有更简单的利用链，比如文件上传、日志投毒、`data://` 直接包含

典型场景：

```php
<?php
include($_GET['file']);
```

攻击者虽然不能直接让 `file` 指向一句话木马文件，但可以传入一个超长的 `php://filter/...` 链。

---

## 核心原理

filter chain RCE 的关键，不是“某一个神奇 filter”，而是下面三件事叠加：

### 1. `php://filter` 支持链式处理

PHP 可以把多个 filter 串起来，前一个输出作为后一个输入：

```text
php://filter/filter1|filter2|filter3/resource=xxx
```

或者写成：

```text
php://filter/read=filter1|filter2|filter3/resource=xxx
```

所以我们可以把一段原始流，反复做：

- 编码
- 解码
- 字符集转换
- 垃圾字符清洗

---

### 2. 某些 `iconv` 转换会引入稳定前缀

`convert.iconv.A.B` 并不总是“老老实实只做字符集转换”。

某些编码在转换时会带上固定前导字节、状态切换字节或 escape sequence。攻击者利用的就是这种“额外产物”。

也就是说，某些 filter 在处理数据时，会：

- 不仅转换原内容
- 还额外吐出一些可预测字节

这些字节本身未必是我们最终想要的 PHP 代码，但可以作为后续构造材料。

---

### 3. `base64` 编解码可以当“筛子”用

这类链子里经常反复出现：

- `convert.base64-encode`
- `convert.base64-decode`

原因不是为了“加密”，而是为了“清洗”和“保留目标字符集”。

实践里可以把它理解成：

- 先通过某次 `iconv` 变换制造一些新字符
- 再经过 base64 编码，把内容拉回到可控字符集
- 再通过下一轮变换继续制造目标字符
- 最后在某一轮 `base64-decode` 后，真正落成 PHP 代码

所以它不是一次性变出 `<?php ... ?>`，而是：

```text
制造一点 -> 清洗一下 -> 再制造一点 -> 再清洗一下 -> ...
```

最终把目标 payload 的 **base64 形式** 一点点拼出来，最后整体解码。

---

## 为什么最后能执行

因为 `include()` 的流程是：

```text
include()
  -> 打开 php://filter 流
  -> 按顺序经过全部 filters
  -> 得到最终字节流
  -> 交给 Zend Engine 解析
  -> 如果结果是合法 PHP，就执行
```

所以攻击者真正要做的是：

```text
控制“最终输出给 include 的字节流”
```

只要最终流内容是：

```php
<?php system($_GET['cmd']); ?>
```

那就已经不是“文件读取”了，而是标准 RCE。

---

## 常见 payload 结构

真实链子通常会非常长，手写基本不现实。结构上大致类似：

```text
php://filter/
convert.iconv.UTF8.CSISO2022KR|
convert.base64-encode|
convert.iconv.UTF8.UTF7|
...很多轮 iconv/base64 组合...|
convert.base64-decode
/resource=php://temp
```

几个观察点：

- 前面是大量 `iconv + base64` 组合
- 最后往往会落一个 `base64-decode`
- `resource` 常见是 `php://temp`

这里的 `php://temp` 不是重点，重点是：

- 给 filter 链一个“可以被打开的流”
- 真正重要的内容由前面的 filters 在处理中构造出来

---

## 一个更容易理解的抽象过程

假设目标是生成：

```php
<?php phpinfo(); ?>
```

filter chain 做的事可以抽象为：

1. 先找办法制造出某些稳定字节
2. 通过多轮变换，只保留对 base64 有意义的字符
3. 慢慢拼出这段代码对应的 base64 字符串
4. 在最后一轮做 `base64-decode`
5. `include` 看到的最终内容就成了真正的 PHP 代码

所以利用思路不是：

```text
“我找到一个 filter，直接变成一句话木马”
```

而是：

```text
“我用很多 filter，逐步把目标 payload 的 base64 结果构造出来”
```

---

## CTF 里的标准利用姿势

### 1. 先确认是包含点，不是单纯读取点

如果是：

```php
echo file_get_contents($_GET['file']);
```

那你需要的是读文件思路，不是 RCE。

如果是：

```php
include($_GET['file']);
```

才值得考虑 filter chain RCE。

---

### 2. 先排除更简单的利用链

优先检查：

- 能不能直接 `data://`
- 能不能 `php://input`
- 能不能上传文件后包含
- 能不能 session/log 临时文件包含
- 能不能 `pearcmd` / `phar` / 临时文件打链

filter chain RCE 的优势是 **无需落地文件**，但缺点是 payload 很长、调试麻烦，所以通常是“别的路都不好走”时再上。

---

### 3. 用生成器，不要手搓

这类链子通常直接用现成生成器，比如常见的 `php_filter_chain_generator`。

思路一般是：

- 指定你想执行的 PHP 代码
- 工具自动帮你生成一串极长的 `php://filter/...`
- 把结果塞进包含参数里

例如目标代码常见会写成：

```php
<?php system($_GET['cmd']); ?>
```

然后请求类似：

```text
/?file=<超长filter链>&cmd=id
```

---

## 为什么 payload 往往长得离谱

因为它不是“编码一次”这么简单，而是：

- 一次次制造可用字符
- 一次次过滤掉无关字符
- 一次次把当前结果拉回可继续利用的状态

目标 payload 越长，最终 filter 链通常也越长。

所以实战里常见优化是：

- 尽量缩短执行代码
- 先用 `phpinfo();`、`system($_GET[0]);` 这种极短 payload 验证
- 成功后再换更实用的命令执行代码

例如：

```php
<?php system($_GET[0]);?>
```

通常比：

```php
<?php system($_GET['cmd']); ?>
```

更适合先验证可用性。

---

## 常见坑点

### 1. 这是 `include` 利用，不是任意读利用

如果目标代码根本不会执行包含内容，而只是读取并回显，那这条链就打不到 RCE。

---

### 2. 依赖环境差异

不同 PHP 版本、不同编译选项、不同 `iconv` 实现，可能导致：

- 某些 charset 不可用
- 某些转换结果不稳定
- 生成器产出的链在目标环境失效

所以“本地能跑”不代表“远端一定能跑”。

---

### 3. 长度限制

链子很长，容易撞上：

- URL 长度限制
- WAF 关键字拦截
- Web 服务器对请求行长度的限制

这也是为什么它更多出现在 CTF 和高可控环境里。

---

### 4. 过滤器名字和顺序不能乱

这个利用极其依赖顺序。

同一组 filter：

- 顺序不同
- 中间少一个
- 最后一轮 decode 提前或延后

都可能导致最终结果不是合法 PHP。

---

## 和其他文件包含 RCE 手法的关系

可以把它放到这张图里理解：

### 传统文件包含 RCE

- 上传一句话木马后 `include`
- 日志投毒后 `include`
- session 投毒后 `include`
- `/proc/self/environ` 污染后 `include`

特点：**先想办法把 PHP 代码写进某个文件，再包含**

### Filter chain RCE

- 不依赖真实文件落地
- 直接在“读取流的过程中”构造代码

特点：**代码不是提前存在的，而是在 filter 处理后才出现**

这也是它最值得记住的地方。

---

## 记忆版总结

### 一句话本质

```text
利用 php://filter 的链式变换能力，在 include 读流时动态合成 PHP 代码，并交给 Zend Engine 执行。
```

### 关键词

- `include`
- `php://filter`
- `convert.iconv`
- `convert.base64-encode`
- `convert.base64-decode`
- 动态构造 payload
- 无文件落地 RCE

### 看到题目时的触发条件

如果你看到：

- 明显的文件包含点
- 不能上传文件
- 不能轻松日志投毒
- 又允许使用 `php://filter`

就该想到：**这题可能要上 php filter chain RCE。**

---

## 实战建议

做题时建议按这个顺序判断：

1. 先确认 sink 是不是 `include`
2. 再测有没有更短的包含链能直接拿代码执行
3. 没有的话，再考虑 filter chain
4. 先生成最短 payload 验证能否执行
5. 成功后再换成真正的命令执行 payload

不要一上来就硬怼超长链子，否则调试成本会很高。

---

## 一个最短工作流模板

```text
发现 include 可控
  -> 测试 data:// / php://input / 上传包含 / 日志投毒
  -> 都不顺
  -> 确认 php://filter 可用
  -> 用生成器为 `<?php system($_GET[0]);?>` 生成链
  -> 请求 `?file=<chain>&0=id`
  -> 成功后切换成更稳定的命令执行方式
```

---

## 参考理解

如果要把这一类题彻底搞懂，最值得理解的不是“某条具体链”，而是下面两点：

- `include()` 读到的不是原始文件，而是 **filters 处理后的最终流**
- 攻击者不是在“找现成 PHP 文件”，而是在“制造最终会被当成 PHP 的字节流”

一旦这两点想清楚，filter chain RCE 就不会再显得像玄学。
