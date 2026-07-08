import json

nodes = [
    {
        "id": "root",
        "type": "text",
        "text": "# 隐函数求导法\n\n**题目**：设 $z=z(x,y)$ 是由方程 $z+e^z=xy$ 所确定，求 $\\frac{\\partial z}{\\partial x}, \\frac{\\partial z}{\\partial y}$ 和 $\\frac{\\partial^2 z}{\\partial x^2}$.\n\n**核心本质**：方程 $F(x,y,z)=0$ 藏着一个曲面。我们没法把 $z$ 单独解出来写成 $z = f(x,y)$，但我们依然能求它的切线斜率（偏导数）。",
        "x": 0, "y": -200, "width": 500, "height": 180, "color": "1"
    },
    {
        "id": "step1-concept",
        "type": "text",
        "text": "### 第一步：大 F 登场 (构造隐函数)\n移项，把所有东西丢到方程一边，让它等于 0。\n\n令 **$F(x,y,z) = z + e^z - xy = 0$**",
        "x": -300, "y": 50, "width": 300, "height": 140, "color": "4"
    },
    {
        "id": "step1-calc",
        "type": "text",
        "text": "### 第二步：分别对 x, y, z 求导\n把 $x, y, z$ 都当成独立、平起平坐的变量去求偏导：\n\n- $F_x' = -y$ (把 y, z 当常数)\n- $F_y' = -x$ (把 x, z 当常数)\n- $F_z' = 1 + e^z$ (把 x, y 当常数)",
        "x": 50, "y": 50, "width": 350, "height": 180, "color": "4"
    },
    {
        "id": "step1-result",
        "type": "text",
        "text": "### 第三步：套用官方公式\n\n- $\\frac{\\partial z}{\\partial x} = -\\frac{F_x'}{F_z'} = -\\frac{-y}{1+e^z} = \\mathbf{\\frac{y}{1+e^z}}$\n\n- $\\frac{\\partial z}{\\partial y} = -\\frac{F_y'}{F_z'} = -\\frac{-x}{1+e^z} = \\mathbf{\\frac{x}{1+e^z}}$",
        "x": 450, "y": 50, "width": 350, "height": 160, "color": "3"
    },
    {
        "id": "step2-second-order",
        "type": "text",
        "text": "### 进阶：如何求二阶偏导 $\\frac{\\partial^2 z}{\\partial x^2}$？\n\n**致命易错点**：对 $x$ 再次求导时，**$z$ 也是 $x$ 的函数！不能把 $z$ 当常数！** 只有 $y$ 才是常数。\n\n$\\frac{\\partial}{\\partial x}(\\frac{y}{1+e^z}) = y \\cdot \\frac{\\partial}{\\partial x}[(1+e^z)^{-1}]$\n$= y \\cdot (-1)(1+e^z)^{-2} \\cdot e^z \\cdot \\mathbf{\\frac{\\partial z}{\\partial x}}$  **(注意末尾的链式法则！)**",
        "x": -100, "y": 300, "width": 550, "height": 200, "color": "5"
    },
    {
        "id": "step2-final",
        "type": "text",
        "text": "### 最终组装\n\n把刚才求出来的 $\\frac{\\partial z}{\\partial x} = \\frac{y}{1+e^z}$ 代入进去：\n\n$\\frac{\\partial^2 z}{\\partial x^2} = -y \\cdot \\frac{e^z}{(1+e^z)^2} \\cdot \\frac{y}{1+e^z} = \\mathbf{-\\frac{y^2 e^z}{(1+e^z)^3}}$\n\n大功告成！",
        "x": -100, "y": 550, "width": 400, "height": 160, "color": "6"
    }
]

edges = [
    {"id": "e1", "fromNode": "root", "fromSide": "bottom", "toNode": "step1-concept", "toSide": "top"},
    {"id": "e2", "fromNode": "step1-concept", "fromSide": "right", "toNode": "step1-calc", "toSide": "left"},
    {"id": "e3", "fromNode": "step1-calc", "fromSide": "right", "toNode": "step1-result", "toSide": "left"},
    {"id": "e4", "fromNode": "step1-result", "fromSide": "bottom", "toNode": "step2-second-order", "toSide": "top"},
    {"id": "e5", "fromNode": "step2-second-order", "fromSide": "bottom", "toNode": "step2-final", "toSide": "top"}
]

canvas = {"nodes": nodes, "edges": edges}

with open("/home/orange114/work/obsidian-notes-repo/高数A/隐函数偏导数与二阶导.canvas", "w", encoding="utf-8") as f:
    json.dump(canvas, f, indent=2, ensure_ascii=False)

print("Canvas created successfully.")
