# -*- coding: utf-8 -*-
"""
My Notes: Test 2026/9/8
route.py - 在戶型圖 (image/map.png) 上標記「廚房」到「主臥」的行走路線。

作法：
1. 用手動測量的座標，建立房間節點與門/走道節點的圖 (graph)。
2. 用 Dijkstra 演算法在圖上尋找從「廚房」到「主臥」的最短路徑。
3. 把路徑畫成箭頭折線疊加在原圖上，並標記起點/終點，輸出成新圖片。
"""

import heapq
import math
import os

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# 路徑與輸出設定
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(BASE_DIR, "image", "map.png")
OUTPUT_PATH = os.path.join(BASE_DIR, "image", "route_kitchen_to_master_bedroom.png")

START_ROOM = "廚房"
END_ROOM = "主臥"

# ---------------------------------------------------------------------------
# 圖的節點座標 (像素座標，對應 image/map.png)
# 節點分兩種：房間中心點 (用來標記/顯示)，以及門口、走道轉折點 (用來讓路徑貼合走道與門)
# ---------------------------------------------------------------------------
NODES = {
    # 房間中心
    "廚房": (85, 175),
    "客餐廳": (190, 400),
    "次衛": (378, 185),
    "主衛": (610, 345),
    "次臥": (378, 470),
    "主臥": (565, 470),
    # 門 / 走道轉折點
    "door_廚房_客餐廳": (48, 247),      # 廚房 <-> 客餐廳 的門
    "corridor_junction": (350, 300),   # 客餐廳延伸到臥室走道的轉角
    "door_走道_次衛": (420, 245),       # 走道 <-> 次衛 的門
    "door_走道_次臥": (325, 340),       # 走道 <-> 次臥 的門
    "door_走道_玄關": (480, 340),       # 走道 <-> 主臥/主衛玄關 的門
    "foyer": (500, 380),               # 主臥/主衛前的小玄關
    "door_玄關_主衛": (575, 375),       # 玄關 <-> 主衛 的門
}

# ---------------------------------------------------------------------------
# 圖的邊 (可互通的節點對)；權重會用兩點的歐氏距離自動計算
# ---------------------------------------------------------------------------
EDGES = [
    ("廚房", "door_廚房_客餐廳"),
    ("door_廚房_客餐廳", "客餐廳"),
    ("客餐廳", "corridor_junction"),
    ("corridor_junction", "door_走道_次衛"),
    ("door_走道_次衛", "次衛"),
    ("corridor_junction", "door_走道_次臥"),
    ("door_走道_次臥", "次臥"),
    ("corridor_junction", "door_走道_玄關"),
    ("door_走道_玄關", "foyer"),
    ("foyer", "door_玄關_主衛"),
    ("door_玄關_主衛", "主衛"),
    ("foyer", "主臥"),
]


def build_graph(nodes, edges):
    """建立無向加權圖：{node: [(neighbor, weight), ...]}"""
    graph = {name: [] for name in nodes}
    for a, b in edges:
        dist = math.dist(nodes[a], nodes[b])
        graph[a].append((b, dist))
        graph[b].append((a, dist))
    return graph


def shortest_path(graph, start, end):
    """用 Dijkstra 演算法找最短路徑，回傳節點名稱組成的路徑列表。"""
    dist = {node: math.inf for node in graph}
    prev = {node: None for node in graph}
    dist[start] = 0
    queue = [(0, start)]
    visited = set()

    while queue:
        d, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        if node == end:
            break
        for neighbor, weight in graph[node]:
            new_dist = d + weight
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(queue, (new_dist, neighbor))

    if dist[end] == math.inf:
        raise ValueError(f"找不到從 {start} 到 {end} 的路徑")

    path = []
    node = end
    while node is not None:
        path.append(node)
        node = prev[node]
    path.reverse()
    return path


def load_font(size):
    """嘗試載入支援中文的字型，找不到就用預設字型。"""
    candidates = [
        r"C:\Windows\Fonts\msjh.ttc",
        r"C:\Windows\Fonts\mingliu.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_arrowhead(draw, tip, direction, size=12, fill=(230, 30, 30)):
    """在 tip 位置依 direction 方向畫一個實心三角形箭頭。"""
    angle = math.atan2(direction[1], direction[0])
    spread = math.radians(28)
    p1 = tip
    p2 = (
        tip[0] - size * math.cos(angle - spread),
        tip[1] - size * math.sin(angle - spread),
    )
    p3 = (
        tip[0] - size * math.cos(angle + spread),
        tip[1] - size * math.sin(angle + spread),
    )
    draw.polygon([p1, p2, p3], fill=fill)


def draw_route(image_path, output_path, path_nodes, nodes, start_label, end_label):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)

    points = [nodes[name] for name in path_nodes]
    line_color = (230, 30, 30)
    start_color = (30, 140, 30)
    end_color = (230, 30, 30)

    # 路線：紅色折線 + 白色外框讓線條在灰色底圖上更明顯
    draw.line(points, fill=(255, 255, 255), width=8, joint="curve")
    draw.line(points, fill=line_color, width=4, joint="curve")

    # 終點箭頭
    last_dir = (
        points[-1][0] - points[-2][0],
        points[-1][1] - points[-2][1],
    )
    draw_arrowhead(draw, points[-1], last_dir, size=14, fill=line_color)

    # 起點/終點圓點標記
    def marker(center, color, radius=8):
        x, y = center
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=color,
            outline=(255, 255, 255),
            width=2,
        )

    marker(points[0], start_color)
    marker(points[-1], end_color)

    # 文字標籤
    font = load_font(18)
    title_font = load_font(22)

    def label(pos, text, color, offset=(12, -28)):
        x, y = pos[0] + offset[0], pos[1] + offset[1]
        bbox = draw.textbbox((x, y), text, font=font)
        pad = 3
        draw.rectangle(
            [bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad],
            fill=(255, 255, 255),
            outline=color,
        )
        draw.text((x, y), text, fill=color, font=font)

    label(points[0], f"起點：{start_label}", start_color)
    label(points[-1], f"終點：{end_label}", end_color)

    title = f"{start_label} → {end_label} 路線圖"
    draw.rectangle([10, 10, 10 + len(title) * 24, 40], fill=(255, 255, 255))
    draw.text((14, 12), title, fill=(20, 20, 20), font=title_font)

    image.save(output_path)
    return output_path


def main():
    if not os.path.exists(MAP_PATH):
        raise FileNotFoundError(f"找不到地圖檔案: {MAP_PATH}")

    graph = build_graph(NODES, EDGES)
    path_nodes = shortest_path(graph, START_ROOM, END_ROOM)

    print("路線節點:", " -> ".join(path_nodes))

    output_path = draw_route(MAP_PATH, OUTPUT_PATH, path_nodes, NODES, START_ROOM, END_ROOM)
    print("已輸出標記路線圖片:", output_path)


if __name__ == "__main__":
    main()
