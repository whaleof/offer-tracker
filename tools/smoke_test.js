// 秋招作战板 · 数据层冒烟测试
// 用法: node smoke_test.js   （改 index.html 里的 STORE/CONFIG 逻辑后必跑）
// 原理: 抽出 index.html 的 <script>，mock 掉浏览器环境，只验证数据层真实行为
//       （参照工作台 test_plans_smoke.js 的套路——假数据过 ≠ 真数据过，这里测的是真实调用路径）
const fs = require("fs"), vm = require("vm");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "index.html"), "utf8");
const m = html.match(/<script>([\s\S]*?)<\/script>/);
if (!m) { console.error("FAIL: 没找到 script 块"); process.exit(1); }
try { new vm.Script(m[1]); console.log("语法检查: PASS"); }
catch (e) { console.error("SYNTAX ERROR:", e.message); process.exit(1); }

const code = m[1].replace(/STORE\.load\(\);\s*renderMain\(\);/,
  "STORE.load();; globalThis.__X={STORE,CONFIG,UI,IO,VIEWS,DEMO,NEWS,THEME,CAL,AI};");
const store = {};
const fakeEl = { innerHTML: "", textContent: "", style: {}, classList: { add() {}, remove() {}, toggle() {} } };
const ctx = {
  localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = v; } },
  document: { querySelector: () => fakeEl, getElementById: () => fakeEl, body: fakeEl, createElement: () => fakeEl, addEventListener: () => {} },
  matchMedia: () => ({ matches: false }),
  fetch: () => Promise.reject(new Error("no fetch in test")),
  console, alert: () => {}, confirm: () => true, Date, Math, JSON,
  Blob: function () {}, URL: { createObjectURL: () => "" }, FileReader: function () {},
};
ctx.window = ctx; ctx.globalThis = ctx;
try { vm.runInNewContext(code, ctx); }
catch (e) { console.error("初始化运行时错误:", e.message); process.exit(1); }

const S = ctx.__X.STORE;
let fails = 0;
const t = (name, cond) => { console.log((cond ? "PASS" : "FAIL") + " " + name); if (!cond) fails++; };

// 1 新增
S.add({ company: "测试A", role: "PM", status: "pool" });
const id = S.data.jobs[0].id;
t("新增岗位进池", S.data.jobs[0].status === "pool" && S.data.jobs[0].history.length === 1);

// 2 编辑+改状态（走编辑表单的路径）
S.update(id, { company: "测试A改" }, "applied");
const j = S.data.jobs[0];
t("编辑改状态生效", j.status === "applied" && j.company === "测试A改");
t("编辑改状态记录历史", j.history.length === 2 && j.history[1].status === "applied");

// 3 详情页推进
S.update(id, {}, "interview");
t("详情页推进记录历史", j.history.length === 3 && j.history[2].status === "interview");

// 4 编辑不改状态 → 不加历史
S.update(id, { notes: "备注" }, j.status);
t("编辑不改状态不加历史", j.history.length === 3);

// 5 删除
S.remove(id);
t("删除生效", S.data.jobs.length === 0);

// 6 演示数据 + 导出回读
ctx.__X.DEMO.load();
const snapshot = JSON.parse(JSON.stringify(S.data));
t("演示数据可导出回读", snapshot.jobs.length === 8 && snapshot.version === 6);

// 6b 演示数据自带复盘题 → 题库视图有内容；自带 AI 思路与打招呼语
t("演示数据自带复盘题", S.data.jobs.some(j => j.reviews && j.reviews.length > 0));
t("题库视图聚合出题目", ctx.__X.VIEWS.qbank().includes("一面"));
t("题库视图带出AI思路", ctx.__X.VIEWS.qbank().includes("ai-box"));
t("演示数据自带打招呼语", S.data.jobs.some(j => j.greeting && j.greeting.length > 10));

// 6c CSV 导出：BOM + 表头 + 数据
const csv = ctx.__X.IO.buildCSV();
t("CSV导出含BOM表头和数据", csv.charCodeAt(0) === 0xFEFF && csv.includes("公司") && csv.includes("某大厂 A"));

