这道题很奇怪，似乎是环境有问题。
题目代码：
```php
<?php  
  
/*  
# -*- coding: utf-8 -*-  
# @Author: h1xa  
# @Date:   2021-01-07 12:59:52  
# @Last Modified by:   h1xa  
# @Last Modified time: 2021-01-07 15:23:51  
# @email: h1xa@ctfer.com  
# @link: https://ctfer.com  
  
*/  
  
error_reporting(0);  
libxml_disable_entity_loader(false);  
$xmlfile = file_get_contents('php://input');  
if(preg_match('/<\?xml version="1\.0"/i', $xmlfile)){  
    die('error');  
}  
if(isset($xmlfile)){    $dom = new DOMDocument();    $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);  
}  
highlight_file(__FILE__);
```
按理说直接用[[OOB套装]]，在xml声明的 `xml`字样后面加上两个空格，或者修改版本号为1.1就行。但奇怪的是，这样做似乎会导致解析失败。
所以我们采用另一种战术：
- 采用[[OOB套装]]并删除xml声明
参考：[[为什么去掉xml声明也能正常解析]]