"""截 sakura 三种背景变体到工作台根目录，便于 present_files 一并展示对比。"""
import subprocess, pathlib, time, urllib.parse

ROOT = pathlib.Path(r"G:\_06_项目代码\offer-tracker")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 输出放工作台根（系统默认允许的输出目录）
OUT = pathlib.Path(r"G:\_06_项目代码\工作台\工作台复盘")
OUT.mkdir(parents=True, exist_ok=True)

VARIANTS = [
    ("a", "甲-精简星网"),
    ("b", "乙-干净底"),
    ("c", "丙-留框去点"),
]

# 视口大小（用稍宽宽度，能并排显示 4-5 张卡片）
WIN = "--window-size=1280,900"
HEADLESS = "--headless=new"
USER_DIR = pathlib.Path(r"C:\_tmp_edge_profile")
USER_DIR.mkdir(exist_ok=True)
CDP_PORT = 9223

def kill_edge():
    subprocess.run(["taskkill","/F","/IM","msedge.exe"], capture_output=True)

def shot(url: str, outpath: pathlib.Path):
    cmd = [
        EDGE,
        HEADLESS,
        WIN,
        f"--disable-gpu",
        f"--hide-scrollbars",
        f"--user-data-dir={USER_DIR}",
        f"--virtual-time-budget=8000",
        f"--screenshot={outpath}",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, timeout=60)

for key, label in VARIANTS:
    src = ROOT / f"sakura-v4-{key}.html"
    # file:// URL + 示例数据 + 牌阵页 + 纵看公司视图
    url = src.as_uri() + "?demo=1&view=board&layout=co"
    out = OUT / f"_sakura-v4-{key}-co.png"
    print(f"[snap] {label} → {out.name}")
    kill_edge()
    time.sleep(0.7)
    shot(url, out)
    print(f"   size={out.stat().st_size}")

kill_edge()
print("[done]")