// 6d 情报视图渲染条目
ctx.__X.NEWS.items = [{ title: "测试情报", date: "2026-09-07", tag: "比赛" }];
t("情报视图渲染条目", ctx.__X.VIEWS.news().includes("测试情报"));

// 6e 月历：事件聚合 + 视图渲染 + 点选展开
const ev = ctx.__X.CAL.eventsByDate(S.data.jobs);
const evDays = Object.keys(ev);
t("月历事件聚合出DDL/投递/复盘", evDays.length > 0
  && evDays.some(d => ev[d].some(e => e.type === "ddl" || e.type === "applied" || e.type === "review")));
t("月历视图渲染格网", ctx.__X.VIEWS.calendar().includes("cal-grid"));
ctx.__X.VIEWS.calSel = evDays[0];
t("月历点选日期内联展开", ctx.__X.VIEWS.calendar().includes("cal-panel"));

// 6f 打招呼语：保存到岗位并回读
const demoE = S.data.jobs.find(j => j.company === "某厂 E");
S.update(demoE.id, { greeting: "您好，看到贵司产品岗位，我有 AI 工作台 13 周迭代经验，期待沟通" });
t("打招呼语保存到岗位", S.data.jobs.find(j => j.id === demoE.id).greeting.includes("13 周"));

// 7 v1 旧数据迁移：自动补 reviews、advice、greeting、events、meta.points，版本升 4
S.replaceAll({ jobs: [{ company: "旧数据", status: "pool" }] });
const oldJ = S.data.jobs[0];
t("v1迁移补reviews且版本升4", S.data.version === 6 && Array.isArray(oldJ.reviews));
t("v1迁移补advice/greeting/events", Array.isArray(oldJ.reviews) && typeof oldJ.greeting === "string" && Array.isArray(oldJ.events));

// 8 添加/删除复盘
const jid = oldJ.id;
S.addReview(jid, { round: "一面", questions: ["题A", "题B"], notes: "n" });
t("添加复盘持久化", oldJ.reviews.length === 1 && oldJ.reviews[0].questions.length === 2);

// 8b AI 思路写入与覆盖
S.addAdvice(jid, 0, "题A", "先答定义再给案例");
t("AI思路按题存储", oldJ.reviews[0].advice["题A"] === "先答定义再给案例");
S.addAdvice(jid, 0, "题A", "换个更好的思路");
t("AI思路重新生成覆盖旧版", oldJ.reviews[0].advice["题A"] === "换个更好的思路" && oldJ.reviews[0].advice["题B"] === undefined);

S.removeReview(jid, 0);
t("删除复盘生效", oldJ.reviews.length === 0);

// 8a 游戏化积分：add/推进/复盘/offer 都加分，level 计算正确
S.replaceAll({ jobs: [] });
S.add({ company: "积分A", role: "PM", status: "pool" });
t("添加岗位得积分", S.data.meta.points === 5);
const pid = S.data.jobs[0].id;
S.update(pid, {}, "applied");
t("状态推进得积分", S.data.meta.points === 15);
S.addReview(pid, { round: "一面", questions: ["题Q"], notes: "" });
t("写复盘得积分", S.data.meta.points === 25);
S.update(pid, {}, "offer");
t("拿Offer得大额积分", S.data.meta.points === 75);
const lv = S.level();
t("等级按累计积分计算", lv.lv >= 2 && lv.p === 75 && !!lv.name);
t("等级条HTML渲染", ctx.__X.VIEWS.levelBar().includes("Lv."));

// 8a-2 日程节点：addEvent 存储并进月历
S.addEvent(pid, { date: "2026-09-10", time: "14:00", label: "面试中" });
t("日程节点持久化", S.data.jobs[0].events.length === 1 && S.data.jobs[0].events[0].time === "14:00");
const evMap = ctx.__X.CAL.eventsByDate(S.data.jobs);
t("日程节点进月历", (evMap["2026-09-10"]||[]).some(e => e.type === "event"));

// 9 空数据兜底
S.replaceAll({});
t("空数据兜底", Array.isArray(S.data.jobs));

if (fails) { console.error("=== " + fails + " 项 FAIL ==="); process.exit(1); }
console.log("=== 数据层全部通过（v4 含积分/日程/迁移） ===");
