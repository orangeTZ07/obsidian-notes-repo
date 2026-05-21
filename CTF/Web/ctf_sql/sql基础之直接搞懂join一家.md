
#用on代替where
我们先从最基础的 `inner join` 下手
`inner join` 可以将两个表拼接在一起，并且由 `on` 来判断其中是否有符合要求的条目
```
SELECT u.name, o.order_id
FROM Users u
INNER JOIN Orders o ON u.user_id = o.user_id;
```
`right join` 就是把左表拼到右表，保留右表所有行
```
SELECT u.name, COUNT(o.order_id) AS order_count
FROM Users u
RIGHT JOIN Orders o ON u.user_id = o.user_id
GROUP BY u.name;
```
`left join` 就是把右表拼到左表，保留左表所有行

那如果 `left join` 时行数量不匹配呢？
- ![[Pasted image 20260409204150.png]]
- 假如说右表匹配行比左表少，那么少的部分就会补null
	- ![[Pasted image 20260409204615.png]]
- 假如说左表匹配行比右表少，那么为了完整保留左表，就会对左表进行扩充，并且尝试对右表缺失条目补null

还有一个高级玩法，叫 `self join`
- 该玩法必须给本表取别名，强制把它表示成两个不相同的表
- ![[Pasted image 20260409210017.png]]

**right join很有用，强制保留右表可能会把左表一些别人不想展示给你的行给匹配出来**
**另外一个join好用的点就是on,可以作为条件判断来代替where**
在[[ctfshow184sql过滤与爆破]]中 `right join`被用来改变整张表的匹配行数，以此来构造布尔盲注

另外一个好用的特性，如图：
![[Pasted image 20260409220053.png]]
具体参考笛卡尔积（离散数学还是好有用啊（感叹））