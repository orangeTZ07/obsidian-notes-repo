## 用户：
```
我有点搞不清__bases__和__mro__：>>> request.**class**.**mro** (<class 'flask.wrappers.Request'>, <class 'werkzeug.wrappers.request.Request'>, <class 'werkzeug.sansio.request.Request'>, <class 'flask.wrappers.JSONMixin'>, <class 'werkzeug.wrappers.json.JSONMixin'>, <class 'object'>) # 返回为元组 >>> request.**class**.**mro**[-1] <class 'object'> >>> request.**class**.**bases** (<class 'werkzeug.wrappers.request.Request'>, <class 'flask.wrappers.JSONMixin'>) # 返回为元组 >>> request.**class**.**bases**[0].**bases**[0].**bases**[0] <class 'object'> >>> request.**class**.**base** <class 'werkzeug.wrappers.request.Request'> >>> request.**class**.**base**.**base**.**base** <class 'object'>。另外我也有些搞不懂bases[0]，我刚接触这些
```

---
## Sonnet 4.6

## `__bases__` vs `__mro__` 的区别

用你的 Flask `request` 举例来说最直观。

---

### `__bases__` —— 只看"亲爸妈"

`__bases__` 只返回**直接父类**，就是你写 `class Foo(A, B)` 时括号里的那些。

```
flask.wrappers.Request
        ↑ __bases__ 就是这两个
werkzeug...Request    flask.wrappers.JSONMixin
```

所以 `request.__class__.__bases__` 返回的正好是 `(werkzeug...Request, flask.wrappers.JSONMixin)`，就两个，不管祖先有多深。

---

### `__mro__` —— 展开整条继承链

MRO = Method Resolution Order，Python 用它来决定**找方法时按什么顺序查找**。它把整棵继承树"压平"成一条有序的列表，从自己一直追到 `object`。

```
flask.wrappers.Request
  → werkzeug.wrappers.request.Request
    → werkzeug.sansio.request.Request
      → flask.wrappers.JSONMixin
        → werkzeug.wrappers.json.JSONMixin
          → object
```

你看到的那个元组就是这个顺序。当你调用 `request.get_json()` 时，Python 就按这个顺序一个一个类去找，找到了就用。

---

### `__base__` vs `__bases__[0]`

这两个其实是**同一个东西**，`__base__` 是 `__bases__[0]` 的快捷方式，就是第一个直接父类。

所以你的两段代码结果相同，只是写法不同：

```python
# 这两行等价
request.__class__.__base__.__base__.__base__
request.__class__.__bases__[0].__bases__[0].__bases__[0]
```

都是沿着"第一个父类"一路往上爬，最终到 `object`。

---

### 一句话总结

|属性|含义|
|---|---|
|`__bases__`|直接父类（可能多个）|
|`__base__`|第一个直接父类（`__bases__[0]` 的简写）|
|`__mro__`|整条继承链展开后的有序列表|

平时查"这个类继承自谁"用 `__bases__`，查"调方法时的查找顺序"用 `__mro__`。