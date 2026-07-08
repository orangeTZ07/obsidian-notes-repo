import json

nodes = [
    {
        "id": "root",
        "type": "text",
        "text": "# 二重积分：形心公式\n\n形心，通俗来说就是**几何中心**。\n想象你手里有一块**厚度均匀**的不规则木板（区域 $D$）。如果你想把它稳稳地顶在一根手指尖上，那个平衡点就是它的形心 $(\\bar{x}, \\bar{y})$！",
        "x": 0, "y": 0, "width": 400, "height": 180, "color": "1"
    },
    {
        "id": "formula-x",
        "type": "text",
        "text": "### x 坐标的形心 $\\bar{x}$\n\n$$ \\bar{x} = \\frac{\\iint_D x dxdy}{\\iint_D 1 dxdy} $$\n\n其实这就是一个**加权平均值**！",
        "x": -250, "y": 250, "width": 350, "height": 150, "color": "2"
    },
    {
        "id": "formula-y",
        "type": "text",
        "text": "### y 坐标的形心 $\\bar{y}$\n\n$$ \\bar{y} = \\frac{\\iint_D y dxdy}{\\iint_D 1 dxdy} $$\n\n和 x 完全对称。",
        "x": 250, "y": 250, "width": 350, "height": 150, "color": "2"
    },
    {
        "id": "denominator",
        "type": "text",
        "text": "### 分母是什么鬼？\n\n**分母 $\\iint_D 1 dxdy$ 就是总面积 $A$**！\n\n把木板切成了无数个面积为 $dxdy$ 的微小块，加起来当然就是总面积。",
        "x": 0, "y": 450, "width": 400, "height": 150, "color": "3"
    },
    {
        "id": "numerator",
        "type": "text",
        "text": "### 分子又是什么鬼？\n\n拿 $\\iint_D x dxdy$ 来说：\n微小块面积是 $dxdy$，它距离 y 轴的距离是 $x$。\n这两个一乘 $x \\cdot dxdy$，相当于这个小块在水平方向上的**“杠杆效应” (静矩)**。\n积分就是把所有的杠杆效应加起来！",
        "x": 0, "y": 650, "width": 400, "height": 200, "color": "4"
    },
    {
        "id": "summary",
        "type": "text",
        "text": "### 🎯 一句话总结\n\n**形心 = (所有小碎片的杠杆效应之和) $\\div$ 总面积**\n\n这和我们算平均分一样的道理：用 (分数 $\\times$ 人数) 的总和，除以总人数。",
        "x": 0, "y": 900, "width": 400, "height": 150, "color": "6"
    }
]

edges = [
    {"id": "e1", "fromNode": "root", "fromSide": "bottom", "toNode": "formula-x", "toSide": "top"},
    {"id": "e2", "fromNode": "root", "fromSide": "bottom", "toNode": "formula-y", "toSide": "top"},
    {"id": "e3", "fromNode": "formula-x", "fromSide": "bottom", "toNode": "denominator", "toSide": "top"},
    {"id": "e4", "fromNode": "formula-y", "fromSide": "bottom", "toNode": "denominator", "toSide": "top"},
    {"id": "e5", "fromNode": "denominator", "fromSide": "bottom", "toNode": "numerator", "toSide": "top"},
    {"id": "e6", "fromNode": "numerator", "fromSide": "bottom", "toNode": "summary", "toSide": "top"}
]

canvas = {"nodes": nodes, "edges": edges}

with open("/home/orange114/work/obsidian-notes-repo/高数A/形心公式图解.canvas", "w", encoding="utf-8") as f:
    json.dump(canvas, f, indent=2, ensure_ascii=False)

print("Canvas created successfully.")
