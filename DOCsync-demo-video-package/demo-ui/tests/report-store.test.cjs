"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const store = require("../report-store.js");

function report(overrides = {}) {
  return {
    schema_version: "2.0",
    manifest: { schema_version: "2.0", run_id: "before", status: "COMPLETED", mode: "rules", config_hash: "config", enabled_types: ["DEFAULT_VALUE", "SIGNATURE"] },
    snapshot: { repo_id: "repo", head_sha: "head", mode: "commit", files: [] },
    findings: [], facts: [], claims: [], judgments: [], patches: [], rejected: [],
    ...overrides,
  };
}

function finding(id, overrides = {}) {
  return { finding_id: id, claim_id: "claim-" + id, status: "INCONSISTENT", verification_status: "VERIFIED", ignored: false, ...overrides };
}

function memoryStorage() {
  const items = new Map();
  return { getItem: (key) => items.has(key) ? items.get(key) : null, setItem: (key, value) => items.set(key, String(value)), removeItem: (key) => items.delete(key) };
}

test("bundled before/after reports are readable and their raw bytes are never modified", () => {
  for (const file of ["before-report.json", "after-report.json"]) {
    const original = fs.readFileSync(path.join(__dirname, "../../artifacts", file), "utf8");
    const input = JSON.parse(original);
    const before = JSON.stringify(input);
    const model = store.normalize(input, file, "verified_bundle");
    assert.equal(JSON.stringify(input), before);
    assert.equal(model.validation, "structure_only");
    assert.equal(model.confirmedCount, file.startsWith("before") ? 1 : 0);
    assert.equal(model.uncertainCount, 0);
    assert.equal(model.patchCount, file.startsWith("before") ? 1 : 0);
  }
});

test("schema 1.0 and version only in manifest remain readable", () => {
  const legacy = report({ schema_version: "1.0" });
  legacy.manifest.schema_version = "1.0";
  assert.equal(store.normalize(legacy).schema, "1.0");
  delete legacy.schema_version;
  assert.equal(store.normalize(legacy).schema, "1.0");
});

test("missing optional records and runtime are unknown, not zero", () => {
  const input = report();
  for (const key of ["judgments", "patches", "facts", "claims", "rejected"]) delete input[key];
  delete input.snapshot.files;
  const model = store.normalize(input);
  for (const key of ["uncertainCount", "patchCount", "runtime", "factCount", "claimCount", "rejectedCount", "fileCount"]) assert.equal(model[key], null, key);
  assert.equal(model.confirmedCount, 0);
  assert.equal(model.warnings.length, 5);
});

test("mixed findings distinguish verified, ignored, unverified, and uncertain decisions", () => {
  const input = report({
    findings: [finding("a"), finding("b", { ignored: true }), finding("c", { verification_status: "UNVERIFIED" }), finding("d", { status: "UNCERTAIN" })],
    judgments: [{ claim_id: "one", decision: "UNCERTAIN" }, { claim_id: "two", decision: "INSUFFICIENT" }, { claim_id: "three", decision: "CONSISTENT" }],
  });
  const summary = store.summarize(input);
  assert.equal(summary.confirmedCount, 1);
  assert.equal(summary.ignoredCount, 1);
  assert.equal(summary.unverifiedCount, 1);
  assert.equal(summary.uncertainCount, 2);
  assert.deepEqual(input.findings.map(store.classify), ["confirmed", "ignored", "unverified", "uncertain"]);
});

test("an omitted finding verification status never becomes confirmed", () => {
  const item = finding("a");
  delete item.verification_status;
  const model = store.normalize(report({ findings: [item] }));
  assert.equal(model.confirmedCount, 0);
  assert.equal(model.unverifiedCount, 1);
  assert.equal(model.warnings.length, 1);
});

test("uncertainty counts the union of rejected and uncertain claim IDs without duplicates", () => {
  const input = report({
    judgments: [{ claim_id: "a", decision: "UNCERTAIN" }, { claim_id: "a", decision: "UNCERTAIN" }, { claim_id: "b", decision: "INCONSISTENT" }],
    rejected: [{ claim_id: "a", reason: "evidence missing" }, { claim_id: "b", reason: "verifier rejected" }, { claim_id: "c", reason: "reference missing" }],
  });
  assert.equal(store.summarize(input).uncertainCount, 3);
  const records = store.records(input);
  assert.equal(records.length, 3);
  assert.equal(records[1].category, "uncertain");
  assert.equal(records[1].kind, "rejected");
  assert.equal(records[1].reason, "verifier rejected");
  assert.equal(records[2].judgment, null);
  delete input.rejected;
  assert.equal(store.summarize(input).uncertainCount, null);
});

