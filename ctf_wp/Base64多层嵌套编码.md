[[ctfshow_web应用安全与防护核心节点]]
### 这道题考察加密链，考察爆破
![[Pasted image 20260410213350.png]]
进去之后先尝试对前端进行修改，尝试直接绕过前端，但是发现没有作用。
可能是因为前端这个只是为了展示加密逻辑吧，后端还有一套代码在进行相同逻辑处理。
那么现在也许就只能乖乖解密了
我先让AI把代码部署到了我本地，以此来减少对ctfshow网站的资源消耗，同时加快破解速度。

题目详细代码：
```
document.getElementById('loginForm').addEventListener('submit', function(e) { const correctPassword = "SXpVRlF4TTFVelJtdFNSazB3VTJ4U1UwNXFSWGRVVlZrOWNWYzU="; function validatePassword(input) { let encoded = btoa(input); encoded = btoa(encoded + 'xH7jK').slice(3); encoded = btoa(encoded.split('').reverse().join('')); encoded = btoa('aB3' + encoded + 'qW9').substr(2); return btoa(encoded) === correctPassword; } const enteredPassword = document.getElementById('password').value; const messageElement = document.getElementById('message'); if (!validatePassword(enteredPassword)) { e.preventDefault(); messageElement.textContent = "Login failed! Incorrect password."; messageElement.className = "message error"; } });
```

---

首先尝试对 `correctPassword` : `SXpVRlF4TTFVelJtdFNSazB3VTJ4U1UwNXFSWGRVVlZrOWNWYzU=` 进行处理：
- 对 `encoded = btoa('aB3' + encoded + 'qW9').substr(2);` 尝试还原
	- 这段代码先给encoded加上前后缀，然后去掉了前边两个字符
	- 发现需要在前面补两个字符，补充后对 `correctPassword` 进行解base64，然后去掉aB3和qW9(这两个字符可以验证解密正确性)
	- 假设处理后得到decoded1
- 对 `encoded = btoa(encoded.split('').reverse().join(''));` 尝试还原
	- 这串代码是先将encoded结果拆分成字符数组，然后对字符数组进行反向，然后再把反向后的字符数组连成字符串
	- 将decoded1进行反向，得到decoded2
- 对 `encoded = btoa(encoded + 'xH7jK').slice(3);` 尝试还原
	- 这段代码的处理逻辑是对base64加密后的字符串加上后缀xH7jk然后去掉前面三个字符
	- 对decoded2前方补充三个字符，然后进行base64解密，然后去掉末尾的xH7jk(这段数字可以用来验证解密正确性)
	- 处理后得到decoded3
- 对 `let encoded = btoa(input);` 尝试还原
	- 这段代码是对input进行了一次base64加密
	- 直接对decoded3进行base64解密
