[[ctfshow351ssrf入门]]进阶版
本题代码：
```php
`<?php   error_reporting(0);   highlight_file(__FILE__);   $url=$_POST['url'];   $x=parse_url($url);   if($x['scheme']==='http'||$x['scheme']==='https'){   if(!preg_match('/localhost|127.0.0/')){   $ch=curl_init($url);   curl_setopt($ch, CURLOPT_HEADER, 0);   curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);   $result=curl_exec($ch);   curl_close($ch);   echo ($result);   }   else{       die('hacker');   }   }   else{       die('hacker');   }   ?>` hacker
```
排版有点难看，截图看看：
![[Pasted image 20260414173326.png]]
发现限制必须使用http类方案，并且不能用localhost和回环地址
**想到了0.0.0.0**
- Linux 内核在路由 `0.0.0.0` 时，会将其解析为**默认路由 / 本机**
- 更重要的是：服务端程序（如 nginx、Apache）监听时，`0.0.0.0:80` 表示**监听所有接口**，因此当 curl 请求 `http://0.0.0.0/` 时，在本机发起的请求会直接命中这个监听套接字
- **0.0.0.0 不是"被解析为回环地址"，而是在本机发起请求时，能直接到达本机上监听 0.0.0.0 的服务**，效果等同于访问本机。
- 这并不是一个标准的结果，但成功率较高

抓包，改包，把GET改成POST，加上**请求头 Content-Type: application/x-www-form-urlencoded**
在请求体里写上 `url=http://0.0.0.0/flag.php`
发包后得到flag

---
### 为什么 #不写端口也能自动获取到资源 ？

这是因为每种协议都有**默认端口**，不写端口时 cURL 会自动使用对应协议的默认值：

| 协议        | 默认端口         |
| --------- | ------------ |
| http://   | 80           |
| https://  | 443          |
| ftp://    | 21           |
| file://   | 无（本地文件，不走网络） |
| dict://   | 2628         |
| gopher:// | 70           |

所以 `http://localhost/flag.php` 实际上请求的是 `http://localhost:80/flag.php`，只是端口被省略了。
而 `file://` 协议**完全不走网络**，它直接让 cURL 读取本地文件系统，所以根本没有端口的概念。**这也是为什么 SSRF 结合 `file://` 特别危险——它绕过了所有网络层面的限制，直接读服务器本地文件。**

---
另外本题还有很多其他解：
- 把ip进行不同表示，比如纯整型，16进制，8进制....
- #回环地址的其他形式 IPv4 地址 `127.0.0.0/8` 整个 A 类段（`127.0.0.1` ~ `127.255.255.254`）在 RFC 5735 中全部被保留为回环地址，**不只是 `127.0.0.1`**。
- http://127.1/flag.php ← 127.x.x.x 整段都是回环
- http://[::1]/flag.php ← IPv6 回环
另外其实**本题没有对输入进行过滤**,所以直接 `http://127.0.0.1/flag.php` 就行