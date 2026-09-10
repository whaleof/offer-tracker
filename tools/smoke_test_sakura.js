const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync("G:/_06_项目代码/offer-tracker/sakura.html", "utf8");
const m = html.match(/<script>([\s\S]*?)<\/script>/);
new vm.Script(m[1]);  // 1) 语法检查
console.log("PASS 1/8 语法检查");

// ---- mock 环境 ----
const store = {
  "job-tracker-v1": JSON.stringify({ jobs: [
    { id: "a1", company: "网易", role: "游戏AI运营", status: "applied", city: "杭州",
      createdAt: "2026-09-01T00:00:00Z", appliedAt: "2026-09-05", history: [{ status: "pool", at: "2026-09-01T00:00:00Z" }, { status: "applied", at: "2026-09-05T00:00:00Z" }], notes: "", events: [] },
    { id: "a2", company: "腾讯", role: "AI 产品经理", status: "applied", city: "深圳",
      createdAt: "2026-09-08T00:00:00Z", appliedAt: "2026-09-08", history: [{ status: "pool", at: "2026-09-08T00:00:00Z" }, { status: "applied", at: "2026-09-08T00:00:00Z" }], notes: "", events: [] }
  ]})
};
const els = {};
const E = id => (els[id] ??= mkEl(id));
function mkEl(id) {
  return { id, innerHTML: "", textContent: "", value: "", src: "", disabled: false,
    style: {}, dataset: {}, classList: { add() {}, remove() {}, toggle() {} }, addEventListener() {} };
}
const ctx = {
  localStorage: { getItem: k => store[k] ?? null, setItem: (k, v) => { store[k] = v; } },
  document: { getElementById: id => (els[id] ??= mkEl(id)), querySelector: () => mkEl("q"), querySelectorAll: () => [] },
  console, JSON, Math, Date, confirm: () => true, alert: () => {},
  fetch: () => new Promise(() => {}),
  setTimeout, clearTimeout,
  location: { search: "", hash: "", hostname: "101.43.110.207" },
  URLSearchParams, FileReader: null, atob: s => Buffer.from(s, "base64").toString("binary"),
  addEventListener() {},
};
ctx.window = ctx; ctx.globalThis = ctx;
// FileReader 桩：同步回调，可控内容
let filePayload = "";
class FakeReader { readAsText() { this.result = filePayload; this.onload(); } }
ctx.FileReader = FakeReader;

vm.runInNewContext(m[1], ctx);  // 2) 初始化无运行时错误
console.log("PASS 2/8 初始化（boot+init）无运行时错误");

const jobs0 = JSON.parse(store["job-tracker-v1"]).jobs.length;
if (jobs0 !== 2) throw new Error("种子数据应为 2 条，实际 " + jobs0);

// 3) 合并雷达：2 条 newJobs（1 条与已有 a2 指纹重复 → 跳过；1 条新 → 落「想投」）
filePayload = JSON.stringify({ newJobs: [
  { company: "腾讯", role: "AI 产品经理", city: "深圳", channel: "官网", notes: "雷达抓的" },
  { company: "小红书", role: "AI 产品实习生", city: "上海", channel: "官网" }
]});
ctx.mergeRadar({ files: [{}], value: "" });
let data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.length !== 3) throw new Error("合并后应为 3 条，实际 " + data.jobs.length);
const added = data.jobs.find(j => j.company === "小红书");
if (!added || added.status !== "pool") throw new Error("新牌应落 pool/想投列");
if (added.id.length < 10) throw new Error("新牌缺唯一 id");
const a2 = data.jobs.find(j => j.id === "a2");
if (a2.status !== "applied" || a2.history.length !== 2) throw new Error("已有牌被合并改动——违反「只加不动」");
console.log("PASS 3/8 雷达合并：去重正确、新牌落想投、已有牌分毫未动");

// 3b) 再合并同文件 → 全部重复 → 不加
const before = JSON.parse(store["job-tracker-v1"]).jobs.length;
ctx.mergeRadar({ files: [{}], value: "" });
data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.length !== before) throw new Error("重复合并产生了重复记录");
console.log("PASS 3b/8 重复合并不产生重复记录");

// 3c) confirm=false 时合并中止
ctx.confirm = () => false;
filePayload = JSON.stringify({ newJobs: [{ company: "字节", role: "PM", city: "北京" }] });
ctx.mergeRadar({ files: [{}], value: "" });
data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.length !== before) throw new Error("取消确认仍写入了");
ctx.confirm = () => true;
console.log("PASS 3c/8 取消合并不写入");

// 4) 添牌（含三格）
E("nf-co").value = "企查查测试公司"; E("nf-po").value = "数据 PM";
E("nf-city").value = "杭州"; E("nf-ch").value = "BOSS";
E("nf-vf").value = "存疑"; E("nf-fit").value = "B"; E("nf-resume").value = "腾讯版-带背景色";
ctx.addCard();
data = JSON.parse(store["job-tracker-v1"]);
const nc = data.jobs.find(j => j.company === "企查查测试公司");
if (!nc) throw new Error("添牌未写入");
if (nc.verify !== "存疑" || nc.fit !== "B" || nc.resume !== "腾讯版-带背景色") throw new Error("添牌三格字段丢失");
if (nc.status !== "pool") throw new Error("添牌应落想投列");
if (E("nf-co").value !== "" || E("nf-vf").value !== "") throw new Error("添牌后表单未清空");
console.log("PASS 4/8 添牌：三格字段随牌写入、表单已清空");

