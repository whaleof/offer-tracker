# -*- coding: utf-8 -*-
"""把本地 offer-tracker/sakura.html 部署到云端 8080 服务。

背景：她平时打开的是 http://101.43.110.207:8080/offer-tracker/sakura.html
      （由服务器上的 workbuddy 服务托管），而本地 G:\\...\\offer-tracker\\sakura.html
      只是开发副本 —— 改完本地必须传上去，她那边刷新才看得到。

流程：远端备份 → 上传 → md5 双向校验 → 报云端 md5/大小。
用法：python tools/deploy_sakura.py
"""
import hashlib
import os
import sys
import time

CLOUD_DIR = r"G:\_06_项目代码\工作台\workspace\cloud"
sys.path.insert(0, CLOUD_DIR)
from _cloud_ssh import run, put, connect  # noqa: E402

LOCAL = r"G:\_06_项目代码\offer-tracker\sakura.html"
REMOTE = "/opt/workbuddy/workspace/offer-tracker/sakura.html"
STAMP = time.strftime("%Y%m%d-%H%M%S")


def md5_local(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not os.path.exists(LOCAL):
        print("本地文件不存在：", LOCAL)
        return 1
    lm = md5_local(LOCAL)
    lsize = os.path.getsize(LOCAL)
    print("本地  %s  %d bytes" % (lm, lsize))

    out, err, code = run("md5sum %s; wc -c < %s" % (REMOTE, REMOTE))
    print("部署前云端：", out.strip().replace("\n", " "))

    bak = REMOTE + ".bak-" + STAMP
    out, err, code = run('cp -a "%s" "%s" && echo BACKUP_OK' % (REMOTE, bak))
    print("远端备份：", out.strip(), bak)

    put(LOCAL, REMOTE)
    out, err, code = run("md5sum %s; wc -c < %s" % (REMOTE, REMOTE))
    print("部署后云端：", out.strip().replace("\n", " "))
    rm = out.split()[0] if out.strip() else ""
    print("MD5 一致：" + ("是 ✓" if rm == lm else "否 ✗ (本地 %s / 云端 %s)" % (lm, rm)))
    connect().close()
    return 0 if rm == lm else 2


if __name__ == "__main__":
    sys.exit(main())
