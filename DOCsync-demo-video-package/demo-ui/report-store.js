/* Local report data shared by the viewer pages. No network or report execution. */
(function (root, factory) {
  "use strict";
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.DocSyncReportStore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";

  const STORAGE_KEY = "docsync.viewer.report.v1";
  const MAX_REPORT_BYTES = 10 * 1024 * 1024;
  const DECISIONS = new Set(["CONSISTENT", "INCONSISTENT", "UNCERTAIN", "INSUFFICIENT", "SKIPPED"]);
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const object = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
  const list = (value) => Array.isArray(value) ? value : [];
  const nonempty = (value) => typeof value === "string" && value.trim().length > 0;
  const finite = (value) => typeof value === "number" && Number.isFinite(value);
  const uncertain = (record) => ["UNCERTAIN", "INSUFFICIENT"].includes(record?.decision || record?.status);

  function invalid(path, description) {
    const error = new Error(path + "：" + description);
    error.name = "ReportValidationError";
    throw error;
  }

  function requireObject(value, path) {
    if (!object(value)) invalid(path, "应为 JSON 对象");
  }

  function optionalString(value, key, path, nullable = false) {
    if (own(value, key) && typeof value[key] !== "string" && !(nullable && value[key] === null)) {
      invalid(path + "." + key, "应为文本" + (nullable ? "或 null" : ""));
    }
  }

  function stringList(value, key, path) {
    if (own(value, key) && (!Array.isArray(value[key]) || value[key].some((item) => typeof item !== "string"))) {
      invalid(path + "." + key, "应为文本列表");
    }
  }

  function recordsList(value, key, path) {
    if (!own(value, key)) return null;
    if (!Array.isArray(value[key]) || value[key].some((item) => !object(item))) {
      invalid(path + "." + key, "应为记录对象列表");
    }
    return value[key];
  }

  function validateSpan(span, path) {
    requireObject(span, path);
    optionalString(span, "path", path);
    optionalString(span, "blob_hash", path);
    for (const key of ["start_line", "end_line", "start_byte", "end_byte"]) {
      if (own(span, key) && (!Number.isSafeInteger(span[key]) || span[key] < (key.endsWith("line") ? 1 : 0))) {
        invalid(path + "." + key, "应为有效的位置整数");
      }
    }
    for (const kind of ["line", "byte"]) {
      if (span["start_" + kind] > span["end_" + kind]) invalid(path, "起始位置不能大于结束位置");
    }
  }

  function validateValue(value, path) {
    if (value === null) return;
    requireObject(value, path);
    if (typeof value.canonical !== "string" || typeof value.type !== "string") {
      invalid(path, "值记录需包含 type 与 canonical 文本");
    }
  }

  function uniqueIds(items, key, path) {
    const ids = new Set();
    for (let index = 0; index < items.length; index += 1) {
      const id = items[index][key];
      if (!nonempty(id)) invalid(path + "[" + index + "]." + key, "缺少记录标识");
      if (ids.has(id)) invalid(path, "记录标识重复：" + id);
      ids.add(id);
    }
  }

  function validate(report) {
    requireObject(report, "report");
    requireObject(report.manifest, "manifest");
    requireObject(report.snapshot, "snapshot");
    const schema = report.schema_version ?? report.manifest.schema_version;
    if (!["1.0", "2.0"].includes(schema)) invalid("schema_version", "仅支持 DocSync 1.0 或 2.0 报告");
    if (own(report, "schema_version") && own(report.manifest, "schema_version") && report.schema_version !== report.manifest.schema_version) {
      invalid("schema_version", "报告与 manifest 的版本不一致");
    }
    if (!nonempty(report.manifest.run_id)) invalid("manifest.run_id", "缺少运行标识");
    if (!["COMPLETED", "PARTIAL", "FAILED"].includes(report.manifest.status)) invalid("manifest.status", "无法识别运行状态");
    if (!nonempty(report.snapshot.head_sha)) invalid("snapshot.head_sha", "缺少源代码提交标识");
    if (!Array.isArray(report.findings)) invalid("findings", "缺少告警列表，请导入完整的 report.json");

    for (const key of ["entities", "facts", "claims", "candidates", "judgments", "findings", "rejected", "patches"]) {
      recordsList(report, key, "report");
    }
    for (const [key, id] of [["entities", "entity_id"], ["facts", "fact_id"], ["claims", "claim_id"], ["findings", "finding_id"], ["patches", "patch_id"]]) {
      if (Array.isArray(report[key])) uniqueIds(report[key], id, key);
    }
    for (const key of ["repo_id", "head_sha", "files_hash", "mode"]) optionalString(report.snapshot, key, "snapshot");
    for (const key of ["mode", "config_hash"]) optionalString(report.manifest, key, "manifest");
    stringList(report.manifest, "enabled_types", "manifest");
    for (const [index, diagnostic] of list(recordsList(report.manifest, "diagnostics", "manifest")).entries()) {
      for (const key of ["code", "message", "stage"]) optionalString(diagnostic, key, "manifest.diagnostics[" + index + "]");
    }
    if (own(report.manifest, "stage_seconds")) {
      requireObject(report.manifest.stage_seconds, "manifest.stage_seconds");
      for (const [key, value] of Object.entries(report.manifest.stage_seconds)) {
        if (!finite(value) || value < 0) invalid("manifest.stage_seconds." + key, "应为非负秒数");
      }
    }
    if (own(report.manifest, "usage")) {
      requireObject(report.manifest.usage, "manifest.usage");
      for (const [key, value] of Object.entries(report.manifest.usage)) {
        if (!Number.isSafeInteger(value) || value < 0) invalid("manifest.usage." + key, "应为非负整数");
      }
    }
    for (const [index, file] of list(recordsList(report.snapshot, "files", "snapshot")).entries()) {
      const path = "snapshot.files[" + index + "]";
      if (!nonempty(file.path)) invalid(path, "缺少文件路径");
      optionalString(file, "blob_hash", path);
      optionalString(file, "encoding", path);
      if (own(file, "size") && (!Number.isSafeInteger(file.size) || file.size < 0)) invalid(path + ".size", "应为非负字节数");
    }
    for (const [index, finding] of report.findings.entries()) {
      const path = "findings[" + index + "]";
      for (const key of ["claim_id", "status", "verification_status", "drift_type", "severity"]) optionalString(finding, key, path);
      stringList(finding, "fact_ids", path);
      if (own(finding, "status") && !DECISIONS.has(finding.status)) invalid(path + ".status", "无法识别判断状态");
      if (own(finding, "ignored") && typeof finding.ignored !== "boolean") invalid(path + ".ignored", "应为 true 或 false");
      optionalString(finding, "ignore_reason", path, true);
      optionalString(finding, "ignore_expires", path, true);
      if (own(finding, "evidence")) {
        requireObject(finding.evidence, path + ".evidence");
        for (const key of ["rule_id", "snapshot_hash", "head_sha", "entity_id"]) optionalString(finding.evidence, key, path + ".evidence");
        for (const key of ["code", "document"]) if (own(finding.evidence, key)) validateSpan(finding.evidence[key], path + ".evidence." + key);
      }
    }
    for (const key of ["judgments", "rejected"]) {
      for (const [index, judgment] of list(report[key]).entries()) {
        const path = key + "[" + index + "]";
        if (!nonempty(judgment.claim_id)) invalid(path + ".claim_id", "缺少声明标识");
        if (key === "judgments" && !DECISIONS.has(judgment.decision)) invalid(path + ".decision", "缺少或无法识别判断结果");
        stringList(judgment, "fact_ids", path);
        for (const field of ["reason_text", "reason_code", "reason"]) optionalString(judgment, field, path);
        for (const field of ["uncertainty_reason", "model_run_id", "drift_type"]) optionalString(judgment, field, path, true);
      }
    }
    for (const key of ["entities", "facts", "claims"]) {
      for (const [index, item] of list(report[key]).entries()) {
        const path = key + "[" + index + "]";
        for (const field of ["subject", "property", "predicate", "quote", "expression", "kind", "qualified_name", "entity_id", "fact_kind", "value_state"]) optionalString(item, field, path);
        if (own(item, "span")) validateSpan(item.span, path + ".span");
        for (const field of ["typed_value", "value"]) if (own(item, field)) validateValue(item[field], path + "." + field);
      }
    }
    for (const [index, patch] of list(report.patches).entries()) {
      const path = "patches[" + index + "]";
      stringList(patch, "finding_ids", path);
      stringList(patch, "validation_details", path);
      optionalString(patch, "diff", path);
      optionalString(patch, "validation", path);
      if (own(patch, "requires_review") && typeof patch.requires_review !== "boolean") invalid(path + ".requires_review", "应为 true 或 false");
      for (const [editIndex, edit] of list(recordsList(patch, "edits", path)).entries()) {
        const editPath = path + ".edits[" + editIndex + "]";
        if (own(edit, "span")) validateSpan(edit.span, editPath + ".span");
        optionalString(edit, "old_text", editPath);
        optionalString(edit, "new_text", editPath);
      }
    }
    return schema;
  }

  function confirmed(finding) {
    return Boolean(finding && finding.status === "INCONSISTENT" && finding.verification_status === "VERIFIED" && finding.ignored !== true);
  }

  function classify(finding) {
    if (finding?.ignored === true) return "ignored";
    if (confirmed(finding)) return "confirmed";
    if (uncertain(finding)) return "uncertain";
    if (finding?.status === "INCONSISTENT" || !finding?.status) return "unverified";
    return "other";
  }

  function uncertainJudgments(report) {
    return [...new Map(list(report?.judgments).filter(uncertain).map((judgment) => [judgment.claim_id, judgment])).values()];
  }

  function summarize(report) {
    const findings = list(report?.findings);
    const count = (key) => Array.isArray(report?.[key]) ? report[key].length : null;
    return {
      confirmedCount: Array.isArray(report?.findings) ? findings.filter(confirmed).length : null,
      ignoredCount: Array.isArray(report?.findings) ? findings.filter((finding) => finding.ignored === true).length : null,
      uncertainCount: Array.isArray(report?.judgments) && Array.isArray(report?.rejected)
        ? new Set([...uncertainJudgments(report), ...report.rejected].map((item) => item.claim_id)).size : null,
      unverifiedCount: Array.isArray(report?.findings) ? findings.filter((finding) => classify(finding) === "unverified").length : null,
      findingCount: count("findings"), patchCount: count("patches"), factCount: count("facts"), claimCount: count("claims"),
      rejectedCount: count("rejected"), fileCount: Array.isArray(report?.snapshot?.files) ? report.snapshot.files.length : null,
      runtime: finite(report?.manifest?.stage_seconds?.total) ? report.manifest.stage_seconds.total : null,
    };
  }

  function normalize(report, name, source = "local_import") {
    const schema = validate(report);
    const warnings = [];
    for (const key of ["facts", "claims", "judgments", "patches", "rejected"]) {
      if (!Array.isArray(report[key])) warnings.push("报告未记录 " + key + "，相关数量和详情未知。");
    }
    if (report.findings.some((item) => !item.status || !item.verification_status)) warnings.push("部分告警未记录判断或验证状态，不计入已确认冲突。");
    return {
      report,
      name: nonempty(name) ? name : report.snapshot.repo_id || "本地报告",
      source,
      schema,
      findings: [...report.findings].sort((a, b) => Number(confirmed(b)) - Number(confirmed(a))),
      ...summarize(report),
      after: null,
      warnings,
      validation: "structure_only",
    };
  }

  function records(report) {
    const claimMap = new Map(list(report?.claims).map((claim) => [claim.claim_id, claim]));
    const factMap = new Map(list(report?.facts).map((fact) => [fact.fact_id, fact]));
    const judgments = list(report?.judgments);
    const findings = [...list(report?.findings)].sort((a, b) => Number(confirmed(b)) - Number(confirmed(a)));
    const represented = new Set(findings.map((finding) => finding.claim_id));
    const rejections = new Map(list(report?.rejected).map((item) => [item.claim_id, item]));
    function makeRecord(finding, judgment, index, rejection = null) {
      const claim = claimMap.get(finding?.claim_id || judgment?.claim_id || rejection?.claim_id) || null;
      const facts = list(finding?.fact_ids || judgment?.fact_ids).map((id) => factMap.get(id)).filter(Boolean);
      const patch = finding && !finding.ignored ? list(report?.patches).find((item) => list(item.finding_ids).includes(finding.finding_id)) || null : null;
      const subject = claim?.subject || facts[0]?.subject;
      const predicate = claim?.predicate && claim.predicate !== "__signature__" ? claim.predicate : null;
      return {
        key: finding ? "finding:" + finding.finding_id : (rejection ? "rejected:" + rejection.claim_id : "judgment:" + judgment.claim_id) + ":" + index,
        kind: finding ? "finding" : rejection ? "rejected" : "judgment",
        category: finding ? classify(finding) : "uncertain",
        finding, judgment, rejection, claim, facts, patch,
        title: [subject, predicate].filter(Boolean).join(" · ") || finding?.drift_type || judgment?.reason_code || "待核对记录",
        path: finding?.evidence?.document?.path || claim?.span?.path || facts[0]?.span?.path || "",
        reason: rejection?.reason || judgment?.reason_text || judgment?.uncertainty_reason || finding?.ignore_reason || "报告未提供判断说明",
      };
    }
    const unresolved = new Map(uncertainJudgments(report).map((judgment) => [judgment.claim_id, judgment]));
    for (const claimId of rejections.keys()) {
      if (!unresolved.has(claimId)) unresolved.set(claimId, judgments.find((judgment) => judgment.claim_id === claimId) || null);
    }
    return [
      ...findings.map((finding, index) => makeRecord(finding, judgments.find((judgment) => judgment.claim_id === finding.claim_id) || null, index)),
      ...[...unresolved].filter(([claimId]) => !represented.has(claimId)).map(([claimId, judgment], index) => makeRecord(null, judgment, index, rejections.get(claimId) || null)),
    ];
  }

  function compare(beforeModel, afterModel) {
    const before = beforeModel?.report || beforeModel;
    const after = afterModel?.report || afterModel;
    const reasons = [];
    if (!object(before?.snapshot) || !object(after?.snapshot) || !object(before?.manifest) || !object(after?.manifest)) {
      return { compatible: false, reasons: ["缺少可比较的运行与快照记录。"] };
    }
    for (const [section, key, label] of [
      ["snapshot", "repo_id", "仓库标识"], ["snapshot", "head_sha", "基础提交"],
      ["manifest", "mode", "扫描模式"], ["manifest", "config_hash", "扫描配置"],
    ]) {
      if (!nonempty(before[section][key]) || !nonempty(after[section][key])) reasons.push(label + "缺失，无法确认可比性。");
      else if (before[section][key] !== after[section][key]) reasons.push(label + "不同。");
    }
    const beforeTypes = before.manifest.enabled_types;
    const afterTypes = after.manifest.enabled_types;
    if (!Array.isArray(beforeTypes) || !Array.isArray(afterTypes)) reasons.push("启用的检查类型缺失，无法确认扫描范围。");
    else if (JSON.stringify([...new Set(beforeTypes)].sort()) !== JSON.stringify([...new Set(afterTypes)].sort())) reasons.push("启用的检查类型不同。");
    if (!nonempty(before.manifest.run_id) || !nonempty(after.manifest.run_id)) reasons.push("运行标识缺失。");
    else if (before.manifest.run_id === after.manifest.run_id) reasons.push("两份报告来自同一次运行，不能作为复扫记录。");
    return { compatible: reasons.length === 0, reasons };
  }

  function storageFor(options) {
    const storage = own(options, "storage") ? options.storage : root.sessionStorage;
    if (!storage || typeof storage.getItem !== "function" || typeof storage.setItem !== "function" || typeof storage.removeItem !== "function") {
      throw new Error("sessionStorage is unavailable");
    }
    return storage;
  }

  function storageFailure(error) {
    const quota = error?.name === "QuotaExceededError" || error?.code === 22 || error?.code === 1014;
    return {
      ok: false, persisted: false,
      code: quota ? "STORAGE_FULL" : "STORAGE_UNAVAILABLE",
      message: quota ? "浏览器会话空间不足，报告仅在当前页面可用；切换页面后请重新导入。" : "浏览器未允许保存会话，报告仅在当前页面可用；切换页面后请重新导入。",
    };
  }

  function save(model, options = {}) {
    let payload;
    try {
      normalize(model?.report, model?.name);
      if (model.after) normalize(model.after.report, model.after.name);
      payload = JSON.stringify({
        version: 1, name: model.name, report: model.report,
        after: model.after ? { name: model.after.name, report: model.after.report } : null,
      });
    } catch (error) {
      return { ok: false, persisted: false, code: "INVALID_REPORT", message: "报告无法保存：" + error.message };
    }
    let storage;
    try {
      storage = storageFor(options);
      storage.setItem(STORAGE_KEY, payload);
      return { ok: true, persisted: true, code: "SAVED", message: "报告已保存在当前浏览器会话，各页面将使用同一份数据。" };
    } catch (error) {
      // Do not let another page silently resurrect an older report after a failed import.
      try { storage?.removeItem(STORAGE_KEY); } catch { /* Storage remains unavailable. */ }
      return storageFailure(error);
    }
  }

  function load(options = {}) {
    const fallback = options.fallback || null;
    let raw;
    try { raw = storageFor(options).getItem(STORAGE_KEY); }
    catch (error) { return { ...storageFailure(error), model: fallback, restored: false }; }
    if (raw === null) return { ok: true, model: fallback, restored: false, code: "EMPTY", message: "当前会话没有导入报告。" };
    try {
      const stored = JSON.parse(raw);
      if (!object(stored) || stored.version !== 1) invalid("session", "无法识别保存格式");
      const model = normalize(stored.report, stored.name, "local_import");
      if (stored.after !== null && stored.after !== undefined) {
        try {
          requireObject(stored.after, "session.after");
          model.after = normalize(stored.after.report, stored.after.name, "local_import");
        } catch (error) {
          return { ok: false, model, restored: true, code: "INVALID_RESCAN_SESSION", message: "复扫记录无法恢复，当前主报告已保留。请重新导入复扫报告：" + error.message };
        }
      }
      return { ok: true, model, restored: true, code: "RESTORED", message: "已恢复本次浏览器会话导入的报告。" };
    } catch (error) {
      return { ok: false, model: fallback, restored: false, code: "INVALID_SESSION", message: "保存的报告无法读取，请重新导入或清除会话：" + error.message };
    }
  }

  function clear(options = {}) {
    try {
      storageFor(options).removeItem(STORAGE_KEY);
      return { ok: true, persisted: false, code: "CLEARED", message: "已清除当前会话中的导入报告和复扫报告。" };
    } catch (error) { return storageFailure(error); }
  }

  function exportJSON(model) {
    const report = model?.report || model;
    validate(report);
    return JSON.stringify(report, null, 2) + "\n";
  }

  return Object.freeze({ STORAGE_KEY, MAX_REPORT_BYTES, normalize, confirmed, classify, summarize, uncertainJudgments, records, compare, save, load, clear, exportJSON });
});
