"""v8 收尾：替换 sakura.html 原文（dual bg：.pcard=card版 / .mini&.backcard=mini版）。"""
import re, pathlib, shutil

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
SRC  = ROOT / "sakura.html"

# 备份（已经存在 bak-20260909-星网v4策略调整前 备份 + 再加一份本次的 bak）
BKP = ROOT / "sakura.html.bak-20260909-星网v8前"
shutil.copy2(SRC, BKP)
print(f"[bak ] {BKP.name}")

text = SRC.read_text(encoding="utf-8")
# 双重保险：检查 bak 与源一致
assert BKP.stat().st_size == SRC.stat().st_size, "bak/源 字节不一致，拒绝改"

# 把所有 data:image 嵌入的巨型 url() 整体替换为对应 url（mini / card 各一份）
# 策略：先全部替换为 <<MINI>> 占位，再回头给 .mini/.backcard 换 mini 图，给 .pcard 换 card 图
card_url = 'background:#FBF7EC url("assets/bg-card-v8.svg")'
mini_url = 'background:#FBF7EC url("assets/bg-mini-v8.svg")'

# 1) 全部替换为 <<BG>> 占位
pat = re.compile(r'(background:\s*#FBF7EC)(?:\s+url\([^)]+\))?', re.IGNORECASE)
hits = pat.findall(text)
print(f"[step1] 命中 {len(hits)} 处 → 全部 <<BG>> 占位")
text = pat.sub(lambda m: "<<BG>>", text)

# 2) 找出 .mini{} 和 .backcard{} 和 .pcard{} 段，分别换
def replace_around_class(text, cls_name, new_bg):
    """把 .clsname{...<<BG>>...} 段里的 <<BG>> 换成 new_bg。"""
    # 用反查：找 .clsname{...<<BG>>...} 段内的第一个 <<BG>>
    pattern = re.compile(r'(\.'+cls_name+r'\{[^}]*?)<<BG>>', re.DOTALL)
    return pattern.sub(lambda m: m.group(1) + new_bg, text, count=1)

text_new = text
text_new = replace_around_class(text_new, "mini",    mini_url)
text_new = replace_around_class(text_new, "backcard", mini_url)
text_new = replace_around_class(text_new, "pcard",   card_url)

# 自检：所有 <<BG>> 都该被替换完了
remaining = text_new.count("<<BG>>")
print(f"[step2] 剩余 <<BG>> 占位：{remaining}（应为 0）")
assert remaining == 0, "有 <<BG>> 没替换掉"

# 写回 sakura.html 主文件
SRC.write_text(text_new, encoding="utf-8")
print(f"[ok ] sakura.html 已替换为 v8 终版（card={card_url.count('card')} / mini={mini_url.count('mini')}）")

# 自检：grep bak / 新版，对比 bg 数
print(f"[verify] bak 大小={BKP.stat().st_size} → v8 大小={SRC.stat().st_size}")
import subprocess
r = subprocess.run(["grep", "-c", "bg-card-v8.svg", str(SRC)], capture_output=True, text=True)
print(f"[verify] sakura.html 含 bg-card-v8.svg: {r.stdout.strip()} 处")
r = subprocess.run(["grep", "-c", "bg-mini-v8.svg", str(SRC)], capture_output=True, text=True)
print(f"[verify] sakura.html 含 bg-mini-v8.svg: {r.stdout.strip()} 处")
