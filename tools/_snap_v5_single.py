"""对 v5 两档 sakura html 做单卡大图截图，便于看清背景的实际效果。"""
import subprocess, pathlib, time

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
OUT  = pathlib.Path(r"G:\_06_项目代码\工作台\工作台复盘")
USER_DIR = pathlib.Path(r"C:\_tmp_edge_profile_v5")
USER_DIR.mkdir(exist_ok=True)

# 直接 inline base64 来保证 file:// 协议下读取稳定（参考上次 _preview-*.html 套路）
import base64
def bg_data_uri(svg_path):
    svg = svg_path.read_text(encoding="utf-8")
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"

def make_preview(key, svg_path):
    bg_uri = bg_data_uri(svg_path)
    return f"""<!doctype html><meta charset=utf-8>
<title>v5 单卡预览 · {key}</title>
<style>
:root{{--kinari:#FBF7EC;--sumi:#2C282B;--sumi-mid:#5b5252;--sumi-light:#8a7e80;--shu:#C2416B;--shu-soft:#F5DCE3;--kin:#C9A227;--kin-soft:#EDE0C0;--kami:#F0E5C9;--serif:"Songti SC",serif}}
html,body{{margin:0;background:#FBF7EC;color:#2C282B;font-family:serif;min-height:100vh}}
.row{{display:grid;grid-template-columns:2fr 1fr;gap:32px;max-width:1080px;margin:40px auto;align-items:start}}
.tag{{font-size:14px;color:#5b5252;margin-bottom:14px;border-left:3px solid #C2416B;padding-left:10px}}
.tag b{{font-size:17px;color:#C2416B;display:block;margin-bottom:2px;font-family:"Songti SC",serif}}
.pc{{padding:10px;border:2px dashed rgba(44,40,43,.15);border-radius:14px}}
.pcard{{position:relative;background:#FBF7EC url("{bg_uri}") no-repeat center / cover;
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
.mini-demo{{position:relative;background:#FBF7EC url("{bg_uri}") no-repeat center / cover;
  border:2px solid var(--sumi);border-radius:10px;padding:14px;width:196px;height:120px;
  display:flex;flex-direction:column;justify-content:space-between}}
.mini-demo .co{{font-family:serif;font-size:14px}}
.mini-demo .po{{font-size:12px;color:#5b5252}}
.mini-demo .meta{{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#8a7e80}}
</style>

<div class=row>
 <div>
  <div class="tag"><b>大卡（pcard）</b>单卡 360×552 满占视口 · 看 v4 算法在卡片里的实际呈现</div>
  <div class="pc"><div class="pcard">
    <div class="top"><span class="stage">存</span><span class="seal"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7" fill="none" stroke="#A83358" stroke-width="1.6"/><circle cx="14" cy="6" r="1.6" fill="#A83358"/></svg></span></div>
    <div class="co">拾光科技</div>
    <div class="po">前端开发工程师 · 已存 2 天</div>
    <div class="ft"><span>想投 · 2 天</span><span>官网</span></div>
  </div></div>
 </div>
 <div>
  <div class="tag"><b>档案小卡</b>196×120，看压缩后成什么样</div>
  <div class="pc"><div class="mini-demo">
    <div class="co">网易雷火</div>
    <div class="po">游戏 AI 产品 · 内推</div>
    <div class="meta"><span>想投 · 2 天</span><span class="seal"><svg viewBox="0 0 20 20"><circle cx="10" cy="10" r="7" fill="none" stroke="#A83358" stroke-width="1.6"/><circle cx="14" cy="6" r="1.6" fill="#A83358"/></svg></span></div>
  </div></div>
 </div>
</div>
"""

def kill_edge():
    subprocess.run(["taskkill","/F","/IM","msedge.exe"], capture_output=True)

WIN = "--window-size=1280,820"
HEADLESS = "--headless=new"

for key, svg_name in [("v5-1", "bg-net-v5-1-sparse.svg"), ("v5-2", "bg-net-v5-2-mid.svg")]:
    svg_path = ROOT / "assets" / svg_name
    html = make_preview(key, svg_path)
    pv = ROOT / f"_preview-{key}.html"
    pv.write_text(html, encoding="utf-8")
    out = OUT / f"_sakura-{key}-singlecard.png"
    print(f"[snap] {key} → {out.name}")
    kill_edge()
    time.sleep(0.6)
    cmd = [EDGE, HEADLESS, WIN, "--disable-gpu", "--hide-scrollbars",
           f"--user-data-dir={USER_DIR}", f"--virtual-time-budget=4000",
           f"--screenshot={out}", pv.as_uri()]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)
    print(f"   size={out.stat().st_size}")

kill_edge()
print("[done]")
