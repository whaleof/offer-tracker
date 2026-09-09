"""为星网v4做3个skin变体：甲(精简)/乙(干净)/丙(留框去点)。
   输入：sakura.html
   输出：sakura-v4-{a,b,c}.html
   影响：仅替换 .mini/.pcard 两段 background 的 url() 段，其他不变。"""
import re, shutil, pathlib

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
SRC  = ROOT / "sakura.html"
BKP  = ROOT / "sakura.html.bak-20260909-星网v4策略调整前"
assert SRC.exists(), "找不到 sakura.html"
# 双保险：再次校验备份
assert BKP.exists() and BKP.stat().st_size == SRC.stat().st_size, "bak 与源不一致，拒绝改"

text = SRC.read_text(encoding="utf-8")

# 三种 background 片段（直接替换 .mini{} 和 .pcard{} 里的 `background:...`）
VARIANTS = {
    "a": (
        # 精简星网 → 引用外部 svg
        'background:#FBF7EC url("assets/bg-net-sparse.svg")',
        "甲 · 精简星网（保留氛围，密度降到约 1/12，曲线 + 4 星 + 4 点）",
    ),
    "b": (
        # 彻底干净 → 纯色
        "background:#FBF7EC",
        "乙 · 彻底干净（删除所有网、点、月牙，只剩 #FBF7EC 卡纸底）",
    ),
    "c": (
        # 只留框去星
        'background:#FBF7EC url("assets/bg-frame-only.svg")',
        "丙 · 只留框去星（一条斜虚线 + 一枚角落小月牙）",
    ),
}

# 用更宽容的正则匹配：background 紧跟着 #FBF7EC 后面有空格+url(...)/或者没 url
# data URI 里有特殊的：`%23C9A227` `2C326.1` 等都正常处理。
# 关键：data URL 一定以 '")' 结尾（CSS 里 url 字符串闭合）。
pat_re = re.compile(
    r'(background:\s*#FBF7EC)(?:\s+url\("data:image/svg\+xml,[^"]*"\))?',
    re.IGNORECASE
)

# 安全计数
hits = []
def _r(m):
    hits.append(m.group(0)[:60])
    return "<<BG>>"  # 占位

probe = pat_re.sub(_r, text)
print(f"[probe] background 替换命中：{len(hits)} 处")
for h in hits:
    print(f"   - {h}…")

assert len(hits) >= 2, "应至少替换 .mini 和 .pcard 两处"

# 真正替换
out = pat_re.sub(lambda m: "<<BG>>", text)

for key, (bg, label) in VARIANTS.items():
    html = out.replace("<<BG>>", bg)
    dst  = ROOT / f"sakura-v4-{key}.html"
    dst.write_text(html, encoding="utf-8")
    print(f"[ok ] {dst.name}  → {label}")

print("[done]")
