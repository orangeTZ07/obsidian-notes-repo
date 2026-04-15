进入题目后看到php代码：
```
<?php  
error_reporting(0);  
highlight_file(__FILE__);  
$url=$_POST['url'];  
$ch=curl_init($url);  
curl_setopt($ch, CURLOPT_HEADER, 0);  
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);  
$result=curl_exec($ch);  
curl_close($ch);  
echo ($result);  
?>
```
### 源码解读
`error_reporting(0);` 关闭了php错误报告
`curl_init($url)` 初始化一个cURL句柄，并把url作为目标
- #句柄 是一种引用方式/一种资源标识，在这里或许可以简单理解成一个会话，但最好还是区分开
- #cURL支持的协议： `http/https,ftp,file,dict,gopher`

`curl_setopt()` 
- 题目中本段代码设置了不将响应头设置进去 `CURLOPT_HEADER = 0`
- 设置了将响应内容作为字符串返回，而非直接输出 `CURLOPT_RETURNTRANSFER = 1`
	- 这里的作用其实是防止curl直接把内容输出到浏览器，要求curl把内容赋值到 `$result` 
`curl_exec()` 执行请求

---
了解了本题如何运作后，我们尝试构造 `url=localhost/flag.php`
- 这里 `localhost/flag.php` 会被 `curl_exec()` 默认当作 `http` 处理
直接得到了flag.