// 5) 档案存三格：不改历史、不碰 updatedAt
E("sv-proof").value = "https://example.com/apply/tencent";
E("sv-vf").value = "届内"; E("sv-fit").value = "S"; E("sv-resume").value = "通用版";
const upd0 = data.jobs.find(j => j.id === "a1").updatedAt;
const hist0 = data.jobs.find(j => j.id === "a1").history.length;
ctx.saveTri("a1");
data = JSON.parse(store["job-tracker-v1"]);
const a1 = data.jobs.find(j => j.id === "a1");
if (a1.verify !== "届内" || a1.fit !== "S" || a1.resume !== "通用版" || a1.proof !== "https://example.com/apply/tencent") throw new Error("存三格失败(含凭证)");
if (a1.history.length !== hist0) throw new Error("存三格不该动 history");
if ((a1.updatedAt || "") !== (upd0 || "")) throw new Error("存三格不该碰 updatedAt");
// 空值兜底：三格全空也能存
E("sv-vf").value = ""; E("sv-fit").value = ""; E("sv-resume").value = "";
ctx.saveTri("a1");
data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.find(j => j.id === "a1").fit !== "") throw new Error("空值覆盖失败");
console.log("PASS 5/8 档案存三格：字段写入、历史与 updatedAt 未动、空值可覆盖");

// 6) 渠道拆解：雷达把整串投递网址写进 channel → 落阵前拆成 短渠道名 + applyUrl
filePayload = JSON.stringify({ newJobs: [
  { company: "小红书", role: "产品经理", city: "上海", channel: "校招官网 job.xiaohongshu.com/campus" }
]});
ctx.mergeRadar({ files: [{}], value: "" });
data = JSON.parse(store["job-tracker-v1"]);
const xhs = data.jobs.find(j => j.company === "小红书" && j.role === "产品经理");
if (!xhs) throw new Error("渠道拆解用例未写入");
if (xhs.channel !== "校招官网") throw new Error("牌面渠道应只留短名，实际「" + xhs.channel + "」");
if (xhs.applyUrl !== "job.xiaohongshu.com/campus") throw new Error("网址未拆进 applyUrl，实际「" + xhs.applyUrl + "」");
const clean2 = ctx.chClean("Moka/BOSS");
if (clean2.n !== "Moka/BOSS" || clean2.u !== "") throw new Error("没有网址的渠道被误改：" + JSON.stringify(clean2));
console.log("PASS 6/8 渠道拆解：牌面只留短名、网址进 applyUrl、无网址的渠道原样保留");

// 7) 拖牌推进：必须同时写 appliedAt（否则月历漏记「投出」——本次修的 bug）
filePayload = JSON.stringify({ newJobs: [{ company: "测试公司甲", role: "PM", city: "杭州", channel: "官网" }] });
ctx.mergeRadar({ files: [{}], value: "" });
const ta = JSON.parse(store["job-tracker-v1"]).jobs.find(j => j.company === "测试公司甲");
ctx.dropCard({ preventDefault() {}, currentTarget: { classList: { add() {}, remove() {} } },
  dataTransfer: { getData: () => ta.id } }, "sent");
const ta2 = JSON.parse(store["job-tracker-v1"]).jobs.find(j => j.company === "测试公司甲");
if (ta2.status !== "applied") throw new Error("拖拽推进失败，status=" + ta2.status);
if (!ta2.appliedAt) throw new Error("拖到「已投」没写 appliedAt —— 月历会漏记投出");
// 再推进一格到笔试，历史要留痕、月历要认
ctx.advance(ta.id);
const ta3 = JSON.parse(store["job-tracker-v1"]).jobs.find(j => j.id === ta.id);
if (ta3.status !== "test") throw new Error("推进到笔试失败，status=" + ta3.status);
if (!(ta3.history || []).some(h => h.status === "test")) throw new Error("推进没写历史");
if (!ctx.stageAt(ta3, "test")) throw new Error("stageAt 取不到「走到笔试」的日期");
console.log("PASS 7/8 阶段推进：拖牌/推进都写历史与投递日，stageAt 能取到每一步日期");

// 7b) 月历：条目来自历史记录（投出 + 进笔试都上历），不再只认 appliedAt
const board = E("board");
ctx.renderCal(board);
const calHtml = board.innerHTML;
if (!/测试公司甲/.test(calHtml)) throw new Error("月历没记上拖拽推进的「投出」");
if (!/进笔试/.test(calHtml)) throw new Error("月历没记上「进笔试」——阶段推进没进化");
if (!/投出/.test(calHtml)) throw new Error("月历丢了「投出」条目");
console.log("PASS 7b/8 月历：投出、进笔试等阶段推进全部自动上历");

// 8) 公司视图：一家一张牌，牌里列出这家所有岗位
const coHtml = ctx.coGroupHTML([
  { id: "z1", co: "小红书", po: "产品经理", st: "sent", days: 2 },
  { id: "z2", co: "小红书", po: "培训生 RPT", st: "want", days: 3 }
]);
if ((coHtml.match(/co-row/g) || []).length < 2) throw new Error("公司牌里没列出多个岗位");
if (!/2 个岗位/.test(coHtml)) throw new Error("公司牌没标出岗位数");
if ((coHtml.match(/小红书/g) || []).length !== 1) throw new Error("公司名出现了多次——没有合并成一张牌");
console.log("PASS 8/8 公司视图：一家一张牌，牌内列出这家所有岗位");

console.log("\nALL SMOKE TESTS PASSED ✓");
