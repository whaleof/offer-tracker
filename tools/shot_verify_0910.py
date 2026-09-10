#!/usr/bin/env python3
"""改后验证截图（2026-09-10）：一司一牌 / 月历自动记 / 卡片底部瘦身
用造好的多岗位 + 阶段推进历史数据，验证 9.10 三处改动。
用法: 先起静态服务 8891，再 python tools/shot_verify_0910.py
"""
import asyncio, json, base64, urllib.request, os, time
from urllib.parse import quote
import websockets

CDP = 'http://localhost:9333'
BASE = 'http://127.0.0.1:8891/sakura.html'
OUT = r'G:/_06_项目代码/offer-tracker/素材图/预览图-底图'
os.makedirs(OUT, exist_ok=True)

J = []
def job(i, co, role, ch, city, status, hist, **kw):
    j = {'id': i, 'company': co, 'role': role, 'channel': ch, 'city': city,
         'status': status, 'resume': '通用版', 'salary': '', 'next': '', 'notes': '',
         'events': [], 'history': [{'status': s, 'at': a} for s, a in hist]}
    j.update(kw)
    J.append(j)

URL = '校招官网 job.xiaohongshu.com/campus'
job('j1', '小红书', '产品经理（AI Coding · AI 应用）', URL, '北京/上海', 'applied',
    [('pool', '2026-09-07T10:00:00Z'), ('applied', '2026-09-08T10:00:00Z')],
    createdAt='2026-09-07T10:00:00Z', appliedAt='2026-09-08')
job('j2', '小红书', '产品经理培训生（RPT · 社区产品）', URL, '上海/北京', 'pool',
    [('pool', '2026-09-08T10:00:00Z')], createdAt='2026-09-08T10:00:00Z')
job('j3', '小红书', '产品经理培训生（RPT · 商业产品）', URL, '上海/北京', 'pool',
    [('pool', '2026-09-08T10:00:00Z')], createdAt='2026-09-08T10:00:00Z')
job('j4', '小红书', 'AI 产品设计师', URL, '上海', 'pool',
    [('pool', '2026-09-08T10:00:00Z')], createdAt='2026-09-08T10:00:00Z')
job('j5', '小红书', '产品经理培训生（RPT · AI 产品）', URL, '上海/北京', 'pool',
    [('pool', '2026-09-08T10:00:00Z')], createdAt='2026-09-08T10:00:00Z')
job('j6', '腾讯', 'AI 产品经理（2027 校招）', '官网', '', 'applied',
    [('pool', '2026-09-08T09:00:00Z'), ('applied', '2026-09-08T10:00:00Z')],
    createdAt='2026-09-08T09:00:00Z', appliedAt='2026-09-08')
job('j7', '腾讯', 'AI 产品经理培训生（WorkBuddy 生态策略）', '官网', '', 'applied',
    [('pool', '2026-09-05T09:00:00Z'), ('applied', '2026-09-05T10:00:00Z')],
    createdAt='2026-09-05T09:00:00Z', appliedAt='2026-09-05', deadline='2026-09-10')
job('j8', 'DeepSeek', 'AI 产品经理', 'Moka/BOSS', '杭州/北京', 'applied',
    [('pool', '2026-09-07T09:00:00Z'), ('applied', '2026-09-08T10:00:00Z'),
     ('test', '2026-09-10T09:30:00Z')],
    createdAt='2026-09-07T09:00:00Z', appliedAt='2026-09-08')
job('j9', '智谱', 'AI 产品经理', '官网', '北京', 'applied',
    [('pool', '2026-09-06T09:00:00Z'), ('applied', '2026-09-08T10:00:00Z')],
    createdAt='2026-09-06T09:00:00Z', appliedAt='2026-09-08')
job('j10', '蚂蚁集团', 'AI 产品经理', '校招官网 talent.antgroup.com', '杭州', 'pool',
    [('pool', '2026-09-10T09:00:00Z')], createdAt='2026-09-10T09:00:00Z')
