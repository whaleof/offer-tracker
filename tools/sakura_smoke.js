/* 樱花帖改动的行为验证：最小 DOM 垫片 + 两遍加载
   第一遍 ?demo 拿到示例数据；第二遍关掉 demo（location.search 为空 + 预置 localStorage），
   这样 mut() 的写入路径才真正被执行。

   用法（改完 sakura.html 必跑）：
     node tools/sakura_smoke.js sakura.html
   覆盖：三视图渲染不报错 / 公司视图分组折叠 / 月历可拖可接 /
        状态任意改 + 回退 / 月历拖拽改投出日并同步 history / 直接改公司岗位名。
   本机跑不了真浏览器（Chrome 在沙箱里起不来），所以 UI 视觉层留给用户实测。 */
const fs = require('fs');
const vm = require('vm');

class El {
  constructor(tag) {
    this.tagName = tag || 'div';
    this._html = '';
    this.textContent = '';
    this.value = '';
    this.src = '';
    this.dataset = {};
    this.children = [];
    this.style = new Proxy({}, { get: (t, k) => (k in t ? t[k] : ''), set: (t, k, v) => { t[k] = v; return true; } });
    const s = new Set();
    this.classList = {
      add: (...c) => c.forEach(x => s.add(x)),
      remove: (...c) => c.forEach(x => s.delete(x)),
      toggle: (c, f) => { f ? s.add(c) : s.delete(c); },
      contains: c => s.has(c),
    };
  }
  get innerHTML() { return this._html; }
  set innerHTML(v) { this._html = String(v); }
  setAttribute() {} getAttribute() { return null; }
  appendChild(x) { this.children.push(x); return x; }
  addEventListener() {} removeEventListener() {}
  querySelector() { return null; } querySelectorAll() { return []; }
  closest() { return null; } focus() {} click() {} remove() {}
  insertAdjacentHTML() {} scrollIntoView() {}
}

function makeCtx(search, seed) {
  const els = {};
  const document = {
    getElementById: id => (els[id] || (els[id] = new El('div'))),
    createElement: t => new El(t),
    querySelector: () => null,
    querySelectorAll: () => [],
    head: new El('head'), body: new El('body'), documentElement: new El('html'),
    addEventListener() {},
  };
  const _ls = new Map();
  if (seed) _ls.set('job-tracker-v1', seed);
  const localStorage = {
    getItem: k => (_ls.has(k) ? _ls.get(k) : null),
    setItem: (k, v) => _ls.set(k, String(v)),
    removeItem: k => _ls.delete(k),
  };
  const g = {
    document, localStorage,
    location: { search, hash: '', protocol: 'file:', hostname: '', origin: 'file://', href: 'file:///x', pathname: '/' },
    fetch: () => Promise.resolve({ json: () => Promise.resolve({}) }),
    confirm: () => true, alert: () => {}, setTimeout, clearTimeout, console, URLSearchParams,
    requestAnimationFrame: fn => setTimeout(fn, 0),
    navigator: { userAgent: 'node' },
    atob: s => Buffer.from(s, 'base64').toString('binary'),
    btoa: s => Buffer.from(s, 'binary').toString('base64'),
  };
  g.window = g; g.self = g; g.globalThis = g;
  g.addEventListener = () => {}; g.removeEventListener = () => {};
  vm.createContext(g);
  return g;
}

const html = fs.readFileSync(process.argv[2], 'utf8');
const script = html.match(/<script[^>]*>([\s\S]*?)<\/script>/)[1];
const out = [];

/* 第一遍：示例模式，取样例数据 */
let g1 = makeCtx('?demo', null);
let err1 = null;
try { vm.runInContext(script, g1, { filename: 'p1.js' }); } catch (e) { err1 = e; }
if (err1) { console.log('第一遍加载 ERR: ' + err1.message + '\n' + err1.stack); process.exit(1); }
const seed = vm.runInContext('JSON.stringify(REAL)', g1);
out.push('第一遍(?demo) OK · 示例牌 ' + JSON.parse(seed).jobs.length + ' 张');

/* 第二遍：真实模式（无 demo），用示例数据预置 localStorage */
let g2 = makeCtx('', seed);
let err2 = null;
try { vm.runInContext(script, g2, { filename: 'p2.js' }); } catch (e) { err2 = e; }
if (err2) { console.log('第二遍加载 ERR: ' + err2.message + '\n' + err2.stack); process.exit(1); }
const run = js => vm.runInContext(js, g2);
out.push('第二遍(真实模式) OK · JOBS=' + run('JOBS.length') + ' DEMO=' + run('DEMO'));

