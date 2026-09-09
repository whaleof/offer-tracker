"""v8 终版：对 sakura 卡背景用的两种 SVG：
   - card（.pcard 用）：spark 6~8px（比 v5-1 的 10~15 小一号）
   - mini（.mini/.backcard 用）：spark 10~14px（v5-1 原版感，"小卡那个还凑合"的）
   两份同 seed=20260913 → 节点/连线位置完全一致，只有 spark 半径不同。"""
import math, pathlib

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker\assets")
ROOT.mkdir(exist_ok=True)
SEED = 20260913
W, H = 300, 460
COLOR = "#C9A227"

def mulberry32(a):
    state = [a & 0xFFFFFFFF]
    def imul(x, y):
        x = x & 0xFFFFFFFF; y = y & 0xFFFFFFFF
        r = (x * y) & 0xFFFFFFFF
        if r >= 0x80000000: r -= 0x100000000
        return r
    def nextint():
        a = state[0]
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = imul(a ^ (a >> 15), 1 | a)
        t = (t + imul(t ^ (t >> 7), 61 | t)) & 0xFFFFFFFF
        t = t ^ (t >> 14)
        state[0] = a
        if t < 0: t += 0x100000000
        return (t % (1 << 32)) / (1 << 32)
    return nextint

def spark(x, y, s, op):
    return (f'<path d="M{x:.2f},{y-s:.2f} L{x+s*0.24:.2f},{y-s*0.24:.2f} '
            f'L{x+s:.2f},{y:.2f} L{x+s*0.24:.2f},{y+s*0.24:.2f} '
            f'L{x:.2f},{y+s:.2f} L{x-s*0.24:.2f},{y+s*0.24:.2f} '
            f'L{x-s:.2f},{y:.2f} L{x-s*0.24:.2f},{y-s*0.24:.2f} Z" '
            f'fill="{COLOR}" opacity="{op:.2f}"/>')

def gen_svg(spark_lo, spark_hi, label):
    """v5-1 原算法：n=7 sparkle + 4 条 polyline（i+=3，限定最多 4 条独立折线）
       + 节点圆点。spark 大小按调用方决定。"""
    R = mulberry32(SEED)
    pts = []
    while len(pts) < 7:
        x, y = R() * W, R() * H
        if x < 12 or x > W - 12 or y < 12 or y > H - 12:
            continue
        if any(math.hypot(x - p[0], y - p[1]) < 80 for p in pts):
            continue
        pts.append((x, y))

    body = [f'  <rect width="{W}" height="{H}" fill="#FBF7EC"/>']

    # 连线：v5-1 原版 4 条独立折线
    for i in (0, 3, 6, 9):
        if i + 2 < len(pts):
            body.append(
                f'  <polyline points="{pts[i][0]:.2f},{pts[i][1]:.2f} '
                f'{pts[i+1][0]:.2f},{pts[i+1][1]:.2f} '
                f'{pts[i+2][0]:.2f},{pts[i+2][1]:.2f}" '
                f'fill="none" stroke="{COLOR}" stroke-width=".5" opacity=".26"/>'
            )

    # 节点圆点 + 7 颗 sparkle
    for x, y in pts:
        # sparkle
        s = spark_lo + R() * (spark_hi - spark_lo)
        op = 0.32 + R() * 0.18
        body.append('  ' + spark(x, y, s, op))

    body.append(f'  <!-- v8 {label} · seed={SEED}（位置/v5-1 一致；spark {spark_lo}~{spark_hi}） -->')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'preserveAspectRatio="xMidYMid slice">\n' + '\n'.join(body) + '\n</svg>\n')

# 两份 spark 大小：card=小星，mini=原版
(ROOT / "bg-card-v8.svg").write_text(gen_svg(6.0, 8.5, "card"), encoding="utf-8")
(ROOT / "bg-mini-v8.svg").write_text(gen_svg(10.0, 14.0, "mini"), encoding="utf-8")
print(f"[ok ] bg-card-v8.svg → spark 6.0~8.5px（大卡用，星小了）")
print(f"[ok ] bg-mini-v8.svg → spark 10~14px（小卡/空列用，原版感）")