job('j11', '字节跳动', 'AI 产品经理 / 前端开发工程师', '校招官网 jobs.bytedance.com/campus',
    '杭州/上海/北京', 'interview',
    [('pool', '2026-09-06T09:00:00Z'), ('applied', '2026-09-07T10:00:00Z'),
     ('test', '2026-09-09T09:00:00Z'), ('interview', '2026-09-10T09:00:00Z')],
    createdAt='2026-09-06T09:00:00Z', appliedAt='2026-09-07')

DATA = {'version': 1, 'jobs': J}
TASKS = [('fix-flow', 'flow'), ('fix-co', 'co'), ('fix-cal', 'cal')]


def http_json(url, method='GET'):
    req = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


async def wait_for(ws, ids, timeout=20):
    res = {}
    deadline = asyncio.get_event_loop().time() + timeout
    while ids and asyncio.get_event_loop().time() < deadline:
        try:
            msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
            if msg.get('id') in ids:
                res[msg['id']] = msg
                ids.discard(msg['id'])
        except asyncio.TimeoutError:
            pass
    return res


async def ev(ws, mid, expr):
    await ws.send(json.dumps({'id': mid, 'method': 'Runtime.evaluate',
                              'params': {'expression': expr, 'returnByValue': True}}))
    r = await wait_for(ws, {mid}, timeout=12)
    return r.get(mid, {}).get('result', {}).get('result', {}).get('value')


async def main():
    t = http_json(CDP + '/json/new?' + quote(BASE + '?t=' + str(int(time.time() * 1000)), safe=''),
                  method='PUT')
    try:
        async with websockets.connect(t['webSocketDebuggerUrl'], max_size=None) as ws:
            await ws.send(json.dumps({'id': 1, 'method': 'Page.enable'}))
            await ws.send(json.dumps({'id': 2, 'method': 'Runtime.enable'}))
            await wait_for(ws, {1, 2})
            await asyncio.sleep(2)
            payload = json.dumps(json.dumps(DATA, ensure_ascii=False))
            await ev(ws, 10, "localStorage.setItem('job-tracker-v1'," + payload +
                             ");location.hash='p-board';location.reload();1")
            await asyncio.sleep(3.5)
            await ws.send(json.dumps({'id': 12, 'method': 'Emulation.setDeviceMetricsOverride',
                                      'params': {'width': 1300, 'height': 1500,
                                                 'deviceScaleFactor': 2, 'mobile': False}}))
            await wait_for(ws, {12})
            await asyncio.sleep(1.2)
            n = await ev(ws, 13, "(typeof JOBS!=='undefined')?JOBS.length:0")
            print('JOBS =', n)

            for name, v in TASKS:
                await ev(ws, 20, "document.querySelector('#vt span[data-v=\"%s\"]').click();1" % v)
                await asyncio.sleep(1.2)
                await ev(ws, 21, "var r=document.getElementById('p-board').getBoundingClientRect();"
                                 "window.scrollBy(0,r.top-74);1")
                await asyncio.sleep(1.0)
                await ws.send(json.dumps({'id': 30, 'method': 'Page.captureScreenshot',
                                          'params': {'format': 'png', 'fromSurface': True}}))
                res = await wait_for(ws, {30}, timeout=30)
                if 30 not in res:
                    print('FAIL', name, res.get(30))
                    continue
                data = base64.b64decode(res[30]['result']['data'])
                p = os.path.join(OUT, name + '.png')
                open(p, 'wb').write(data)
                print('OK  %-10s %s  %dKB' % (name, p, len(data) // 1024))
    finally:
        try:
            urllib.request.urlopen(urllib.request.Request(CDP + '/json/close/' + t['id'])).read()
        except Exception:
            pass


if __name__ == '__main__':
    asyncio.run(main())
