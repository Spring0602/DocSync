(() => {
  "use strict";
  const store = window.DocSyncReportStore;
  const main = document.querySelector("main");
  const byId = (id) => document.getElementById(id);
  const list = (value) => Array.isArray(value) ? value : [];
  const set = (id, value) => {
    const target = byId(id);
    if (target) target.textContent = value ?? "—";
  };
  const make = (tag, value, className) => {
    const element = document.createElement(tag);
    if (value !== undefined) element.textContent = value;
    if (className) element.className = className;
    return element;
  };
  const short = (value, head = 10, tail = 6) => typeof value === "string"
    ? value.length > head + tail + 1 ? value.slice(0, head) + "…" + value.slice(-tail) : value
    : "—";
  const statusText = (status) => ({ COMPLETED: "扫描完成", PARTIAL: "扫描不完整", FAILED: "扫描失败" })[status] || "状态未记录";
  const categoryText = (category) => ({ confirmed: "确认冲突", ignored: "已忽略", uncertain: "不确定", unverified: "待验证", other: "其他记录" })[category] || "待核对";

  function notice(message, warning = false) {
    let target = byId("portalNotice");
    if (!target) {
      target = make("p", undefined, "notice session-notice");
      target.id = "portalNotice";
      target.setAttribute("role", "status");
      main.prepend(target);
    }
    target.textContent = message;
    target.classList.toggle("is-warning", warning);
  }

  if (!store) {
    notice("缺少 report-store.js，请完整解压前端文件夹。", true);
    return;
  }
  let fallback = null;
  try {
    const bundle = window.DOCSYNC_DEMO_REPORTS;
    if (bundle?.before) {
      fallback = store.normalize(bundle.before, bundle.repoName, "verified_bundle");
      if (bundle.after) fallback.after = store.normalize(bundle.after, bundle.repoName, "verified_bundle");
    }
  } catch (error) { notice("演示报告读取失败：" + error.message, true); }
  const loaded = store.load({ fallback });
  const model = loaded.model;
  if (!loaded.ok) notice(loaded.message, true);
  if (!model) {
    notice("没有可读取的报告。请进入报告页导入 report.json。", true);
    return;
  }
  const report = model.report;
  const isDemo = model.source === "verified_bundle";
  const runtime = model.runtime === null ? "未记录" : model.runtime.toFixed(2) + " s";
  const comparison = model.after ? store.compare(model, model.after) : null;
  const currentRecords = store.records(report);

  function renderContext() {
    const context = make("section", undefined, "report-context");
    context.setAttribute("aria-label", "当前报告");
    const info = make("div", undefined, "context-info");
    const name = make(byId("homeFileTree") ? "button" : "strong", model.name);
    if (byId("homeFileTree")) { name.type = "button"; name.className = "report-picker-trigger"; name.id = "reportPickerTrigger"; name.setAttribute("aria-expanded", "false"); }
    name.title = model.name;
    info.append(make("span", isDemo ? "演示报告" : "本地导入", "source-pill"), name, make("span", statusText(report.manifest.status), "context-status"));
    const actions = make("div", undefined, "context-actions");
    const open = make("a", "管理报告", "text-action");
    open.href = "./reports.html";
    const download = make("button", "导出 JSON", "text-action");
    download.type = "button";
    download.addEventListener("click", () => {
      try {
        const url = URL.createObjectURL(new Blob([store.exportJSON(model)], { type: "application/json;charset=utf-8" }));
        const link = make("a");
        link.href = url;
        link.download = "docsync-report.json";
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      } catch (error) { notice("导出失败：" + error.message, true); }
    });
    actions.append(open, download);
    if (!isDemo) {
      const reset = make("button", "恢复演示", "text-action");
      reset.type = "button";
      reset.addEventListener("click", () => {
        const result = store.clear();
        if (result.ok) window.location.reload();
        else notice(result.message, true);
      });
      actions.append(reset);
    }
    context.append(info, actions);
    main.prepend(context);
    document.querySelectorAll("[data-source-footer]").forEach((element) => {
      element.textContent = isDemo ? "随包 CLI 演示报告 · 本地读取" : "当前会话导入报告 · 网页未重新验证";
    });
    document.querySelectorAll("[data-demo-only]").forEach((element) => { element.hidden = !isDemo; });
    document.querySelectorAll("[data-repo]").forEach((element) => { element.textContent = model.name; });
    document.querySelectorAll(".portal-nav .is-active").forEach((element) => element.setAttribute("aria-current", "page"));
  }

  function renderHome() {
    set("homeHead", short(report.snapshot.head_sha));
    set("homeRun", short(report.manifest.run_id));
    set("homeSchema", model.schema);
    set("consoleSchema", "SCHEMA " + model.schema);
    set("consoleSource", isDemo ? "DEMO REPORT" : "IMPORTED REPORT");
    set("homeMode", report.manifest.mode || "未记录");
    set("homeRuntime", runtime);
    set("homeStatus", statusText(report.manifest.status));
    set("homeFindingSummary", model.confirmedCount + " 条确认冲突 · " + (model.uncertainCount ?? "数量未知的") + " 条不确定项");
    set("homeSource", isDemo ? "随包演示，可直接查看" : "当前会话导入，结论沿用原报告");
  }


  function setupHome() {
    const tree = byId("homeFileTree");
    if (!tree) return;
    function empty(target, message) {
      const box = make("div", undefined, "project-empty");
      const icon = make("span", "▱"); icon.setAttribute("aria-hidden", "true");
      box.append(icon, make("p", message)); target.replaceChildren(box);
    }
    const files = list(report.snapshot.files);
    set("homeFileCount", files.length + " 个已记录文件 · 非完整仓库保证");
    if (!files.length) empty(tree, "暂无项目文件，导入包含快照文件的报告后显示。");
    else {
      const folders = new Map();
      for (const file of [...files].sort((a,b) => String(a.path).localeCompare(String(b.path)))) {
        const parts = String(file.path).split("/"); let parent = tree, key = "";
        for (const part of parts.slice(0,-1)) {
          key += part + "/";
          if (!folders.has(key)) {
            const folder = make("details", undefined, "repo-folder"); folder.open = true;
            folder.append(make("summary", "▸ " + part)); parent.append(folder); folders.set(key, folder);
          }
          parent = folders.get(key);
        }
        const row = make("div", undefined, "repo-file");
        row.append(make("span", "▤  " + parts.at(-1)), make("small", Number.isInteger(file.size) ? file.size + " B" : "大小未记录"));
        parent.append(row);
      }
    }
    const readme = byId("homeReadme");
    empty(readme, "报告未包含 README 全文，可选择此项目的本地 README 查看。");
    byId("readmeInput").addEventListener("change", async event => {
      const file = event.target.files[0]; if (!file) return;
      try {
        if (file.size > 2 * 1024 * 1024) throw Error("README 请控制在 2 MB 内。");
        const content = await file.text();
        readme.replaceChildren(make("p", "本地选择：" + file.name + " · 未校验与报告快照的一致性", "readme-source"), make("pre", content));
      } catch(error) { notice(error.message, true); }
      event.target.value = "";
    });
    const trigger = byId("reportPickerTrigger");
    const panel = make("section", undefined, "report-picker"); panel.id = "reportPicker"; panel.hidden = true;
    panel.setAttribute("aria-label", "筛选与切换报告"); trigger.setAttribute("aria-controls", panel.id);
    const search = make("input"); search.type = "search"; search.placeholder = "搜索仓库、报告名或运行 ID"; search.setAttribute("aria-label", "筛选报告");
    const options = make("div", undefined, "report-picker-options");
    const upload = make("input"); upload.type = "file"; upload.accept = ".json"; upload.multiple = true; upload.id = "homeReportsInput";
    const label = make("label", "添加本地报告（可多选）", "text-action"); label.htmlFor = upload.id; upload.className = "sr-only";
    const feedback = make("p", "报告仅保存在当前标签页会话。", "picker-feedback"); feedback.setAttribute("role", "status");
    panel.append(search, options, label, upload, feedback); trigger.closest(".report-context").after(panel);
    const catalogKey = "docsync.home.catalog.v1"; let choices = [];
    try { const raw = JSON.parse(sessionStorage.getItem(catalogKey) || "[]"); if (Array.isArray(raw)) choices = raw.map(item => store.normalize(item.report, item.name)); } catch { feedback.textContent = "历史列表不可用，请重新添加报告。"; }
    function add(item) {
      const index = choices.findIndex(entry => entry.report.manifest.run_id === item.report.manifest.run_id && entry.report.snapshot.repo_id === item.report.snapshot.repo_id);
      if (index < 0) choices.push(item); else choices[index] = item;
    }
    if (fallback) add(fallback); add(model);
    function renderOptions() {
      const query = search.value.toLowerCase().trim(); options.replaceChildren();
      for (const item of choices.filter(item => [item.name, item.report.snapshot.repo_id, item.report.manifest.run_id].join(" ").toLowerCase().includes(query))) {
        const button = make("button", undefined, "report-choice"); button.type = "button";
        button.append(make("strong", item.name), make("small", item.name + " · " + short(item.report.manifest.run_id)));
        button.addEventListener("click", () => {
          const result = store.save(item);
          if (result.ok) location.reload(); else feedback.textContent = result.message;
        }); options.append(button);
      }
      if (!options.childElementCount) options.append(make("p", "没有匹配的报告。"));
    }
    search.addEventListener("input", renderOptions);
    trigger.addEventListener("click", () => { panel.hidden = !panel.hidden; trigger.setAttribute("aria-expanded", String(!panel.hidden)); if (!panel.hidden) search.focus(); });
    panel.addEventListener("keydown", event => { if (event.key === "Escape") { panel.hidden = true; trigger.setAttribute("aria-expanded", "false"); trigger.focus(); } });
    upload.addEventListener("change", async () => {
      let added = 0; const errors = [];
      for (const file of upload.files) {
        try { if (file.size > store.MAX_REPORT_BYTES) throw Error("超过 10 MB"); add(store.normalize(JSON.parse(await file.text()), file.name)); added++; }
        catch(error) { errors.push(file.name + "：" + error.message); }
      }
      try { sessionStorage.setItem(catalogKey, JSON.stringify(choices.map(item => ({name:item.name, report:item.report})))); }
      catch { errors.push("会话空间不足，新增列表仅在当前页面有效。"); }
      feedback.textContent = "已添加 " + added + " 份报告。" + errors.join("；"); upload.value = ""; renderOptions();
    });
    renderOptions();
  }

  function renderData() {
    set("metricFiles", model.fileCount);
    set("metricFacts", model.factCount);
    set("metricFindings", model.confirmedCount);
    set("metricUncertain", model.uncertainCount);
    set("dataHead", report.snapshot.head_sha);
    set("dataSnapshot", report.snapshot.files_hash);
    set("dataRun", report.manifest.run_id);
    set("dataStatus", statusText(report.manifest.status));
    const fileRows = byId("fileRows");
    if (!fileRows) return;
    const files = list(report.snapshot.files);
    const search = byId("fileSearch");
    function renderFiles() {
      const query = (search?.value || "").trim().toLowerCase();
      const matches = files.filter((file) => (file.path + " " + (file.encoding || "")).toLowerCase().includes(query));
      fileRows.replaceChildren();
      for (const file of matches) {
        const row = make("tr");
        const filePath = make("td");
        filePath.append(make("strong", file.path));
        const hash = make("td");
        const code = make("code", short(file.blob_hash, 12, 8));
        code.title = file.blob_hash || "未记录";
        hash.append(code);
        row.append(filePath, make("td", file.encoding || "未记录"), make("td", Number.isInteger(file.size) ? file.size + " B" : "未记录"), hash);
        fileRows.append(row);
      }
      if (!matches.length) {
        const row = make("tr");
        const cell = make("td", query ? "没有匹配的文件。" : Array.isArray(report.snapshot.files) ? "此快照未列出文件。" : "报告未提供快照文件列表。", "empty-state");
        cell.colSpan = 4;
        row.append(cell);
        fileRows.append(row);
      }
      set("fileCountLabel", model.fileCount === null ? "文件数量未记录" : "显示 " + matches.length + " / " + files.length + " 个文件");
    }
    search?.addEventListener("input", renderFiles);
    renderFiles();
  }

  function spanLines(span) {
    if (!Number.isInteger(span?.start_line)) return "行号未记录";
    return "L" + span.start_line + (Number.isInteger(span.end_line) && span.end_line !== span.start_line ? "–" + span.end_line : "");
  }

  function renderCode() {
    const selector = byId("evidenceSelect");
    if (!selector) return;
    selector.replaceChildren();
    for (const [index, record] of currentRecords.entries()) {
      const option = make("option", (index + 1) + ". " + categoryText(record.category) + " · " + record.title);
      option.value = String(index);
      selector.append(option);
    }
    if (!currentRecords.length) selector.append(make("option", "此报告没有告警或待核对记录"));
    selector.disabled = !currentRecords.length;
    const requested = new URLSearchParams(window.location.search).get("record");
    const requestedIndex = currentRecords.findIndex((record) => record.key === requested);
    selector.value = String(requestedIndex < 0 ? 0 : requestedIndex);

    function renderEvidence() {
      const record = currentRecords[Number(selector.value)];
      const fact = record?.facts[0];
      const claim = record?.claim;
      const signature = fact?.fact_kind === "DEFAULT_VALUE" && fact.entity_id
        ? list(report.facts).find((item) => item.entity_id === fact.entity_id && item.fact_kind === "SIGNATURE" && typeof item.expression === "string")
        : null;
      const codeSource = signature || fact;
      const codeSpan = codeSource?.span || record?.finding?.evidence?.code;
      const docSpan = claim?.span || record?.finding?.evidence?.document;
      set("codePath", codeSpan?.path || "未提供代码证据");
      set("docPath", docSpan?.path || "未提供文档证据");
      set("codeLines", spanLines(codeSpan));
      set("docLines", spanLines(docSpan));
      set("codeHash", short(codeSpan?.blob_hash, 14, 8));
      set("docHash", short(docSpan?.blob_hash, 14, 8));
      set("codeView", typeof codeSource?.expression === "string" && codeSource.expression.length ? codeSource.expression : "报告未提供此记录的代码表达式。");
      set("docView", typeof claim?.quote === "string" && claim.quote.length ? claim.quote : "报告未提供此记录的文档原文。");
      set("evidenceState", record ? categoryText(record.category) : "暂无记录");
      set("evidenceReason", record?.reason || "没有告警不代表所有文档均已验证一致。请结合报告中的覆盖范围与诊断查看。");
      set("evidenceCodeLabel", fact ? (signature ? "报告中的函数定义" : "报告中的表达式") + " · " + (fact.subject || "") + (fact.property ? " · " + fact.property : "") : "代码事实缺失");
      const full = byId("openEvidenceReport");
      if (full) full.href = "./reports.html" + (record ? "?record=" + encodeURIComponent(record.key) : "");
    }
    selector.addEventListener("change", renderEvidence);
    renderEvidence();
  }

  function renderHistory() {
    const history = byId("runHistory");
    if (!history) return;
    history.replaceChildren();
    function entry(title, description, identity) {
      const item = make("li", undefined, "history-item");
      item.append(make("h3", title), make("p", description));
      if (identity) item.append(make("code", identity));
      history.append(item);
    }
    const snapshotMode = report.snapshot.mode === "working-tree" ? "工作区快照" : report.snapshot.mode === "commit" ? "提交快照" : "快照模式未记录";
    entry("源码快照", snapshotMode + "；文件内容以报告中的快照哈希为准。", report.snapshot.head_sha);
    entry("本次扫描 · " + statusText(report.manifest.status), "确认冲突 " + model.confirmedCount + " 条；不确定项 " + (model.uncertainCount ?? "未记录") + "；耗时 " + runtime + "。", report.manifest.run_id);
    if (model.patchCount === null) entry("补丁记录缺失", "原报告没有 patches 字段，无法确定是否生成补丁。");
    else if (!model.patchCount) entry("未生成补丁", "该报告未列出补丁建议。");
    else entry("补丁建议 · " + model.patchCount + " 项", "生成补丁不等于已经应用；以下状态沿用原始报告。", list(report.patches).map((patch) => patch.patch_id + " · " + (patch.validation || "校验状态未记录")).join("\n"));
    if (!model.after) {
      entry("尚未导入复扫报告", "在报告页导入另一次运行的 report.json 后，可比较前后结果。");
    } else if (!comparison.compatible) {
      entry("复扫报告不可直接比较", comparison.reasons.join(" "), model.after.report.manifest.run_id);
    } else {
      const after = model.after;
      entry("后续扫描 · " + statusText(after.report.manifest.status), "确认冲突 " + model.confirmedCount + " → " + after.confirmedCount + "；不确定项 " + (model.uncertainCount ?? "未记录") + " → " + (after.uncertainCount ?? "未记录") + "。可比性基于报告元数据，不能据此证明具体补丁已应用。", after.report.manifest.run_id);
    }
  }

  renderContext();
  renderHome();
  setupHome();
  renderData();
  renderCode();
  renderHistory();
})();
