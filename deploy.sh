#!/usr/bin/env bash
# ═══ 樱帖一键双端部署 ═══
# 一条命令发两端：GitHub Pages + 云端 101.43 服务器（9090）。
# 用法：bash deploy.sh "这次改了什么（可空）"
# 依赖：node（语法检查）、git、python + paramiko（凭据在 工作台/workspace/cloud/_secrets.py，不入库）
set -e
cd "$(dirname "$0")"

CLOUD_DIR="G:/_06_项目代码/工作台/workspace/cloud"
REMOTE="/opt/workbuddy/workspace/offer-tracker/sakura.html"
PAGES="https://whaleof.github.io/offer-tracker/sakura.html"
SRV="http://101.43.110.207:9090/sakura.html"
NOTE="${1:-樱帖更新}"

echo "── 1/5 JS 语法检查"
node -e "const m=require('fs').readFileSync('sakura.html','utf8').match(/<script>([\s\S]*)<\/script>/);try{new Function(m[1])}catch(e){console.error('✗ JS 语法错误：'+e.message);process.exit(1)}"
echo "  ✓ 语法通过"

echo "── 2/5 防密钥泄漏检查"
if grep -qE 'sk-[a-f0-9]{20,}' sakura.html README.md; then
  echo "  ✗ 检测到疑似 API 密钥，停止部署！先清掉再发"; exit 1
fi
echo "  ✓ 无密钥泄漏"

echo "── 3/5 推 GitHub"
git add sakura.html README.md deploy.sh
if ! git diff --cached --quiet; then git commit -m "deploy: $NOTE"; fi
git push origin main
echo "  ✓ GitHub 已推（Pages 约 1-2 分钟后生效）"

echo "── 4/5 部署云端 101.43（先备份旧版）"
MD5_LOCAL=$(md5sum sakura.html | cut -d' ' -f1)
python - "$MD5_LOCAL" "$REMOTE" <<'EOF'
import sys, os
sys.path.insert(0, r"G:\_06_项目代码\工作台\workspace\cloud")
from _cloud_ssh import run, put
md5_local, remote = sys.argv[1], sys.argv[2]
o, _, _ = run(f"cp {remote} {remote}.bak-deploy-$(date +%m%d-%H%M) && echo backed-up")
print("  旧版备份:", o.strip())
put("sakura.html", remote)
o, _, _ = run(f"md5sum {remote}")
md5_remote = o.split()[0] if o.strip() else ""
print("  ✓ 云端已上传，MD5 " + ("一致" if md5_remote == md5_local else "✗ 不一致！本地 %s / 远端 %s" % (md5_local, md5_remote)))
sys.exit(0 if md5_remote == md5_local else 1)
EOF

echo "── 5/5 公网验证"
sleep 1
if curl -sf -m 15 "$SRV" | grep -q "樱帖"; then echo "  ✓ 云端 9090 已是新版"; else echo "  ✗ 云端 9090 验证失败"; exit 1; fi
if curl -sf -m 15 "$PAGES" | grep -q "樱帖"; then echo "  ✓ GitHub Pages 可访问"; else echo "  ⚠ Pages 暂时没通（可能还在构建，稍后自己刷一下）"; fi

echo ""
echo "双端部署完成 ✓  $NOTE"