test("invalid containers, versions, and report identities are rejected", () => {
  for (const input of [null, [], "{}", {}, report({ schema_version: "9.0" }), report({ snapshot: [] }), report({ findings: null }), report({ judgments: [{}] }), report({ patches: [null] })]) {
    assert.throws(() => store.normalize(input), { name: "ReportValidationError" });
  }
  const mismatch = report();
  mismatch.manifest.schema_version = "1.0";
  assert.throws(() => store.normalize(mismatch), /版本不一致/);
  const badDiagnostic = report();
  badDiagnostic.manifest.diagnostics = [null];
  assert.throws(() => store.normalize(badDiagnostic), /diagnostics/);
});

test("malformed values, intervals, booleans, and duplicate IDs are rejected", () => {
  const inputs = [
    report({ findings: [finding("same"), finding("same")] }),
    report({ findings: [finding("a", { ignored: "false" })] }),
    report({ findings: [finding("a", { fact_ids: "fact" })] }),
    report({ facts: [{ fact_id: "f", span: { start_line: 10, end_line: 2 } }] }),
    report({ facts: [{ fact_id: "f", typed_value: { type: "int", canonical: 60 } }] }),
    report({ claims: [{ claim_id: "c", quote: { html: "unsafe" } }] }),
    report({ patches: [{ patch_id: "p", diff: {} }] }),
  ];
  for (const input of inputs) assert.throws(() => store.normalize(input), { name: "ReportValidationError" });
  const nonfinite = report();
  nonfinite.manifest.stage_seconds = { total: Infinity };
  assert.throws(() => store.normalize(nonfinite), /非负秒数/);
});

test("records include uncertainty without inventing a finding or duplicating an existing one", () => {
  const input = report({
    findings: [finding("a")],
    claims: [{ claim_id: "claim-a", subject: "connect", predicate: "timeout" }, { claim_id: "claim-b", subject: "upload", predicate: "retries", span: { path: "README.md" } }],
    facts: [{ fact_id: "fact-b", subject: "upload" }],
    judgments: [{ claim_id: "claim-a", decision: "UNCERTAIN" }, { claim_id: "claim-b", decision: "INSUFFICIENT", fact_ids: ["fact-b"], reason_text: "动态值" }],
    patches: [{ patch_id: "patch-a", finding_ids: ["a"], diff: "diff" }],
  });
  const rows = store.records(input);
  assert.equal(rows.length, 2);
  assert.equal(rows[0].patch.patch_id, "patch-a");
  assert.equal(rows[1].finding, null);
  assert.equal(rows[1].kind, "judgment");
  assert.equal(rows[1].category, "uncertain");
  assert.equal(rows[1].title, "upload · retries");
  assert.equal(rows[1].facts[0].fact_id, "fact-b");
  assert.equal(rows[1].path, "README.md");
  assert.equal(rows[1].reason, "动态值");
});

test("snapshot commit to working-tree rescan is comparable on the same base", () => {
  const before = report();
  const after = structuredClone(before);
  after.manifest.run_id = "after";
  after.manifest.enabled_types.reverse();
  after.snapshot.mode = "working-tree";
  after.snapshot.files_hash = "changed";
  assert.deepEqual(store.compare(store.normalize(before), store.normalize(after)), { compatible: true, reasons: [] });
});

test("comparison rejects different repository, base, config, scope, mode, or same run", () => {
  const before = report();
  for (const mutate of [
    (after) => { after.snapshot.repo_id = "other"; },
    (after) => { after.snapshot.head_sha = "other"; },
    (after) => { after.manifest.config_hash = "other"; },
    (after) => { after.manifest.mode = "hybrid"; },
    (after) => { after.manifest.enabled_types = []; },
    (after) => { delete after.manifest.enabled_types; },
    (after) => { after.manifest.run_id = "before"; },
  ]) {
    const after = structuredClone(before);
    after.manifest.run_id = "after";
    mutate(after);
    assert.equal(store.compare(before, after).compatible, false);
    assert.ok(store.compare(before, after).reasons.length);
  }
});

test("all pages can restore the same report and an optional rescan", () => {
  const storage = memoryStorage();
  const model = store.normalize(report(), "my-report.json");
  const after = report();
  after.manifest.run_id = "after";
  model.after = store.normalize(after, "after.json");
  assert.equal(store.save(model, { storage }).code, "SAVED");
  const restored = store.load({ storage });
  assert.equal(restored.ok, true);
  assert.equal(restored.restored, true);
  assert.equal(restored.model.name, "my-report.json");
  assert.equal(restored.model.after.report.manifest.run_id, "after");
  assert.equal(restored.model.source, "local_import");
  assert.deepEqual(restored.model.report, model.report);
});

test("session data cannot promote a report to trusted demo status", () => {
  const storage = memoryStorage();
  const model = store.normalize(report(), "local.json", "verified_bundle");
  store.save(model, { storage });
  assert.equal(store.load({ storage }).model.source, "local_import");
});

test("fresh session uses the caller's fallback and clear only removes this app key", () => {
  const storage = memoryStorage();
  storage.setItem("unrelated", "keep");
  const fallback = store.normalize(report(), "demo", "verified_bundle");
  assert.equal(store.load({ storage, fallback }).model, fallback);
  store.save(store.normalize(report(), "local"), { storage });
  assert.equal(store.clear({ storage }).ok, true);
  assert.equal(store.load({ storage, fallback }).model, fallback);
  assert.equal(storage.getItem("unrelated"), "keep");
});

