## 注意事项
> 尽量不要出现中文路径
> 有些脚本基于python编写，可能需要给bp装Jython环境
### 请求相关

	HTTPHeadModifier(自动化变形请求头)
	 FakeIP(配合回环地址很好用)

### 自动化生成脚本

	 copy as python-requests
	 copy as go-requests

### 自动化漏洞挖掘

	 jsonp hunter  xss的一个分支（现在xss特别难挖）

### 敏感信息匹配

	 HAE 匹配一些规则字符串，来发现疑似漏洞或信息泄露的内容（会直接在HTTP history里标记）

### 绕过访问限制

	 403 bypass

### 美化

	 sharpener