```
`<?php   error_reporting(0);   highlight_file(__FILE__);   $url=$_POST['url'];   $x=parse_url($url);   if($x['scheme']==='http'||$x['scheme']==='https'){   $host=$x['host'];   if((strlen($host)<=5)){   $ch=curl_init($url);   curl_setopt($ch, CURLOPT_HEADER, 0);   curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);   $result=curl_exec($ch);   curl_close($ch);   echo ($result);   }   else{       die('hacker');   }   }   else{       die('hacker');   }   ?>` hacker
```
![[Pasted image 20260414213956.png]]
这道题将主机名/ip长度限制到5及以下
- 考虑将0.0.0.0转换成整数形式:
	- `0*256^3+0*256^2+0*256^1+0*256 = 0`
- 考虑省略IP中间的0字节，构造IPv4省略写法 `127.1`
使用这些IP形式进行注入，拿到flag。
#ip整数形式 #ip简化写法
[[ctfshow352ssrf限制localhost]]的升级版