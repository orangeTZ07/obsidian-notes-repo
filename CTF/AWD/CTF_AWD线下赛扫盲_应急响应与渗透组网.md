# 御网杯线下 AWD/AWDP 扫盲：应急响应、渗透与组网

## 1. 概念引入
线下攻防赛（如御网杯）不再是单向解题，而是强调 **AWD (Attack With Defense)** 甚至 **AWDP (AWD Plus)**。你不仅要攻，还要防。

- **[AWD (Attack-Defend CTF)](https://en.wikipedia.org/wiki/Capture_the_flag#Attack-Defend)**：每个队伍初始拥有一台或多台相同的[靶机(Target Machine)](https://en.wikipedia.org/wiki/Vulnerable_machine)。你需要修补自己机器的漏洞（防御），同时利用这些漏洞去攻击其他队伍（攻击/渗透），并抓取他们的 Flag 提交得分。
- **[应急响应 (Incident Response)](https://en.wikipedia.org/wiki/Computer_security_incident_management)**：当你的机器被别人打进来了，你该怎么发现、怎么把黑客踢出去、怎么清理后门、怎么恢复业务。
- **组网 (Networking)**：线下赛的比赛网络极其复杂。你需要配置自己的路由器，将队伍内部机器连接成局域网，并与官方比赛网络互通。这还涉及到防火墙配置、流量镜像等。

---

## 2. 核心场景举例（从易到难）

### 例子1（基础）：SSH 弱口令与基础后门清理
**场景**：比赛刚开始，由于大家靶机的初始密码都一样（比如 `root/123456`），别队的脚本小子通过 SSH 疯狂登录并种下了一个 [WebShell](https://en.wikipedia.org/wiki/Web_shell)。
- **应急响应**：
  1. 发现机器里有未知文件，或者发现被扣分了。
  2. 立即修改自己机器的 SSH 密码和数据库密码。
  3. 使用 `D-Shield` 或手动去 web 目录下查找 `.php` 文件，用 `find /var/www/html -type f -mmin -30` 查找最近30分钟被修改的文件，删掉 WebShell。
- **组网/防御**：如果有硬路由控制权，在路由器直接通过 ACL 阻断外界对你们靶机 22 端口的访问（防止再被 SSH 爆破）。

### 例子2（进阶）：Java 反序列化与无文件内存马
**场景**：系统存在 Shiro 反序列化漏洞，其他队伍打入了一个无文件落地的“内存马”（Memory Shell）。你翻遍了 `/var/www/html` 也没有发现任何多余的 `.jsp` 文件，但是每轮还是在掉分！
- **应急响应**：
  1. 传统的文件查杀失效了。你需要监控到靶机存在极短的异常 CPU 波动。
  2. 使用阿里开源的 `Arthas` 工具，挂载到运行的 JVM 上：`java -jar arthas-boot.jar`。
  3. 执行 `mbean` 或者反编译查找被动态注入的恶意 Filter/Valve 类，找出内存马并 kill 掉恶意进程或重启 Web 容器。
  4. 赶紧上 WAF（Web应用防火墙）脚本，或者替换存在反序列化漏洞的包，打上 Patch。
- **渗透**：你也学会了这招，抓取别人的反序列化利用流量包，提取出 Payload，针对还没补漏洞的队伍进行批量重放攻击。

### 例子3（地狱级）：Rootkit 隐藏进程与内核级维持（坑点极多）
**场景**：对手是个内核大牛，利用内核提权漏洞拿下你的 root，并加载了一个 LKM（Linux Kernel Module）类型的 [Rootkit](https://en.wikipedia.org/wiki/Rootkit)。
- **渗透与维持**：对手通过修改内核的系统调用，将他的进程、建立的后门网络连接（比如监听 1337 端口）全部从 `ps` 和 `netstat` 命令的输出中隐藏。
- **应急响应（坑点）**：
  - **坑点1（工具欺骗）**：你输入 `netstat -antp`，什么异常都看不到。因为系统的 `/bin/netstat` 调用的内核接口已经被劫持了。你必须使用静态编译的 `busybox` 或者直接查阅 `/proc` 下的原始信息，甚至通过 `lsmod` 去排查未知的内核模块。
  - **坑点2（不可删除文件）**：对手在 `/etc/cron.d/` 下写了定时任务，当你去删除时提示 `Operation not permitted`。这是因为对手使用了 `chattr +i` 或者 `chattr +a` 给文件加了不可变属性。必须先 `lsattr` 确认，再 `chattr -i` 解锁后才能删除。
- **组网联动**：这种时候最怕对手不仅挂后门，还把你的靶机当**跳板机**去打别人，导致你疯狂背锅扣分。你在本地组网时，必须在路由器配置严格的**出站规则 (Egress Filtering)**，只允许靶机响应请求，绝对禁止靶机主动向外部其他队伍发起无关网络连接！

---

## 3. 关联知识点与拓展
搞定了以上内容，你还需要补足以下拼图：
1. **[内网横向移动 (Lateral Movement)](https://en.wikipedia.org/wiki/Lateral_movement_(cybersecurity))**：拿到一台靶机后，如何利用这台机器扫描内网其他不出网的机器？
2. **流量包分析 (PCAP Analysis)**：AWD比赛通常会给你提供本队的网络流量包。利用 Wireshark 或者编写 Python 脚本提取出其他队伍打你的流量（包含他们的 Exploit），从而实现“白嫖 Payload”。
3. **自动化攻防框架**：别人打 AWD 都是全自动的批量扫描、批量打 Patch、批量交 Flag。

---

## 4. 推荐项目与论文
针对 AWD 和实战，强烈推荐你研究以下优秀项目：
- **[AWD-Tools](https://github.com/zhl2008/awd-tools)** 或 **[AWD-Watchbird](https://github.com/DasSecurity-HatLab/Awd-Watchbird)**：专为 AWD 比赛设计的批量脚本、防御框架和轻量级 WAF。
- **[Arthas](https://github.com/alibaba/arthas)**：Java 应急响应排查内存马的神器。
- **[Goby](https://gobysec.net/)**：极其优秀的实战化漏洞扫描和资产收集工具，对于线下赛快速摸清其他队伍资产非常有帮助。
- **经典学术论文**：《*A Survey of Memory Corruption Exploits and Defenses*》。当你想明白为什么缓冲溢出、ROP能成功，你才懂得内核级别的攻防本质。

---

## 5. 随堂自测题（试着回答或思考）
1. **易**：在接手 Linux 靶机的第一分钟，如果想快速把 `/var/www/html/` 整个目录备份并压缩成一个文件，该使用什么命令？
2. **中**：如果对手的 WebShell 利用了 PHP 的 `LD_PRELOAD` 环境变量来绕过 `disable_functions`，作为防守方，在不改变应用源码的前提下，有什么最快的方法来让这个绕过手段失效？
3. **难（刁钻题）**：你发现服务器的 Redis 存在未授权访问漏洞，且确定攻击者利用它写了计划任务（Cron）。但是当你执行 `crontab -l` 以及查看 `/var/spool/cron/root` 时，屏幕上看似没有任何恶意的定时任务，文件依然只有正常的配置。请问攻击者是如何“隐藏”任务的？你该如何排查？

---
*Created by Antigravity*