初步估计整个流程可能需要2份爆破脚本
```
import subprocess
import base64

passwd = "abc"
cmd = "curl http://127.0.0.1:3000/test?input={}".format(passwd)
correctPassword = "SXpVRlF4TTFVelJtdFNSazB3VTJ4U1UwNXFSWGRVVlZrOWNWYzU="


def boom1():
    for a in range(32, 127):
        for b in range(32, 127):
            mix = chr(a) + chr(b)
            coPa = mix + correctPassword
            decoded = base64.b64encode(coPa.encode()).decode()
            if decoded[0:3] == "aB3" and decoded[-3:] == "qW9":
                return decoded
    exit("boom1 Not found")


def boom2(decoded):
    for a in range(32, 127):
        for b in range(32, 127):
            for c in range(32, 127):
                mix = chr(a) + chr(b) + chr(c)
                coPa = mix + correctPassword
                decoded = base64.b64encode(coPa.encode()).decode()
                if decoded[-5:] == "xH7jk":
                    return decoded
    exit("boom2 Not found")


decoded1 = boom1()
decoded1 = decoded1[2:-3]
decoded2 = decoded1[::-1]
decoded3 = boom2(decoded2)
decoded3 = decoded3[0:-5]

decoded_final = base64.b64decode(decoded3).decode()
print(decoded_final)
run = subprocess.run(cmd.format(decoded_final), shell=True, capture_output=True)
print(run.stdout.decode())
```
解密失败，审查之后发现是开头少了一层base64编码，整个解密思路在最开始时就少了个关键环节。
我们把base64解密加到第一步
```
import subprocess
import base64

passwd = "abc"
cmd = "curl http://127.0.0.1:3000/test?input={}".format(passwd)
correctPassword = "SXpVRlF4TTFVelJtdFNSazB3VTJ4U1UwNXFSWGRVVlZrOWNWYzU="


def boom1(decoded):
    for a in range(32, 127):
        for b in range(32, 127):
            mix = chr(a) + chr(b)
            coPa = mix + decoded
            decoded_t = base64.b64encode(coPa.encode()).decode()
            if decoded_t[0:3] == "aB3" and decoded_t[-3:] == "qW9":
                return decoded_t
    exit("boom1 Not found")


def boom2(decoded):
    for a in range(32, 127):
        for b in range(32, 127):
            for c in range(32, 127):
                mix = chr(a) + chr(b) + chr(c)
                coPa = mix + decoded
                decoded_t = base64.b64encode(coPa.encode()).decode()
                if decoded_t[-5:] == "xH7jk":
                    return decoded_t
    exit("boom2 Not found")


decoded0 = base64.b64encode(correctPassword.encode()).decode()
decoded1 = boom1(decoded0)
decoded1 = decoded1[2:-3]
decoded2 = decoded1[::-1]
decoded3 = boom2(decoded2)
decoded3 = decoded3[0:-5]

decoded_final = base64.b64decode(decoded3).decode()
print(decoded_final)
run = subprocess.run(cmd.format(decoded_final), shell=True, capture_output=True)
print(run.stdout.decode())

```
结果还是错误，让AI帮忙改一下代码：
```
import base64
import itertools
import subprocess

correctPassword = "SXpVRlF4TTFVelJtdFNSazB3VTJ4U1UwNXFSWGRVVlZrOWNWYzU=".strip()


# 正向加密函数（完全模拟前端 validatePassword）
def validatePassword(input_str):
    # Step 1
    encoded = base64.b64encode(input_str.encode()).decode()
    # Step 2
    encoded = base64.b64encode((encoded + "xH7jK").encode()).decode()[3:]
    # Step 3
    encoded = base64.b64encode(encoded[::-1].encode()).decode()
    # Step 4
    encoded = base64.b64encode(("aB3" + encoded + "qW9").encode()).decode()[2:]
    # Step 5 (最终比较)
    return base64.b64encode(encoded.encode()).decode() == correctPassword


# Base64 字符集
B64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")

# 可打印 ASCII
PRINTABLE = set(chr(i) for i in range(32, 127))

# Step 5 解码
step4_output = base64.b64decode(correctPassword).decode("utf-8")
print(f"[Step5] step4_output = {step4_output}")

found = []
count = 0

# 穷举 Step 4 前缀 (2 字符)
for a in range(32, 127):
    for b in range(32, 127):
        prefix4 = chr(a) + chr(b)
        full4 = prefix4 + step4_output
        try:
            decoded4 = base64.b64decode(full4).decode("utf-8")
            if decoded4.startswith("aB3") and decoded4.endswith("qW9"):
                step3_b64 = decoded4[3:-3]
                try:
                    rev_str = base64.b64decode(step3_b64).decode("utf-8")
                    step2_frag = rev_str[::-1]
                    if not all(c in B64_CHARS for c in step2_frag):
                        continue
                    # 穷举 Step 2 前缀 (3 字符)
                    for c, d, e in itertools.product(range(32, 127), repeat=3):
                        prefix2 = chr(c) + chr(d) + chr(e)
                        full2 = prefix2 + step2_frag
                        try:
                            decoded2 = base64.b64decode(full2).decode("utf-8")
                            if decoded2.endswith("xH7jK"):
                                step1_b64 = decoded2[:-5]
                                try:
                                    password_bytes = base64.b64decode(step1_b64)
                                    password = password_bytes.decode("utf-8")
                                    if all(ch in PRINTABLE for ch in password):
                                        count += 1
                                        # 正向验证
                                        if validatePassword(password):
                                            found.append(password)
                                            print(
                                                f"\n✅ Correct password found: {password}"
                                            )
                                            print(
                                                f"   Step4 prefix: {prefix4}, Step2 prefix: {prefix2}"
                                            )
                                except:
                                    continue
                        except:
                            continue
                except:
                    continue
        except:
            continue

print(f"\nTotal candidates checked: {count}")
print(f"Correct passwords found: {len(found)}")

if len(found) == 1:
    real_password = found[0]
    # 执行 curl
    cmd = f"curl http://127.0.0.1:3000/test?input={real_password}"
    run = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print("\nCurl stdout:")
    print(run.stdout)
else:
    print("No unique correct password found. Check encryption logic or character sets.")
```
最后爆出来570个正确密码，几乎全部可以正常使用
碰撞这么多的原因可能在于频繁切片导致信息丢失

最后输入正确密码后按照新页面提示改一下user-agent就行

最后纠结了一下我的代码，发现我错误原因是：
- 不会写base64编码/解码，由于时间有限，直接随便抄了网上代码，导致全反了
- python字符串切片没有很搞明白
- 检查条件写错大小写
但是现在AI时代了，谁还手写代码？？