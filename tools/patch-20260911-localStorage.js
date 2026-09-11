/*
 * 樱帖本地数据补丁（2026-09-11）
 * 用法：
 * 1. 在浏览器打开樱帖（本地文件或服务器地址都行，确保是你平时用的那个）。
 * 2. 按 F12 打开控制台（Console）。
 * 3. 把本文件内容整个复制粘贴进去，回车运行。
 * 4. 运行完刷新页面看效果。
 *
 * 它会做三件事：
 * A. 把今天已导入但状态错成「想投」的 4 张牌（蔚来×3 + 杭州精准学）改回「已投」。
 * B. 把公司名里的「（主体未披露）」从标题移到 notes 详情，月历不再挤长名。
 * C. 给「上海 AI陪伴产品 / PawLogic·iLands / AI4S 初创」三条的 notes 追加信源「小红书」。
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

  // A. 修正今天已投但错落成「想投」的牌
  data.jobs.forEach(j => {
    const note = String(j.notes || '');
    const isTodaySent = j.status === 'pool' && /2026-09-11 已投/.test(note);
    if (isTodaySent) {
      j.status = 'applied';
      j.appliedAt = j.appliedAt || '2026-09-11';
      j.history = Array.isArray(j.history) ? j.history : [];
      if (!j.history.some(h => h.status === 'applied')) {
        j.history.push({ status: 'applied', at: j.appliedAt + 'T12:00:00.000Z' });
      }
      j.updatedAt = now;
      changes++;
      console.log('✓ 已改「已投」:', j.company, '·', j.role);
    }
  });

  // B. 把公司名里的括号备注移到 notes
  data.jobs.forEach(j => {
    const original = j.company;
    const clean = String(original).replace(/（[^）]+）/g, '').trim();
    if (clean !== original) {
      const moved = String(original).match(/（([^）]+)）/g);
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
