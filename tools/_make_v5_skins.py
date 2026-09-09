"""v5 变体：直接复用 sakura.html，只换 .mini/.pcard/.backcard 三段的
   background url 指向新的 bg-net-v5-{1,2}.svg（同种子不同 n）。"""
import re, pathlib

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
SRC  = ROOT / "sakura.html"

text = SRC.read_text(encoding="utf-8")
VARIANTS = {
    "v5-1": ('background:#FBF7EC url("assets/bg-net-v5-1-sparse.svg")',
             "稀疏 · n=12 · 同种子散布 · 12 sparkle + 4 polyline"),
    "v5-2": ('background:#FBF7EC url("assets/bg-net-v5-2-mid.svg")',
             "中等 · n=20 · 同种子散布 · 20 sparkle + 4 polyline"),
}

pat_re = re.compile(r'(background:\s*#FBF7EC)(?:\s+url\([^)]+\))?', re.IGNORECASE)
probe = pat_re.findall(text)
print(f"[probe] 命中 {len(probe)} 处")
out = pat_re.sub(lambda m: "<<BG>>", text)

for key, (bg, label) in VARIANTS.items():
    html = out.replace("<<BG>>", bg)
    dst = ROOT / f"sakura-{key}.html"
    dst.write_text(html, encoding="utf-8")
    # 自检：新文件中不应有 Q/curve 之外的多余曲线
    paths_curved = re.findall(r'<path[^>]*\sd="[^"]*[QCTA][^"]*"', html)
    print(f"[ok ] {dst.name} · {label} · 全文件 {len(paths_curved)} 条曲线路径（应仅 faceSVG 内的")
    print(f"       笔画星章等，不影响卡片背景）")

# 注：faceSVG (line 492) 等多处含有 card 内 SVG 路径，但都和 background 无关
# 真正影响 .mini/.pcard 背景图的只有 url() 那一段
print("[done]")
