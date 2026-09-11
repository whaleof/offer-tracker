/*
 * 樱帖本地数据补丁（2026-09-11 升级版）
 * 用法：
 * 1. 在浏览器打开樱帖（本地文件或服务器地址都行，确保是你平时用的那个）。
 * 2. 按 F12 打开控制台（Console）。
 * 3. 把本文件内容整个复制粘贴进去，回车运行。
 * 4. 运行完刷新页面看效果。
 *
 * 它会做三件事：
 * A. 把今天已导入但状态错成「想投」的 4 张牌（蔚来×3 + 杭州精准学）改回「已投」，
 *    并把蔚来 3 张占位牌「待补真名 #1/#2/#3」替换为真实岗名 + 对应简历版本。
 * B. 只把公司名里的「（主体未披露）」类括号备注移到 notes，月历不再挤长名（保留（NIO）等品牌标识不动）。
 * C. 给「上海 AI陪伴产品 / PawLogic·iLands / AI4S 初创」三条的 notes 追加信源「小红书」。
 *
 * 映射（基于 SOP 记录的蔚来校招职位ID，已联网核实岗名）：
 *   #1 = A35766  firefly萤火虫 数字体验产品经理（AI&创新）         → 蔚来AI产品经理版
 *   #2 = A74095A 数字产品-NOMI 体验经理（智能座舱 AI 大模型）      → 蔚来AI产品经理版
 *   #3 = 运营线 A184703（候选 A210213A / A65282，具体岗名待本人从 BOSS 确认）→ 蔚来产品运营版
 */

(function patch() {
  const LS_KEY = 'job-tracker-v1';
  const raw = localStorage.getItem(LS_KEY);
  if (!raw) { console.warn('找不到樱帖数据（key=' + LS_KEY + '）'); return; }
  let data;
  try { data = JSON.parse(raw); } catch (e) { console.error('解析失败', e); return; }
  if (!data || !Array.isArray(data.jobs)) { console.warn('数据格式不对'); return; }

  let changes = 0;
  const isoDay = () => new Date().toISOString().slice(0, 10);
  const now = new Date().toISOString();

  // 蔚来 3 岗真名映射
  const NIO_MAP = {
    '#1': {
      role: 'firefly萤火虫 数字体验产品经理（AI&创新）',
      city: '上海',
      resume: '常玉涵-简历-蔚来AI产品经理版',
      note: '职位ID A35766。蔚来校招产品经理线（AI 产品线），firefly 萤火虫品牌数字座舱 AI&创新体验，与 AI 产品方向高度契合。'
    },
    '#2': {
      role: '数字产品-NOMI 体验经理（智能座舱 AI 大模型）',
      city: '上海/北京',
      resume: '常玉涵-简历-蔚来AI产品经理版',
      note: '职位ID A74095A。蔚来校招产品经理线（AI 产品线），NOMI 智能座舱 AI 大模型方向，依托 NOMI 交互 IP 做车载 AI 体验规划。'
    },
    '#3': {
      role: '产品运营（蔚来内推·A184703）',
      city: '（内推）',
      resume: '常玉涵-简历-蔚来产品运营版',
      note: '运营线三候选职位ID：A184703 / A210213A / A65282，本次默认记 A184703；具体岗名公开查不到编号映射，请从 BOSS/蔚来校招后台确认实际投的是哪个号，告诉 AI 立刻补真名。'
    }
  };

  // A. 修正今天已投但错落成「想投」的牌；顺便把「待补真名」占位换成真实岗名
  data.jobs.forEach(j => {
    const note = String(j.notes || '');
    const isTodaySent = j.status === 'pool' && /2026-09-11 已投/.test(note);
    const m = String(j.role || '').match(/待补真名\s*(#[123])/);
    if (!isTodaySent && !m) return;

    if (m && NIO_MAP[m[1]]) {
      const info = NIO_MAP[m[1]];
      j.role = info.role;
      j.city = info.city;
      j.resume = info.resume;
      j.notes = (note ? note + '\n' : '') + '【岗名已补全】' + info.note;
    }
    j.status = 'applied';
    j.appliedAt = j.appliedAt || '2026-09-11';
    j.history = Array.isArray(j.history) ? j.history : [];
    if (!j.history.some(h => h.status === 'applied')) {
      j.history.push({ status: 'applied', at: j.appliedAt + 'T12:00:00.000Z' });
    }
    j.updatedAt = now;
    changes++;
    console.log('✓ 已修正:', j.company, '·', j.role);
  });

  // B. 只清「（主体未披露）」这类括号备注，移到 notes；保留（NIO）等品牌标识
  data.jobs.forEach(j => {
    const original = j.company;
    const clean = String(original).replace(/（[^）]*未披露[^）]*）/g, '').trim();
    if (clean !== original) {
      const moved = String(original).match(/（([^）]*未披露[^）]*)）/g);
      j.company = clean;
      const appendix = moved ? ('原括号备注：' + moved.join('、')) : '';
      j.notes = (j.notes ? j.notes + '\n' : '') + appendix;
      j.updatedAt = now;
      changes++;
      console.log('✓ 已清括号:', original, '→', clean);
    }
  });

  // C. 给三条目标牌追加信源「小红书」
  const targets = ['上海 AI陪伴产品', 'PawLogic', 'AI4S 初创'];
  data.jobs.forEach(j => {
    const co = String(j.company || '');
    const hit = targets.some(t => co.includes(t));
    if (hit) {
      const note = String(j.notes || '');
      if (!note.includes('小红书')) {
        j.notes = (note ? note + '\n' : '') + '【信源】小红书';
        j.updatedAt = now;
        changes++;
        console.log('✓ 已加信源:', co, '·', j.role);
      }
    }
  });

  if (changes === 0) { console.log('没有需要改的数据'); return; }
  localStorage.setItem(LS_KEY, JSON.stringify(data));
  console.log('补丁完成，共', changes, '处改动。请刷新页面。');
})();
