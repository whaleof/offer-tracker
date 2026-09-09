const fs = require("fs"), vm = require("vm");
const html = fs.readFileSync("G:/_06_项目代码/offer-tracker/sakura.html", "utf8");
const m = html.match(/<script>([\s\S]*?)<\/script>/);
new vm.Script(m[1]);  // 1) 语法检查
console.log("PASS 1/5 语法检查");

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
console.log("PASS 2/5 初始化（boot+init）无运行时错误");

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
console.log("PASS 3/5 雷达合并：去重正确、新牌落想投、已有牌分毫未动");

// 3b) 再合并同文件 → 全部重复 → 不加
const before = JSON.parse(store["job-tracker-v1"]).jobs.length;
ctx.mergeRadar({ files: [{}], value: "" });
data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.length !== before) throw new Error("重复合并产生了重复记录");
console.log("PASS 3b/5 重复合并不产生重复记录");

// 3c) confirm=false 时合并中止
ctx.confirm = () => false;
filePayload = JSON.stringify({ newJobs: [{ company: "字节", role: "PM", city: "北京" }] });
ctx.mergeRadar({ files: [{}], value: "" });
data = JSON.parse(store["job-tracker-v1"]);
if (data.jobs.length !== before) throw new Error("取消确认仍写入了");
ctx.confirm = () => true;
console.log("PASS 3c/5 取消合并不写入");

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
console.log("PASS 4/5 添牌：三格字段随牌写入、表单已清空");

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
console.log("PASS 5/5 档案存三格：字段写入、历史与 updatedAt 未动、空值可覆盖");
console.log("\nALL SMOKE TESTS PASSED ✓");
