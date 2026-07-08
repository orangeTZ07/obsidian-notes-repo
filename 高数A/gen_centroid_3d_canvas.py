import json

nodes = [
    {
        "id": "root",
        "type": "text",
        "text": "# 三重积分：三维形心公式\n\n刚才我们搞定了“平面薄板”的平衡点，现在我们升级到**三维空间的立体物体**（区域 $\\Omega$）！\n想象你手里拿着一个密度均匀的实心土豆🥔，你想用一根很细的针在内部顶住它的中心点，让它在空间里达到完美的平衡，这个点就是**三维形心 $(\\bar{x}, \\bar{y}, \\bar{z})$**！",
        "x": 0, "y": 0, "width": 450, "height": 220, "color": "1"
    },
    {
        "id": "formula-x",
        "type": "text",
        "text": "### x 坐标的形心 $\\bar{x}$\n\n$$ \\bar{x} = \\frac{\\iiint_\\Omega x dxdydz}{\\iiint_\\Omega 1 dxdydz} = \\frac{\\iiint_\\Omega x dV}{V} $$\n\n仍然是加权平均！只是从二重积分变成了三重积分。($dV = dxdydz$ 就是体积微元)",
        "x": -300, "y": 300, "width": 350, "height": 180, "color": "2"
    },
    {
        "id": "formula-y",
        "type": "text",
        "text": "### y, z 坐标的形心 (同理)\n\n$$ \\bar{y} = \\frac{\\iiint_\\Omega y dV}{V} $$\n$$ \\bar{z} = \\frac{\\iiint_\\Omega z dV}{V} $$\n\n三个方向完全对称，只需要换掉分子里的字母即可。",
        "x": 300, "y": 300, "width": 350, "height": 180, "color": "2"
    },
    {
        "id": "denominator",
        "type": "text",
        "text": "### 积分分母代表什么？\n\n分母 $\\iiint_\\Omega 1 dxdydz$ 就是整个土豆的**总体积 $V$**！\n\n把土豆切成了无数个像骰子一样的微小立方体，每个体积是 $dV$，全加起来自然就是总体积。",
        "x": 0, "y": 550, "width": 400, "height": 180, "color": "3"
    },
    {
        "id": "numerator",
        "type": "text",
        "text": "### 积分分子代表什么？\n\n拿 $\\iiint_\\Omega x dV$ 来说：\n这次“重”的不再是面积，而是每个微小立方体的**体积 $dV$**。\n它距离 yz 坐标面的距离是 $x$。\n两者相乘 $x \\cdot dV$，就是这个小立方体在 x 方向上的**杠杆效应** (体积对坐标面的静矩)。\n三重积分就是把所有这些小立方体的杠杆效应加起来！",
        "x": 0, "y": 780, "width": 450, "height": 220, "color": "4"
    },
    {
        "id": "summary",
        "type": "text",
        "text": "### 🎯 学长/老师的“一句话秘籍”\n\n不管是一维的线段、二维的面、还是三维的体，形心公式的本质永远是：\n**对应的“杠杆效应”之和 $\\div$ 对应的“总量 (长度/面积/体积)”**\n\n做期末题的时候，分母通常可以直接用几何公式（如球体积公式）算，甚至不用积分！分子则是老老实实算三重积分。",
        "x": 0, "y": 1050, "width": 450, "height": 200, "color": "6"
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

with open("/home/orange114/work/obsidian-notes-repo/高数A/三维形心公式图解.canvas", "w", encoding="utf-8") as f:
    json.dump(canvas, f, indent=2, ensure_ascii=False)

print("3D Canvas created successfully.")