test("disabled storage returns a useful status instead of crashing the page", () => {
  const fallback = store.normalize(report(), "demo");
  const storage = { getItem() { throw new Error("denied"); }, setItem() { throw new Error("denied"); }, removeItem() { throw new Error("denied"); } };
  assert.equal(store.save(fallback, { storage }).code, "STORAGE_UNAVAILABLE");
  assert.equal(store.load({ fallback, storage }).model, fallback);
  assert.equal(store.clear({ storage }).ok, false);
  assert.equal(store.load({ storage: null }).code, "STORAGE_UNAVAILABLE");
});

test("quota failure clears stale report so another page cannot show the wrong project", () => {
  const storage = memoryStorage();
  store.save(store.normalize(report(), "old"), { storage });
  storage.setItem = () => { const error = new Error("full"); error.name = "QuotaExceededError"; throw error; };
  const result = store.save(store.normalize(report(), "new"), { storage });
  assert.equal(result.code, "STORAGE_FULL");
  assert.equal(result.persisted, false);
  assert.equal(storage.getItem(store.STORAGE_KEY), null);
});

test("invalid saved JSON and invalid imported models have distinct errors", () => {
  const storage = memoryStorage();
  const fallback = store.normalize(report(), "demo");
  storage.setItem(store.STORAGE_KEY, "{bad json");
  const loaded = store.load({ storage, fallback });
  assert.equal(loaded.code, "INVALID_SESSION");
  assert.equal(loaded.model, fallback);
  assert.equal(store.save({ report: {} }, { storage }).code, "INVALID_REPORT");
});

test("export preserves report claims and does not serialize UI state", () => {
  const input = report({ claims: [{ claim_id: "c", quote: "<img src=x onerror=alert(1)>" }] });
  const model = store.normalize(input, "name");
  const exported = JSON.parse(store.exportJSON(model));
  assert.deepEqual(exported, input);
  assert.equal(exported.source, undefined);
});

test("browser global export works without CommonJS or sessionStorage", () => {
  const context = vm.createContext({});
  vm.runInContext(fs.readFileSync(path.join(__dirname, "../report-store.js"), "utf8"), context);
  assert.equal(typeof context.DocSyncReportStore.normalize, "function");
  assert.equal(context.DocSyncReportStore.load().code, "STORAGE_UNAVAILABLE");
});

test("invalid uncertainty descriptions cannot reach text rendering or record search", () => {
  for (const value of [{ toString: null, valueOf: null }, [], 123, false]) {
    const input = report({ judgments: [{ claim_id: "c", decision: "UNCERTAIN", uncertainty_reason: value }] });
    assert.throws(() => store.normalize(input), /uncertainty_reason/);
  }
  for (const value of [null, "运行时求值"]) {
    const input = report({ judgments: [{ claim_id: "c", decision: "UNCERTAIN", uncertainty_reason: value }] });
    const model = store.normalize(input);
    assert.equal(model.uncertainCount, 1);
    assert.equal(typeof store.records(input)[0].reason, "string");
  }
});

test("record metadata consumed by filters rejects nested values", () => {
  const poison = { toString: null, valueOf: null };
  assert.throws(() => store.normalize(report({ judgments: [{ claim_id: "c", decision: "UNCERTAIN", drift_type: poison }] })), /drift_type/);
  for (const key of ["fact_kind", "entity_id", "value_state"]) {
    assert.throws(() => store.normalize(report({ facts: [{ fact_id: "f", [key]: poison }] })), new RegExp(key));
  }
});

test("malformed import preserves the previous stored report", () => {
  const storage = memoryStorage();
  store.save(store.normalize(report(), "keep-this-report.json"), { storage });
  const invalid = report({ judgments: [{ claim_id: "c", decision: "UNCERTAIN", uncertainty_reason: { toString: null, valueOf: null } }] });
  assert.equal(store.save({ report: invalid, name: "bad-report.json" }, { storage }).code, "INVALID_REPORT");
  assert.equal(store.load({ storage }).model.name, "keep-this-report.json");
});

test("a corrupt saved rescan cannot replace a valid imported report with demo data", () => {
  const storage = memoryStorage();
  const fallback = store.normalize(report(), "demo");
  store.save(store.normalize(report(), "my-report.json"), { storage });
  const saved = JSON.parse(storage.getItem(store.STORAGE_KEY));
  saved.after = { report: {}, name: "broken-rescan.json" };
  storage.setItem(store.STORAGE_KEY, JSON.stringify(saved));
  const result = store.load({ storage, fallback });
  assert.equal(result.ok, false);
  assert.equal(result.restored, true);
  assert.equal(result.code, "INVALID_RESCAN_SESSION");
  assert.equal(result.model.name, "my-report.json");
  assert.equal(result.model.after, null);
  assert.match(result.message, /复扫/);
});
