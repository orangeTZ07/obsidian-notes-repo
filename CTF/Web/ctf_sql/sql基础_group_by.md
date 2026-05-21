# 本期主角 `GROUP BY`

GROUP BY可以对数据进行分组，比如有个学生表，记录了每班学生信息。那你想统计班级平均分的时候就可以 `select class,AVG(score) from class_table group by class;`
值得注意的是，如果select 列表 里面非聚合函数字段在 `group by` 后面没有出现的话可能会造成一定混乱。
这个混乱对于初学者来讲比较难理解，很多教程也没讲清楚(主要是没抓好重点)。
我们先上实际例子，然后再深入理解：
有如图数据库表![[Pasted image 20260409175936.png]]
我们先执行语句 `select count(*) from Supplier group by creditlevel;`
![[Pasted image 20260409180141.png]]
发现 `group by` 把所有相同值的行给融合成一行了(其实到这里就已经很清晰为什么会混乱了)
然后我们执行语句 `select count(*),city from Supplier group by creditlevel;`
![[Pasted image 20260409180350.png]]
这时候可以看到城市名少了很多。
我们再执行语句 `select count(*),city,SupplierName from Supplier group by creditlevel;`
![[Pasted image 20260409180511.png]]
发现供应商也变少了
假设我们当前处于 `mysql严格模式` 我们再执行语句 `select count(*),City from Supplier group by creditlevel,City;`
![[Pasted image 20260409180643.png]]
可以看到缺失的内容又回来了(虽然被更加细分了)
再把 `creditlevel` 给调出来，对比一下之前的表： `select count(*),City,creditlevel from Supplier group by creditlevel;`
![[Pasted image 20260409185830.png]]
整个表：
![[Pasted image 20260409185948.png]]
对比之后发现**group by 在非严格模式下进行分组时，会把第一个匹配的结果的字段值当成最值返回**

其实整个内容的核心要点就在于 `group by` 会压缩返回的行，直接压缩成一行。


-----
ChatGPT是这样讲的：
```
## 一、从执行机制直观理解 `GROUP BY`

### 1. 分组的本质：从“行”到“组”

假设有如下 `employees` 表：

|id|department|name|salary|
|---|---|---|---|
|1|IT|Alice|8000|
|2|IT|Bob|9000|
|3|HR|Carol|7000|
|4|HR|Dave|7500|

执行以下 SQL：

SELECT department, COUNT(*)  
FROM employees  
GROUP BY department;

### 执行过程（逻辑层面）

1. **FROM**：读取所有行。
2. **GROUP BY department**：将数据划分为多个组：
    - IT → {Alice, Bob}
    - HR → {Carol, Dave}
3. **聚合计算**：对每个组计算 `COUNT(*)`。
4. **SELECT 输出**：每个组输出一行结果。

结果：

|department|COUNT(*)|
|---|---|
|IT|2|
|HR|2|

在这个过程中，**每个组最终只保留一行输出**，而不是原来的多行。

---

## 二、为什么“未分组的列”会产生不确定性？

现在考虑下面的查询：

SELECT department, name, COUNT(*)  
FROM employees  
GROUP BY department;

### 1. 关键矛盾

- `GROUP BY department`：意味着**每个部门只输出一行**。
- `name`：在每个部门中存在**多个可能的值**。

例如：

|department|可选的 name|
|---|---|
|IT|Alice 或 Bob|
|HR|Carol 或 Dave|

数据库此时面临一个问题：

> 对于 IT 部门，应该返回 `Alice` 还是 `Bob`？

SQL 语义中并没有任何规则来决定这一点，因此结果是**不确定的（Non-Deterministic）**。

### 2. 为什么“看起来是确定的”？

在某些情况下，你可能发现数据库**总是返回同一个 `name`**，这通常是因为：

- 数据的**物理存储顺序**；
- **索引的扫描顺序**；
- **执行计划**的选择；
- **临时表或排序算法**的实现方式。

然而，这些因素：

- **不是 SQL 语义的一部分**；
- **在不同版本或不同执行环境中可能改变**；
- **不能被开发者依赖**。

例如，以下情况都可能改变返回结果：

-- 添加索引  
CREATE INDEX idx_dept ON employees(department);  
  
-- 改变执行计划  
ANALYZE TABLE employees;  
  
-- 升级数据库版本

因此，即使结果“看起来稳定”，它在逻辑上仍然是**未定义行为**。

---

## 三、形象类比：投票代表问题

可以把 `GROUP BY` 想象成“为每个部门选一个代表”：

- `COUNT(*)`：统计每个部门的人数 —— 没有歧义。
- `AVG(salary)`：计算平均工资 —— 没有歧义。
- `name`：如果没有规则，**选谁当代表？**

如果没有明确的规则（如“工资最高的人”），那么选择就是**随机的**。为了消除这种歧义，你需要明确指定规则，例如：

-- 选择工资最高的员工  
SELECT department, name, salary  
FROM employees e1  
WHERE salary = (  
    SELECT MAX(salary)  
    FROM employees e2  
    WHERE e2.department = e1.department  
);

或者使用窗口函数：

SELECT department, name, salary  
FROM (  
    SELECT *,  
           ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) AS rn  
    FROM employees  
) t  
WHERE rn = 1;

---

## 四、MySQL 历史行为与 `ONLY_FULL_GROUP_BY`

### 1. 宽松模式（旧版本 MySQL）

在未启用 `ONLY_FULL_GROUP_BY` 时，MySQL 会：

- 从每个分组中**任意选择一行**；
- 这个选择通常是“第一行”，但**并不保证**。

SELECT department, name  
FROM employees  
GROUP BY department;

可能的结果：

|department|name|
|---|---|
|IT|Alice|
|HR|Carol|

但在另一种执行计划下，也可能变为：

|department|name|
|---|---|
|IT|Bob|
|HR|Dave|

### 2. 严格模式的作用

启用 `ONLY_FULL_GROUP_BY` 后，MySQL 会直接拒绝这种语义不明确的查询，从而：

- 保证结果的**确定性**；
- 与 SQL 标准保持一致；
- 避免潜在的逻辑错误。

---

## 五、如何消除不确定性？

### ✅ 方法 1：将列加入 `GROUP BY`

SELECT department, name, COUNT(*)  
FROM employees  
GROUP BY department, name;

此时每个 `(department, name)` 组合都是唯一的，不再存在歧义。

---

### ✅ 方法 2：使用聚合函数

SELECT department, MIN(name), COUNT(*)  
FROM employees  
GROUP BY department;

这里明确规定：选择字典序最小的 `name`。

---

### ✅ 方法 3：使用 `ANY_VALUE()`（MySQL 特有）

SELECT department, ANY_VALUE(name), COUNT(*)  
FROM employees  
GROUP BY department;

这表示：**明确接受任意值**，从而消除语义歧义。

---

### ✅ 方法 4：利用函数依赖（主键）

如果 `GROUP BY` 的字段是主键或唯一键，则其他列由其唯一确定：

SELECT id, name  
FROM employees  
GROUP BY id;  -- 合法，因为 id 唯一确定 name

---

## 六、总结：为什么会“不确定”？

|关键点|解释|
|---|---|
|分组后的结果|每个组只输出一行|
|未分组的列|在组内可能有多个候选值|
|SQL 标准|未定义应选择哪一个|
|看似稳定|依赖物理实现，而非逻辑语义|
|严格模式|防止这种不确定行为|
```