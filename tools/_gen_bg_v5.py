"""用 v4 的 mulberry32+scatter 算法（同种子散布+近邻连线）生成两张
无任何 Q/curve 的稀疏 SVG，专门给 sakura 卡背景用。两档密度让她挑。"""
import math, pathlib

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker\assets")
ROOT.mkdir(exist_ok=True)
SEED = 20260913  # 与 v4'net3'同款同种子 → 改大小不变位置
W, H = 300, 460
COLOR = "#C9A227"  # 樱花主金

def mulberry32(a):
    """标准 Mulberry32 伪随机，外部同样的 a 同样序列。
       JS 的 `Math.imul(x,y)` 是 32-bit 有符号乘法，这里手写保证一致。"""
    state = [a & 0xFFFFFFFF]

    def imul(x, y):
        # 32-bit 有符号乘法（取低 32 位，按有符号回正）
        x = x & 0xFFFFFFFF
        y = y & 0xFFFFFFFF
        r = (x * y) & 0xFFFFFFFF
        if r >= 0x80000000:
            r -= 0x100000000
        return r

    def nextint():
        a = state[0]
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = (t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF
        t = t ^ (t >> 14)
        state[0] = a
        if t < 0:
            t += 0x100000000
        return (t % (1 << 32)) / (1 << 32)
    return nextint

def spark(x, y, s, op):
    # s 改为 8~14 px（相对 300x460 viewBox），放大到 360x552 卡片上 ≈10~17px，
    # 这样 sparkle 是真的"8 角星"而非"看不清的小点"
    return (f'<path d="M{x:.2f},{y-s:.2f} L{x+s*0.24:.2f},{y-s*0.24:.2f} '
            f'L{x+s:.2f},{y:.2f} L{x+s*0.24:.2f},{y+s*0.24:.2f} '
            f'L{x:.2f},{y+s:.2f} L{x-s*0.24:.2f},{y+s*0.24:.2f} '
            f'L{x-s:.2f},{y:.2f} L{x-s*0.24:.2f},{y-s*0.24:.2f} Z" '
            f'fill="{COLOR}" opacity="{op:.2f}"/>')

def gen_svg(n_spark, n_node, label, n_lines=4, line_step=3,
            spark_lo=4.0, spark_hi=6.0,
            node_r=0.9, node_op=0.20, line_op=0.20, line_w=0.45):
    """「有逻辑的星网」= v4 原版连线逻辑（i+=3，少数几条独立折线）
       + 星点减到 2~3 颗且极小 + 线更细更淡。

       为什么之前"纯乱"：之前用 i+=2 把所有节点串成贯穿全卡的长折线，
       看起来就是随机乱画的线。v4 原版是 i+=3 且只画 4 条互不相连的
       独立折线 —— 短线、成组、有星座感，那才是"有逻辑"。
    """
    R = mulberry32(SEED)
    pts = []
    while len(pts) < n_node:
        x = R() * W
        y = R() * H
        if x < 10 or x > W - 10 or y < 10 or y > H - 10:
            continue
        if any(math.hypot(x - p[0], y - p[1]) < 52 for p in pts):
            continue
        pts.append((x, y))

    body = [f'  <rect width="{W}" height="{H}" fill="#FBF7EC"/>']

    # ① 连线网：v4 原版逻辑 —— 少数几条独立折线（互不串成一大片）
    i = 0
    drawn = 0
    while drawn < n_lines and i + 2 < len(pts):
        body.append(
            f'  <polyline points="{pts[i][0]:.2f},{pts[i][1]:.2f} '
            f'{pts[i+1][0]:.2f},{pts[i+1][1]:.2f} '
            f'{pts[i+2][0]:.2f},{pts[i+2][1]:.2f}" '
            f'fill="none" stroke="{COLOR}" stroke-width="{line_w}" opacity="{line_op}"/>'
        )
        i += line_step
        drawn += 1

    # ② 节点：极淡小圆点（只是"星点"的暗示，不是星星）
    for x, y in pts:
        body.append(
            f'  <circle cx="{x:.2f}" cy="{y:.2f}" r="{node_r}" '
            f'fill="{COLOR}" opacity="{node_op}"/>'
        )

    # ③ 星点（陪衬）：只挑 n_spark 个，且很小
    step = max(1, len(pts) // max(1, n_spark))
    spark_idx = [k * step for k in range(n_spark) if k * step < len(pts)]
    for idx in spark_idx:
        x, y = pts[idx]
        s = spark_lo + R() * (spark_hi - spark_lo)
        op = 0.30 + R() * 0.12
        body.append('  ' + spark(x, y, s, op))

    body.append(
        f'  <!-- {label} · seed={SEED}, 节点={len(pts)}, 折线={drawn}条, '
        f'星点={len(spark_idx)}颗 · v4 原版连线逻辑（独立折线，不串成一片） -->'
    )
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
           f'preserveAspectRatio="xMidYMid slice">\n' + '\n'.join(body) + '\n</svg>\n')
    return svg

def gen_svg_cached(n):
    # 让多档 SVG 都用同一文件位置 → 这样所有卡片都引用同一张图
    pass

# A：n_node=10 + 3 条独立折线 + 3 小星 —— 星座图式（节点稀疏、线条独立、有逻辑）
A = gen_svg(n_spark=3, n_node=10, label="v8-A · 10节点/3折线/3小星",
            n_lines=3, line_step=3)
# B：更克制：n_node=8 + 2 条折线 + 2 小星
B = gen_svg(n_spark=2, n_node=8,  label="v8-B · 8节点/2折线/2小星",
            n_lines=2, line_step=3, line_op=0.16, line_w=0.4)

(ROOT / "bg-net-v5-1-sparse.svg").write_text(A, encoding="utf-8")
(ROOT / "bg-net-v5-2-mid.svg").write_text(B, encoding="utf-8")
print(f"[ok ] A = 10节点 / 3条折线 / 3小星(4~6px) / 线 0.45px@0.20")
print(f"[ok ] B = 8节点 / 2条折线 / 2小星(4~6px) / 线 0.40px@0.16")

# 双重自检：解析两档看是否真的没有 Q/curve/Arc/Quadratic 任何曲线
for fname in ("bg-net-v5-1-sparse.svg", "bg-net-v5-2-mid.svg"):
    text = (ROOT / fname).read_text(encoding="utf-8")
    bad = [k for k in ["Q", "C", "A ", "Z " + ".", "cubic", "quadratic"] if k in text]
    # 注意 'A' 单字符会误报；改为"path d="不以"Q"/"C"/"T"开头
    import re
    paths = re.findall(r'<path[^>]*\sd="[^"]+"', text)
    bad_paths = [p for p in paths if re.search(r'd="[^"]*[QCTA][^"]*"', p)]
    lines = [l for l in text.split("\n") if l.strip().startswith("<polyline")]
    print(f"[check] {fname}: {len(paths)} paths({len(bad_paths)} curved), {len(lines)} polylines")
    assert len(bad_paths) == 0, f"{fname} 含曲线！"
print("[done]")