/* 1. 三视图渲染 */
for (const v of ['flow', 'cal', 'co']) {
  try {
    run(`view=${JSON.stringify(v)};renderBoard();`);
    out.push(`[视图] ${v}: OK, html=${run("document.getElementById('board').innerHTML.length")}`);
  } catch (e) { out.push(`[视图] ${v}: ERR ${e.message}`); }
}
/* 2. 公司视图分组 + 折叠 */
try {
  run("view='co';renderBoard();");
  const h = run("document.getElementById('board').innerHTML");
  out.push('[公司] 分组数=' + (h.match(/class="co-sec"/g) || []).length
    + ' 含已投出=' + /co-sec-title">已投出/.test(h)
    + ' 含未投=' + /co-sec-title">未投（想投）/.test(h));
  run("toggleCoGroup('sent')");
  const h2 = run("document.getElementById('board').innerHTML");
  out.push('[公司] 点组头可收起=' + /co-sec-body" style="display:none"/.test(h2) + ' 箭头变▶=' + /co-sec-arrow">▶/.test(h2));
  run("toggleCoGroup('sent')");
  // 折叠状态在重渲染后保持
  const h3 = run("renderBoard();document.getElementById('board').innerHTML");
  out.push('[公司] 收起态可恢复=' + !/co-sec-body" style="display:none"/.test(h3));
} catch (e) { out.push('[公司] ERR ' + e.message); }

/* 3. 月历：条目可拖 + 格子可接 */
try {
  run("view='cal';renderBoard();");
  const h = run("document.getElementById('board').innerHTML");
  out.push('[月历] 可拖条目=' + (h.match(/cal-it [a-z]+" draggable="true"/g) || []).length
    + ' 可接格子=' + (h.match(/ondrop="calDropItem\(event,'\d{4}-\d{2}-\d{2}'\)"/g) || []).length
    + ' 带data-cls=' + /data-cls="(ap|ddl|ev|pg|win|lose)"/.test(h));
} catch (e) { out.push('[月历] ERR ' + e.message); }

/* 4. 状态修改：直接改成落樱，再回退 */
try {
  const before = run('JOBS.find(j=>j.id==="d2").st');
  run("setStatus('d2','fallen')");
  const mid = run('JOBS.find(j=>j.id==="d2").st');
  const rawMid = run('REAL.jobs.find(j=>j.id==="d2").status');
  const histLen = run("REAL.jobs.find(j=>j.id==='d2').history.length");
  run("setStatus('d2','sent')");
  const back = run('REAL.jobs.find(j=>j.id==="d2").status');
  out.push(`[状态] ${before}→落樱=${mid}(raw=${rawMid}) history+1=${histLen > 2} 回退→${back}`);
} catch (e) { out.push('[状态] ERR ' + e.message); }

/* 5. 月历拖拽改投出日（含 history 同步） */
try {
  run("view='cal';renderBoard();");
  const oldAp = run('REAL.jobs.find(j=>j.id==="d2").appliedAt');
  const newDate = '2026-09-10';
  run(`_calDrag={id:'d2',cls:'ap',date:'${oldAp}',label:'投出'};calDropItem({preventDefault(){},currentTarget:document.getElementById('x')},'${newDate}');`);
  const newAp = run('REAL.jobs.find(j=>j.id==="d2").appliedAt');
  const histAp = run("REAL.jobs.find(j=>j.id==='d2').history.filter(h=>h.status==='applied').map(h=>String(h.at).slice(0,10)).join(',')");
  out.push(`[拖拽] 投出日 ${oldAp} → ${newAp} · history同步=${histAp}`);
  // 拖到自己原本那天应无变化
  run(`_calDrag={id:'d2',cls:'ap',date:'${newDate}',label:'投出'};calDropItem({preventDefault(){},currentTarget:document.getElementById('x')},'${newDate}');`);
  out.push('[拖拽] 拖到同一天不变=' + (run('REAL.jobs.find(j=>j.id==="d2").appliedAt') === newDate));
  // 月历上应出现新日期
  run("view='cal';renderBoard();");
  out.push('[拖拽] 月历已在新格显示=' + new RegExp(newDate + '\\"').test(run("document.getElementById('board').innerHTML")));
} catch (e) { out.push('[拖拽] ERR ' + e.message); }

/* 6. 直接改公司名/岗位名 */
try {
  run("openSheet('d3')");
  run("document.getElementById('sv-co').value='浙江精准学科技';document.getElementById('sv-po').value='AI产品经理';saveCoPo('d3');");
  out.push('[改名] ' + run('JSON.stringify({c:REAL.jobs.find(x=>x.id==="d3").company,r:REAL.jobs.find(x=>x.id==="d3").role})'));
} catch (e) { out.push('[改名] ERR ' + e.message); }

console.log(out.join('\n'));
