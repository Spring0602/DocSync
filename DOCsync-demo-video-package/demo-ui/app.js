"use strict";

const $ = (id) => document.getElementById(id);
const store = window.DocSyncReportStore;
const list = (value) => Array.isArray(value) ? value : [];
const text = (id, value) => { $(id).textContent = value ?? "未记录"; };
const shortHash = (value) => typeof value === "string" && value.length > 18
  ? value.slice(0, 9) + "…" + value.slice(-6) : value || "未记录";
const seconds = (value) => typeof value === "number" && Number.isFinite(value)
  ? value.toFixed(2) + " s" : "未记录";
const node = (tag, value, className) => {
  const element = document.createElement(tag);
  if (value !== undefined) element.textContent = value;
  if (className) element.className = className;
  return element;
};
const categoryNames = { confirmed: "确认冲突", uncertain: "不确定", ignored: "已忽略", unverified: "未验证", other: "其他记录" };
const typeNames = { DEFAULT_VALUE: "默认值", SIGNATURE: "调用签名", CONFIG: "配置值" };
const stageMessages = [
  ["选择记录", "定位需要处理的问题", "按路径、状态或类型筛选，先确认问题，再审阅证据。"],
  ["核对证据", "源码与文档，同屏核对", "摘录、行号和哈希均来自报告；页面不会补造缺失源码。"],
  ["审阅补丁", "审阅修改，再显式应用", "下载的是 diff，不是自动修复。应用前仍需原始校验清单。"],
  ["对比运行", "用复扫报告核对变化", "展示两次运行的计数差异，不把生成补丁当作修复完成。"],
];
const sections = ["overview", "evidence-section", "patch-section", "verify-section"];
const panels = [...document.querySelectorAll("[data-report-panel]")];
const pageSize = 12;
let data, records = [], filtered = [], selectedKey = null, page = 0, stage = 0;
let toastTimer, autoTimer, searchTimer;

