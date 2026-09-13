#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jing_fetch · 樱帖面经雷达（牛客版，仅标准库）

与岗位雷达同一分工：发现=牛客搜索接口（匿名可用）；本脚本只做抓取/去重/落盘。
读同目录 jing-config.json 里的目标公司/岗位 → 搜「公司 岗位 面经」
→ 提取标题/正文摘要/链接 → 写同目录 jing-latest.json（与 sakura.html 同目录，静态可读）。
樱帖「📡 面经雷达」按钮读这个文件；拆题由用户在樱帖里触发（AI 只抽取不编题）。
"""
import json
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent
CFG = BASE / 'jing-config.json'
OUT = BASE / 'jing-latest.json'
STATE = BASE / 'jing-state.json'
API = 'https://gw-c.nowcoder.com/api/sparta/pc/search'


def load(p, default):
    try:
        return json.loads(Path(p).read_text(encoding='utf-8'))
    except Exception:
        return default


def search(q, size):
    body = json.dumps({'type': 'all', 'query': q, 'page': 1, 'size': size, 'tag': [], 'order': ''}).encode('utf-8')
    req = urllib.request.Request(API, data=body, headers={
        'Content-Type': 'application/json;charset=utf-8', 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    cfg = load(CFG, {})
    targets = cfg.get('targets') or [{'co': '腾讯', 'role': 'AI 产品经理'}]
    per = int(cfg.get('per_query', 8))
    keep = int(cfg.get('keep', 30))
    min_len = int(cfg.get('min_content_len', 80))

    seen = set(load(STATE, {}).get('ids', []))
    fresh, seen_new = [], set()
    for t in targets:
        q = f"{t.get('co', '')} {t.get('role', '')} 面经".strip()
        try:
            d = search(q, per)
        except Exception as e:
            print(f"[warn] 搜索失败 {q}: {e}")
            continue
        recs = ((d.get('data') or {}).get('records')) or []
        got = 0
        for r in recs:
            data = r.get('data') or {}
            cd = data.get('contentData') or {}
            cid = str(cd.get('id') or '')
            content = str(cd.get('content') or '').strip()
            title = str(cd.get('title') or '').strip()
            if not cid or len(content) < min_len:
                continue
            # 牛客全文搜索相关性很松，硬过滤：公司名要么在标题里，要么正文出现 ≥3 次
            co = t.get('co', '')
            if co and (co not in title) and content.count(co) < 3:
                continue
            if cid in seen:
                continue
            entity = ((data.get('extraInfo') or {}).get('entityID_var')) or cid
            fresh.append({
                'id': cid,
                'query': q,
                'co': t.get('co', ''),
                'role': t.get('role', ''),
                'title': title or (content[:24] + '…'),
                'content': content[:2500],
                'url': f"https://www.nowcoder.com/discuss/{entity}",
                'fetchedAt': time.strftime('%Y-%m-%d %H:%M'),
            })
            seen_new.add(cid)
            got += 1
        print(f"[ok] {q} → 新 {got} 条")
        time.sleep(1)

    old_ids = {x['id'] for x in fresh}
    old = [x for x in load(OUT, {}).get('items', []) if x['id'] not in old_ids]
    items = (fresh + old)[:keep]
    OUT.write_text(json.dumps({'updatedAt': time.strftime('%Y-%m-%d %H:%M'), 'items': items},
                              ensure_ascii=False, indent=1), encoding='utf-8')
    st = load(STATE, {})
    st['ids'] = list(seen_new) + list(seen)
    st['ids'] = st['ids'][:400]
    STATE.write_text(json.dumps(st, ensure_ascii=False), encoding='utf-8')
    print(f"面经雷达：本次新抓 {len(fresh)}，在册 {len(items)} → {OUT.name}")


if __name__ == '__main__':
    main()
