"""单卡大图截图 v2：把 svg 内容作为 data: URI 直接嵌入预览页，避开 file:// 协议问题。"""
import subprocess, pathlib, time, base64, re

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT  = pathlib.Path(r"G:\_06_项目代码\工作台\工作台复盘")
USER_DIR = pathlib.Path(r"C:\_tmp_edge_profile_big2")
USER_DIR.mkdir(exist_ok=True)

# 读取两张 svg 原内容，转成 base64
def to_data_uri(svg_path: pathlib.Path) -> str:
    raw = svg_path.read_text(encoding="utf-8")
    b64 = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"

bg_sparse = to_data_uri(ROOT / "assets/bg-net-sparse.svg")
bg_frame  = to_data_uri(ROOT / "assets/bg-frame-only.svg")

def page_for(bg: str | None) -> str:
    bg_css = f"#FBF7EC url({bg!r})" if bg else "#FBF7EC"
    bg_mini = bg_css  # mini 和 pcards 用同一张背景
    return f"""<!doctype html><meta charset=utf-8>
<title>背景预览</title>
<style>
:root{{--kinari:#FBF7EC;--sumi:#2C282B;--sumi-mid:#5b5252;--sumi-light:#8a7e80;--shu:#C2416B;--shu-soft:#F5DCE3;--kin:#C9A227;--kin-soft:#EDE0C0;--kami:#F0E5C9}}
html,body{{margin:0;background:#FBF7EC;color:#2C282B;font-family:serif;min-height:100vh}}
.row{{display:grid;grid-template-columns:2fr 1fr;gap:32px;max-width:1080px;margin:40px auto;align-items:start}}
.tag{{font-size:14px;color:#5b5252;margin-bottom:14px;border-left:3px solid #C2416B;padding-left:10px}}
.tag b{{font-size:17px;color:#C2416B;display:block;margin-bottom:2px;font-family:"Songti SC",serif}}
.bigcard,.minicard{{padding:10px;border:2px dashed rgba(44,40,43,.15);border-radius:14px}}
.pcard{{position:relative;background:{bg_css} no-repeat center / cover;
  border:2px solid #C9A227;border-radius:13px;padding:16px 15px 13px;
  width:360px;height:552px;display:flex;flex-direction:column;cursor:pointer;
  box-shadow:3px 3px 0 rgba(44,40,43,.16);aspect-ratio:300/460}}
.pcard::before{{content:'';position:absolute;inset:6px;border:1px solid #C2416B;opacity:.5;border-radius:8px;pointer-events:none}}
.pcard .top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}}
.pcard .stage{{font-family:serif;width:30px;height:30px;border-radius:50%;border:1.4px solid #C9A227;color:#854F0B;display:flex;align-items:center;justify-content:center;font-size:15px;background:#fff}}
.pcard .co{{font-family:serif;font-size:25px;line-height:1.25;margin-bottom:8px}}
.pcard .po{{font-size:14px;color:#5b5252;line-height:1.5;margin-bottom:14px}}
.pcard .ft{{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:14px;font-size:13px;color:#8a7e80}}
.pcard .seal svg{{display:block}}
.seal{{width:24px;height:24px}}
.mini-demo{{position:relative;background:{bg_mini} no-repeat center / cover;
  border:2px solid var(--sumi);border-radius:10px;padding:14px;width:196px;height:120px;
  display:flex;flex-direction:column;justify-content:space-between}}
.mini-demo .co{{font-family:serif;font-size:14px}}
.mini-demo .po{{font-size:12px;color:#5b5252}}
.mini-demo .meta{{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#8a7e80}}
</style>
<div class=row>
 <div><div class=tag><b>大卡（pcard）</b>单卡 360×552 满占视口，看清背景星网实际密度</div>
  <div class=bigcard><div class=pcard>
    <div class=top><span class=stage>存</span><span class=seal><svg viewBox="0 0 20 20"><circle cx=10 cy=10 r=7 fill=none stroke=#A83358 stroke-width=1.6 /><circle cx=14 cy=6 r=1.6 fill=#A83358 /></svg></span></div>
    <div class=co>拾光科技</div>
    <div class=po>前端开发工程师 · 已存 2 天</div>
    <div class=ft><span>想投 · 2 天</span><span>官网</span></div>
  </div></div>
 </div>
 <div><div class=tag><b>小卡（mini）</b>档案栅格 196×120，看看压缩后成什么样</div>
  <div class=minicard><div class=mini-demo>
    <div class=co>网易雷火</div>
    <div class=po>游戏 AI 产品 · 内推</div>
    <div class=meta><span>想投 · 2 天</span><span class=seal><svg viewBox="0 0 20 20"><circle cx=10 cy=10 r=7 fill=none stroke=#A83358 stroke-width=1.6 /><circle cx=14 cy=6 r=1.6 fill=#A83358 /></svg></span></div>
  </div></div>
 </div>
</div>
"""

def kill_edge():
    subprocess.run(["taskkill","/F","/IM","msedge.exe"], capture_output=True)

WIN = "--window-size=1280,820"
HEADLESS = "--headless=new"

variants = [
    ("a", bg_sparse,  "甲 · 精简星网（4 星 + 4 点 + 3 曲线）"),
    ("b", None,        "乙 · 彻底干净（纯 #FBF7EC，无星网）"),
    ("c", bg_frame,   "丙 · 只留框去星（一条斜虚线 + 一枚角落小月）"),
]

for key, bg, label in variants:
    html = page_for(bg)
    src = ROOT / f"_preview-{key}-inline.html"
    src.write_text(html, encoding="utf-8")
    out = OUT / f"_sakura-v4-{key}-singlecard.png"
    print(f"[snap] {label}")
    kill_edge()
    time.sleep(0.5)
    cmd = [EDGE, HEADLESS, WIN, "--disable-gpu", "--hide-scrollbars",
           f"--user-data-dir={USER_DIR}", f"--virtual-time-budget=4000",
           f"--screenshot={out}", src.as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    print(f"   size={out.stat().st_size}")

kill_edge()
print("[done]")