function notice(message) {
  $("reportNotice").hidden = !message;
  text("reportNotice", message);
}
function toast(message) {
  clearTimeout(toastTimer);
  text("toast", message);
  $("toast").classList.add("is-visible");
  toastTimer = setTimeout(() => $("toast").classList.remove("is-visible"), 6000);
}
function persist() {
  const result = store.save(data);
  if (!result.ok) notice(result.message + " 当前页面仍可使用；跨页可能无法保留，请先导出报告。");
}
function typed(value) {
  if (typeof value?.canonical !== "string") return null;
  try {
    const parsed = JSON.parse(value.canonical);
    if (!Array.isArray(parsed) || parsed.length < 2) return null;
    const display = parsed[1] === null ? "None" : value.type === "bool"
      ? parsed[1] ? "True" : "False" : JSON.stringify(parsed[1]);
    return { display, type: String(value.type || parsed[0]) };
  } catch { return null; }
}
function hashButton(id, value) {
  const target = $(id);
  const real = typeof value === "string" ? value : "";
  target.textContent = shortHash(real);
  target.title = real ? real + " · 点击复制" : "报告未记录";
  target.dataset.copy = real;
  target.disabled = !real;
}
function current() { return records.find((record) => record.key === selectedKey) || null; }
function currentItems() {
  const record = current();
  return { record, f: record?.finding, fact: record?.facts?.[0], claim: record?.claim,
    patch: record?.patch, judgment: record?.judgment };
}
function driftType(record) {
  return record.finding?.drift_type || record.judgment?.drift_type ||
    ({ DEFAULT_ASSERTION: "DEFAULT_VALUE", CONFIG_ASSERTION: "CONFIG", CALL_EXAMPLE: "SIGNATURE" }[record.claim?.kind]) || "other";
}
function filterRecords(reset = true) {
  const query = $("recordSearch").value.trim().toLocaleLowerCase();
  const category = $("statusFilter").value, type = $("typeFilter").value;
  filtered = records.filter((record) => {
    const search = [record.title, record.path, record.reason, record.claim?.subject,
      record.claim?.predicate, record.key, ...list(record.facts).map((fact) => fact.span?.path)].join(" ").toLocaleLowerCase();
    return (category === "all" || category === record.category) &&
      (type === "all" || type === driftType(record)) && (!query || search.includes(query));
  });
  if (reset) page = 0;
  page = Math.min(page, Math.max(0, Math.ceil(filtered.length / pageSize) - 1));
  const visibleRecords = filtered.slice(page * pageSize, (page + 1) * pageSize);
  if (!visibleRecords.some((record) => record.key === selectedKey)) {
    selectedKey = visibleRecords[0]?.key || null;
    renderFinding();
  }
  renderRecords();
}
function renderRecords() {
  text("recordCount", records.length);
  text("resultCount", filtered.length + " 条匹配 / " + records.length + " 条记录");
  text("pageIndicator", (page + 1) + " / " + Math.max(1, Math.ceil(filtered.length / pageSize)));
  $("previousPage").disabled = page === 0;
  $("nextPage").disabled = (page + 1) * pageSize >= filtered.length;
  $("recordEmpty").hidden = filtered.length > 0;
  text("recordEmpty", records.length ? "没有符合筛选条件的记录。可清空搜索或重置筛选。" :
    "报告中没有待审查记录。零告警不代表所有文档均已验证一致，请同时检查扫描状态、覆盖范围与诊断。");
  $("recordList").replaceChildren(...filtered.slice(page * pageSize, (page + 1) * pageSize).map((record) => {
    const button = node("button", undefined, "record-row" + (record.key === selectedKey ? " is-selected" : ""));
    button.type = "button";
    button.setAttribute("aria-pressed", String(record.key === selectedKey));
    const description = node("span", undefined, "record-description");
    description.append(node("strong", record.title || record.claim?.subject || "报告记录"),
      node("small", record.path || "未记录文档路径"));
    button.append(node("span", categoryNames[record.category] || "其他记录", "record-badge " + record.category),
      description, node("span", typeNames[driftType(record)] || "其他", "record-type"),
      node("span", "查看 →", "record-open"));
    button.addEventListener("click", () => {
      stopAuto();
      selectedKey = record.key;
      renderRecords();
      renderFinding();
      navigate(0, false);
      panels.find((panel) => panel.dataset.reportPanel === "finding").open = true;
    });
    return button;
  }));
}
function fillCode(id, snippet, span, highlight, style) {
  const target = $(id);
  target.replaceChildren();
  if (typeof snippet !== "string" || !snippet) {
    target.append(node("p", "报告未提供此项摘录。请根据路径和行号核对原仓库。", "diff-empty"));
    return;
  }
  const start = Number.isInteger(span?.start_line) ? span.start_line : null;
  const end = Number.isInteger(span?.end_line) ? span.end_line : start;
  snippet.replace(/\n$/, "").split("\n").forEach((line, i) => {
    const row = node("div", undefined, "code-row");
    row.append(node("span", start !== null && start + i <= end ? start + i : "·", "line-number"));
    const code = node("code");
    const index = typeof highlight === "string" && highlight ? line.indexOf(highlight) : -1;
    if (index >= 0) code.append(document.createTextNode(line.slice(0, index)),
      node("mark", highlight, style), document.createTextNode(line.slice(index + highlight.length)));
    else code.textContent = line || " ";
    row.append(code);
    target.append(row);
  });
}
function positionRange(span, kind, prefix) {
  const start = span?.["start_" + kind], end = span?.["end_" + kind];
  if (!Number.isInteger(start)) return "";
  return prefix + start + (Number.isInteger(end) && end !== start ? "–" + end : "");
}
function spanInfo(prefix, span) {
  text(prefix === "code" ? "codePath" : "docPath", span?.path || "未提供路径");
  text(prefix + "Line", positionRange(span, "line", "L") || "行号未记录");
  text(prefix + "Bytes", positionRange(span, "byte", "字节 "));
  hashButton(prefix + "Hash", span?.blob_hash);
}
function renderDiff(diff) {
  const target = $("patchCode");
  target.replaceChildren();
  if (typeof diff !== "string" || !diff) {
    target.append(node("p", "当前记录没有可下载的补丁。请人工核对，不要自行推断修复值。", "diff-empty"));
    return;
  }
  let oldLine = null, newLine = null;
  for (const line of diff.replace(/\n$/, "").split("\n")) {
    let kind = "diff-meta", oldNo = "", newNo = "", sign = "", content = line;
    const hunk = /^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@/.exec(line);
    if (hunk) { oldLine = Number(hunk[1]); newLine = Number(hunk[2]); }
    else if (line.startsWith("--- ") || line.startsWith("+++ ")) { oldLine = null; newLine = null; }
    else if (oldLine !== null && newLine !== null) {
      sign = line[0]; content = line.slice(1);
      if (sign === "-") { kind = "diff-remove"; oldNo = oldLine++; }
      else if (sign === "+") { kind = "diff-add"; newNo = newLine++; }
      else if (sign === " ") { kind = ""; oldNo = oldLine++; newNo = newLine++; }
      else { content = line; sign = ""; }
    }
    const row = node("div", undefined, "diff-line " + kind);
    row.append(node("span", oldNo, "old-line"), node("span", newNo, "new-line"),
      node("span", sign, "diff-sign"), node("code", content || " "));
    target.append(row);
  }
}
function renderFinding() {
  const { record, f, fact, claim, patch } = currentItems();
  const ev = f?.evidence || {};
  const isConflict = record?.category === "confirmed";
  $("finding-section").classList.toggle("is-neutral", !isConflict);
  text("findingPosition", record ? (records.indexOf(record) + 1) + " / " + records.length : "未选择");
  const title = record?.title || (records.length ? "请选择符合筛选条件的记录" : "报告中没有待审查记录");
  text("findingTitle", title);
  text("findingPreview", title);
  text("findingReason", record?.reason || "请核对原始报告的覆盖范围与诊断；没有告警不等于所有声明一致。");
  text("findingStatus", record ? categoryNames[record.category] || "报告记录" : "未选择");
  text("ruleId", ev.rule_id || "未记录规则");
  text("severityText", f?.severity ? "级别 · " + ({ warning: "警告", error: "错误", info: "提示" }[f.severity] || f.severity) : "");
  text("verifyStatus", f ? "报告验证状态 · " + (f.verification_status || "未记录") : record ? "尚不能确认为冲突或一致" : "");
  $("ignoreNotice").hidden = !f?.ignored && !f?.ignore_expires;
  text("ignoreNotice", f?.ignored
    ? "已忽略：" + (f.ignore_reason || "未提供原因") + (f.ignore_expires ? "；有效期至 " + f.ignore_expires : "")
    : f?.ignore_expires ? "忽略规则未生效 / 已过期：" + (f.ignore_reason || "未提供原因") + "；截止日期 " + f.ignore_expires + "。本条仍计入有效告警。" : "");
  const docValue = typed(claim?.value), codeValue = fact?.value_state === "KNOWN" ? typed(fact.typed_value) : null;
  $("valueComparison").hidden = !isConflict || !docValue || !codeValue;
  text("documentValue", docValue?.display); text("documentType", docValue?.type);
  text("codeValue", codeValue?.display); text("codeType", codeValue?.type);
  text("comparisonContext", fact ? [fact.subject, fact.property].filter(Boolean).join(" · ") : "");
  text("findingId", f?.finding_id || record?.key);
  text("snapshotHash", ev.snapshot_hash || data.report.snapshot.files_hash);
  const signature = fact && list(data.report.facts).find((item) => item.entity_id === fact.entity_id &&
    item.fact_kind === "SIGNATURE" && typeof item.expression === "string");
  const codeSource = f?.drift_type === "DEFAULT_VALUE" ? signature || fact : fact;
  const codeSpan = codeSource?.span || ev.code;
  spanInfo("code", codeSpan); spanInfo("doc", ev.document || claim?.span);
  text("codeBytes", positionRange(ev.code, "byte", "事实字节 "));
  hashButton("codeHash", ev.code?.blob_hash || codeSpan?.blob_hash);
  text("codeExcerptLabel", signature && codeSource === signature ? "报告中的函数定义" : "报告中的静态表达式");
  fillCode("codeSnippet", codeSource?.expression, codeSpan, fact?.expression, "value-code");
  fillCode("docSnippet", claim?.quote, claim?.span || ev.document, docValue?.display, "value-document");
  renderDiff(patch?.diff);
  const edits = list(patch?.edits);
  text("patchScope", patch ? new Set(edits.map((edit) => edit.span?.path).filter(Boolean)).size +
    " 个文件 · " + edits.length + " 处替换" : "没有补丁");
  text("patchValidation", patch ? "校验 · " + (patch.validation || "未记录") : "");
  text("patchReview", patch ? "仍需人工审阅" : "");
  text("patchReason", patch ? "下载仅含 diff；CLI 应用时还需要原始 manifest，并检查仓库内容未变更。" : "此记录没有可用补丁，不确定项需要补充证据。");
  $("copyPatch").disabled = !patch?.diff;
  $("downloadPatch").disabled = !patch?.diff;
  $("copyPatch").dataset.copy = typeof patch?.diff === "string" ? patch.diff : "";
  $("validationList").replaceChildren(...list(patch?.validation_details).map((value) => node("li", value)));
  if (!list(patch?.validation_details).length) $("validationList").append(node("li", "未提供校验明细。"));
  renderVerification();
}
function renderVerification() {
  const { f, patch } = currentItems(), report = data.report, after = data.after;
  const comparison = after ? store.compare(data, after) : null;
  const rescanCompleted = after?.report.manifest.status === "COMPLETED";
  const events = [
    [Boolean(report.snapshot.head_sha), "固定快照", shortHash(report.snapshot.head_sha)],
    [Array.isArray(report.facts), "静态事实", Array.isArray(report.facts) ? report.facts.length + " 条记录" : "未提供"],
    [f?.verification_status === "VERIFIED", "证据验证", f?.verification_status || "未确认"],
    [patch?.validation === "VALIDATED", "补丁校验", patch?.validation || "当前记录没有补丁"],
    [Boolean(comparison?.compatible && rescanCompleted), "复扫对照", after
      ? after.report.manifest.status + (rescanCompleted ? "" : " · 结果不完整") : "尚未导入"],
  ];
  $("timeline").replaceChildren(...events.map(([done, title, detail]) => {
    const row = node("li", undefined, done ? "done" : "");
    const copy = node("div"); copy.append(node("strong", title), node("small", detail));
    row.append(node("span", done ? "✓" : "○", "timeline-symbol"), copy); return row;
  }));
  $("rescanStats").replaceChildren();
  $("clearRescan").disabled = !after;
  $("closureCard").classList.toggle("is-closed", Boolean(comparison?.compatible && after.confirmedCount === 0 &&
    after.uncertainCount === 0 && after.unverifiedCount === 0 && rescanCompleted));
  $("closureCard").classList.toggle("is-incomplete", Boolean(after && !rescanCompleted));
  if (!after) {
    text("closureTitle", "尚未提供复扫报告");
    text("closureBody", "在 CLI 审阅并应用补丁、重新扫描后，导入新的 report.json。当前页面不会执行这些操作。");
    return;
  }
  text("closureTitle", !comparison.compatible ? "两份报告不可直接对比" : !rescanCompleted
    ? "复扫未完成，暂不能判断修复结果" : data.confirmedCount + " → " + after.confirmedCount + " 条确认冲突");
  text("closureBody", comparison.compatible
    ? "复扫状态 " + after.report.manifest.status + "。" + (rescanCompleted
      ? "这里只比较报告计数，不证明补丁已应用，也不保证未覆盖的声明正确。"
      : "扫描失败或覆盖不完整，即使报告中为零告警也不能视为修复通过。请先排查原报告诊断，再重新扫描。")
    : list(comparison.reasons).join("；"));
  for (const [label, value] of [["报告中冲突", after.confirmedCount ?? "未记录"], ["不确定", after.uncertainCount ?? "未记录"],
    ["运行 ID", shortHash(after.report.manifest.run_id)], ["耗时", seconds(after.runtime)]]) {
    const cell = node("div"); cell.append(node("dt", label), node("dd", value)); $("rescanStats").append(cell);
  }
}
function applyDataset(model) {
  const nextRecords = store.records(model.report); // Prepare before replacing a valid current report.
  data = model; records = nextRecords; selectedKey = records[0]?.key || null;
  const requested = new URLSearchParams(location.search).get("record");
  if (records.some((record) => record.key === requested)) selectedKey = requested;
  const report = data.report, manifest = report.manifest, isDemo = data.source === "verified_bundle";
  text("repoName", data.name);
  text("sourceLabel", isDemo ? "随包演示 · 只读" : "本地导入 · 结论来自原报告");
  text("sourceBadgeText", isDemo ? "演示" : "本地报告");
  text("consoleTitle", isDemo ? "演示工件" : "本地报告");
  text("consoleDetail", "此页面不执行扫描或修改仓库。");
  text("consoleState", "LOCAL · READ ONLY");
  hashButton("headSha", report.snapshot.head_sha);
  text("scanStatus", ({ COMPLETED: "扫描完成", PARTIAL: "扫描不完整", FAILED: "扫描失败" })[manifest.status] || manifest.status);
  $("scanStatus").className = "scan-status" + (manifest.status === "FAILED" ? " is-failed" : manifest.status !== "COMPLETED" ? " is-partial" : "");
  text("runtimeText", seconds(data.runtime)); text("modeText", manifest.mode);
  text("topRunId", shortHash(manifest.run_id)); $("topRunId").title = manifest.run_id;
  text("topSchema", report.schema_version);
  for (const key of ["confirmedCount", "patchCount", "uncertainCount", "ignoredCount"]) text(key, data[key] ?? "—");
  text("summaryCaptionDetail", "只读 · 不会自动应用补丁");
  text("runId", manifest.run_id); text("schemaText", report.schema_version);
  text("requestCount", manifest.usage?.requests ?? "未记录");
  const diagnostics = list(manifest.diagnostics).map((value) => typeof value === "string"
    ? value : value?.code || value?.message || "诊断内容未记录");
  text("diagnosticSummary", "验证拒绝 " + (Array.isArray(report.rejected) ? report.rejected.length : "未记录") +
    "；诊断 " + (Array.isArray(manifest.diagnostics) ? diagnostics.length : "未记录") +
    (diagnostics.length ? " · " + diagnostics.join(" / ") : ""));
  $("findingSelectWrap").hidden = true;
  text("sourceNote", isDemo ? "演示来源：随包 artifacts/ · 纯规则运行" : "本地会话缓存 · 未重新扫描或验证 · 恢复演示可清除当前导入");
  const warnings = list(data.warnings).map((value) => typeof value === "string" ? value : value?.message || String(value));
  if (manifest.status !== "COMPLETED") warnings.unshift("本次扫描状态为 " + manifest.status + "，不能把零告警解释为扫描通过。");
  if (!isDemo) warnings.push("导入仅校验报告结构，不重新验证证据真实性。");
  if (location.protocol === "file:") warnings.push("建议使用“启动前端.cmd”打开，确保各页面共享同一份报告。");
  notice(warnings.join(" "));
  $("recordSearch").value = ""; $("statusFilter").value = "all"; $("typeFilter").value = "all";
  page = Math.max(0, Math.floor(records.findIndex((record) => record.key === selectedKey) / pageSize));
  filterRecords(false);
  renderFinding();
  navigate(0, false);
}
function navigate(index, scroll = true) {
  stage = Math.max(0, Math.min(3, index));
  const targetPanel = [null, "evidence", "patch", "verify"][stage];
  panels.forEach((panel) => { panel.open = panel.dataset.reportPanel === targetPanel; });
  document.querySelectorAll(".step").forEach((button, i) => {
    button.classList.toggle("is-active", i === stage);
    if (i === stage) button.setAttribute("aria-current", "step"); else button.removeAttribute("aria-current");
    button.querySelector("em").textContent = i === stage ? "当前" : "";
  });
  const message = stageMessages[stage];
  text("overviewBadge", message[0]); text("overviewHeading", message[1]); text("overviewDescription", message[2]);
  text("guideLabel", (stage + 1) + " / 4");
  text("nextStage", stage === 3 ? "返回列表 →" : ["", "核对证据 →", "审阅补丁 →", "查看复扫 →"][stage + 1]);
  renderVerification();
  if (scroll) $(sections[stage]).scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth", block: "start" });
}
function stopAuto() {
  clearInterval(autoTimer); autoTimer = null;
  text("playLabel", "导览"); $("autoDemo").setAttribute("aria-pressed", "false");
}
function demoModel() {
  const bundle = window.DOCSYNC_DEMO_REPORTS;
  if (!bundle) throw new Error("缺少 demo-data.js，请完整解压前端文件夹。");
  const model = store.normalize(bundle.before, bundle.repoName, "verified_bundle");
  model.after = store.normalize(bundle.after, bundle.repoName, "verified_bundle");
  return model;
}
async function copyText(value) {
  if (!value) return;
  try {
    if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value);
    else {
      const input = node("textarea"); input.value = value; input.style.cssText = "position:fixed;opacity:0;";
      document.body.append(input); input.select(); const copied = document.execCommand("copy"); input.remove();
      if (!copied) throw new Error("copy");
    }
    toast("已复制。");
  } catch { toast("浏览器未允许复制。可下载原始报告或手动选择文本复制。"); }
}
function download(content, filename, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = node("a"); link.href = url; link.download = filename;
  document.body.append(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
async function importFile(input, rescan) {
  const file = input.files?.[0]; if (!file) return;
  stopAuto();
  try {
    if (file.size > 10 * 1024 * 1024) throw new Error("当前视图支持 10 MB 以内的报告。");
    const report = JSON.parse(await file.text());
    const model = store.normalize(report, report.snapshot?.repo_id || file.name, "local_import");
    if (rescan) {
      const comparison = store.compare(data, model);
      if (!comparison.compatible) throw new Error("不能作为复扫对照：" + comparison.reasons.join("；"));
      data.after = model; renderVerification(); persist();
      toast("已载入复扫对照。比较计数不等于证明所有问题已修复。");
    } else {
      applyDataset(model); persist();
      toast("已导入报告。可搜索记录，或前往数据、代码与运行轨迹页。");
    }
  } catch (error) { toast("导入失败：" + error.message + " 原报告保持不变。"); }
  finally { input.value = ""; }
}

document.querySelectorAll(".step").forEach((button) => button.addEventListener("click", () => {
  stopAuto(); navigate(Number(button.dataset.stage));
}));
panels.forEach((panel) => panel.addEventListener("toggle", () => {
  const action = panel.querySelector(".disclosure-action");
  if (action) action.textContent = panel.open ? "收起" : "展开查看";
}));
$("recordSearch").addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => filterRecords(), 120); });
for (const id of ["statusFilter", "typeFilter"]) $(id).addEventListener("change", () => filterRecords());
$("resetFilters").addEventListener("click", () => {
  $("recordSearch").value = ""; $("statusFilter").value = "all"; $("typeFilter").value = "all"; filterRecords();
});
$("previousPage").addEventListener("click", () => { page--; filterRecords(false); });
$("nextPage").addEventListener("click", () => { page++; filterRecords(false); });
$("nextStage").addEventListener("click", () => { stopAuto(); navigate(stage === 3 ? 0 : stage + 1); });
$("autoDemo").addEventListener("click", () => {
  if (autoTimer) { stopAuto(); return; }
  navigate(0); text("playLabel", "暂停"); $("autoDemo").setAttribute("aria-pressed", "true");
  autoTimer = setInterval(() => { if (stage < 3) navigate(stage + 1); else stopAuto(); }, 5500);
});
$("resetDemo").addEventListener("click", () => {
  stopAuto(); const cleared = store.clear(); applyDataset(demoModel());
  if (!cleared.ok) notice(cleared.message);
  toast("已恢复演示；原始文件未被修改。");
});
for (const id of ["headSha", "codeHash", "docHash", "copyPatch"]) $(id).addEventListener("click", () => copyText($(id).dataset.copy));
$("importReport").addEventListener("click", () => $("reportInput").click());
$("importRescan").addEventListener("click", () => $("rescanInput").click());
$("reportInput").addEventListener("change", () => importFile($("reportInput"), false));
$("rescanInput").addEventListener("change", () => importFile($("rescanInput"), true));
$("clearRescan").addEventListener("click", () => { data.after = null; renderVerification(); persist(); toast("已移除复扫对照。"); });
$("downloadReport").addEventListener("click", () => download(JSON.stringify(data.report, null, 2) + "\n", "docsync-report.json", "application/json"));
$("downloadPatch").addEventListener("click", () => {
  const diff = currentItems().patch?.diff;
  if (diff) download(diff, "docsync-review.patch", "text/plain;charset=utf-8");
});
$("toggleSidebar").addEventListener("click", () => {
  const collapsed = document.body.classList.toggle("sidebar-collapsed");
  $("toggleSidebar").setAttribute("aria-expanded", String(!collapsed));
  $("toggleSidebar").setAttribute("aria-label", collapsed ? "展开侧栏" : "折叠侧栏");
});
try {
  const loaded = store.load({ fallback: demoModel() });
  applyDataset(loaded.model || demoModel());
  if (!loaded.ok) notice(loaded.message);
} catch (error) {
  notice("报告无法初始化：" + error.message + "。请完整解压前端文件，或重新导入 report.json。");
}
