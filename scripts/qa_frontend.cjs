#!/usr/bin/env node
/** Real-browser smoke checks for the offline DocSync report workspace.
 * Install/use Playwright separately, then:
 *   node scripts/qa_frontend.cjs --browser /path/to/chrome --out runs/frontend-qa
 * Use --base-url http://127.0.0.1:PORT/ to test a separately started local server.
 * Optional: DOCSYNC_PLAYWRIGHT_PATH points to an existing playwright package.
 * All report mutations below are synthetic QA fixtures, never benchmark labels.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const http = require('node:http');
const { pathToFileURL } = require('node:url');

const repo = path.resolve(__dirname, '..');
const ui = path.join(repo, 'DOCsync-demo-video-package', 'demo-ui');
const artifacts = path.join(repo, 'DOCsync-demo-video-package', 'artifacts');
const argv = process.argv.slice(2);
const reportOnly = argv.includes('--report-only');
const visualOnly = argv.includes('--visual-only');
const option = (name, fallback) => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : fallback;
};
const output = path.resolve(option('--out', path.join(repo, 'runs', 'frontend-qa')));
const checks = [];
const exceptions = [];
const failures = [];
const externalRequests = [];
const cspViolations = [];
let browser;
let server;
let testedBase;

async function check(name, task) {
  try {
    await task();
    checks.push(name);
    console.log('PASS ' + name);
  } catch (error) {
    failures.push({ name, error: error.message });
    console.error('FAIL ' + name + ': ' + error.message);
  }
}

async function startServer() {
  const mime = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml' };
  server = http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://localhost');
      const relative = decodeURIComponent(url.pathname).replace(/^\/+/, '') || 'index.html';
      const target = path.resolve(ui, relative);
      if (!target.startsWith(ui + path.sep)) { response.writeHead(403).end(); return; }
      const content = await fs.readFile(target);
      response.writeHead(200, { 'Content-Type': (mime[path.extname(target)] || 'application/octet-stream') + '; charset=utf-8', 'Cache-Control': 'no-store' }).end(content);
    } catch { response.writeHead(404).end('Not found'); }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  return 'http://127.0.0.1:' + server.address().port + '/';
}

async function loadPage(page, url) {
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
}

const text = (page, id) => page.locator('#' + id).textContent();
async function importReport(page, report, filename = 'qa-import.json', inputId = 'reportInput') {
  const raw = typeof report === 'string' ? report : JSON.stringify(report);
  await page.locator('#' + inputId).setInputFiles({ name: filename, mimeType: 'application/json', buffer: Buffer.from(raw) });
  // File.text() and DOM rendering are asynchronous; wait for the input to reset.
  await page.waitForFunction(id => document.getElementById(id).value === '', inputId);
}

async function noOverflow(page, label) {
  const result = await page.evaluate(() => ({ viewport: innerWidth, width: document.documentElement.scrollWidth }));
  assert.ok(result.width <= result.viewport + 1, label + ' overflows: ' + JSON.stringify(result));
}

async function captureResponsive(page, pages, base) {
  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: width < 768 ? 844 : 1000 });
    for (const filename of pages) {
      await loadPage(page, base + filename);
      await page.evaluate(() => window.scrollTo(0, 0));
      await noOverflow(page, filename + ' ' + width);
      if (visualOnly || width === 390 || width === 1440) {
        const suffix = width === 390 ? 'mobile' : width === 1440 ? 'desktop' : String(width);
        await page.screenshot({ path: path.join(output, filename.replace('.html', '-' + suffix + '.png')), fullPage: true });
      }
    }
  }
}

async function saveResults() {
  await fs.writeFile(path.join(output, 'results.json'), JSON.stringify({ passed: failures.length === 0, browser: await browser.version(), baseUrl: testedBase, checks, failures, exceptions, externalRequests, cspViolations, screenshots: output }, null, 2));
  if (failures.length) process.exitCode = 1;
}

async function main() {
  await fs.mkdir(output, { recursive: true });
  const suppliedBase = option('--base-url', null);
  if (suppliedBase) {
    const parsed = new URL(suppliedBase);
    if (parsed.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(parsed.hostname) || parsed.username || parsed.password || parsed.search || parsed.hash) {
      throw Error('--base-url must be a local HTTP address without credentials, query, or fragment.');
    }
    testedBase = parsed.href.replace(/\/?$/, '/');
  } else testedBase = await startServer();
  const base = testedBase;
  const allowedOrigin = new URL(base).origin;
  const modulePath = option('--playwright', process.env.DOCSYNC_PLAYWRIGHT_PATH || 'playwright');
  let playwright;
  try { playwright = require(modulePath); } catch {
    throw Error('Playwright is not available. Set DOCSYNC_PLAYWRIGHT_PATH or pass --playwright to an installed package; this script never downloads dependencies.');
  }
  browser = await playwright.chromium.launch({ headless: true, executablePath: option('--browser', process.env.DOCSYNC_BROWSER_PATH), timeout: 20000 });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
  await context.exposeBinding('docsyncQaCspReport', (_, violation) => cspViolations.push(violation));
  await context.addInitScript(() => {
    document.addEventListener('securitypolicyviolation', event => window.docsyncQaCspReport({ directive: event.effectiveDirective, blockedURI: event.blockedURI }));
  });
  context.on('page', page => page.on('pageerror', error => exceptions.push(error.message)));
  context.on('request', request => {
    if (/^https?:/.test(request.url()) && new URL(request.url()).origin !== allowedOrigin) externalRequests.push(request.url());
  });
  const page = await context.newPage();
  const before = JSON.parse(await fs.readFile(path.join(artifacts, 'before-report.json'), 'utf8'));
  const after = JSON.parse(await fs.readFile(path.join(artifacts, 'after-report.json'), 'utf8'));
  const imported = structuredClone(before);
  imported.manifest.run_id = 'qa-import-' + before.manifest.run_id;
  const pages = reportOnly ? ['reports.html'] : ['index.html', 'data.html', 'code.html', 'history.html', 'reports.html'];

  await check('five pages load without horizontal overflow', async () => {
    for (const filename of pages) {
      await loadPage(page, base + filename);
      assert.ok(await page.locator('h1').count(), filename + ' has no h1');
      await noOverflow(page, filename + ' desktop');
      await page.screenshot({ path: path.join(output, filename.replace('.html', '-desktop.png')), fullPage: true });
    }
  });

  if (visualOnly) {
    await check('responsive layouts at 320, 390, 768, 1024 and 1440 pixels', async () => captureResponsive(page, pages, base));
    await saveResults();
    return;
  }

  await check('embedded report preserves real conflict and evidence', async () => {
    await loadPage(page, base + 'reports.html');
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.equal(await text(page, 'uncertainCount'), '0');
    assert.equal(await text(page, 'documentValue'), '30');
    assert.equal(await text(page, 'codeValue'), '60');
    assert.ok((await text(page, 'codeSnippet')).includes('connect'));
    assert.ok((await text(page, 'patchCode')).includes('30'));
    assert.ok((await text(page, 'patchCode')).includes('60'));
  });

  await check('disclosures and sidebar navigation show requested details', async () => {
    await page.locator('[data-report-panel="evidence"] > summary').click();
    assert.equal(await page.locator('[data-report-panel="evidence"]').evaluate(element => element.open), true);
    await page.locator('.step[data-stage="2"]').click();
    assert.equal(await page.locator('[data-report-panel="patch"]').evaluate(element => element.open), true);
    await page.locator('.step[data-stage="3"]').click();
    assert.ok((await text(page, 'closureTitle')).includes('0'));
  });

  await check('real local report imports and is explicitly identified', async () => {
    await importReport(page, imported);
    assert.equal(await text(page, 'runId'), imported.manifest.run_id);
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.ok((await text(page, 'sourceBadgeText')).includes('本地'));
    assert.ok((await text(page, 'sourceLabel')).includes('原报告'));
  });

  await check('imported report survives reload and follows all workspace pages', async () => {
    await page.reload({ waitUntil: 'load' });
    assert.equal(await text(page, 'runId'), imported.manifest.run_id);
    if (!reportOnly) {
      await loadPage(page, base + 'data.html');
      assert.equal(await text(page, 'dataRun'), imported.manifest.run_id);
      await loadPage(page, base + 'code.html');
      assert.ok((await text(page, 'codeView')).includes('60'));
      await loadPage(page, base + 'history.html');
      assert.ok((await page.locator('main').textContent()).includes(imported.manifest.run_id));
      await loadPage(page, base + 'reports.html');
    }
    assert.equal(await text(page, 'runId'), imported.manifest.run_id);
  });

  await check('broken JSON, unknown schema and bad nested data preserve current report', async () => {
    const invalidUncertainty = structuredClone(imported);
    invalidUncertainty.judgments[0].uncertainty_reason = { invalid: 'must be plain text' };
    const invalids = ['{', { ...imported, schema_version: '999.0' }, { ...imported, manifest: { ...imported.manifest, diagnostics: [null] } }, invalidUncertainty];
    for (const invalid of invalids) {
      await importReport(page, invalid, 'qa-invalid.json');
      assert.equal(await text(page, 'runId'), imported.manifest.run_id);
      assert.ok((await text(page, 'toast')).includes('失败'));
    }
  });

  await check('rejected evidence counts as uncertain, deduplicated by claim', async () => {
    const fixture = structuredClone(imported);
    fixture.findings = [];
    fixture.patches = [];
    fixture.judgments = [];
    fixture.rejected = [{ claim_id: fixture.claims[0].claim_id, decision: 'UNCERTAIN', reason: 'QA_REJECTED_EVIDENCE' }];
    await importReport(page, fixture, 'qa-rejected.json');
    assert.equal(await text(page, 'uncertainCount'), '1');
    assert.equal(await text(page, 'confirmedCount'), '0');
    fixture.judgments = [{ ...before.judgments[0], claim_id: fixture.claims[0].claim_id, decision: 'UNCERTAIN', reason_code: 'QA_UNKNOWN', reason_text: 'Synthetic QA uncertainty' }];
    fixture.manifest.status = 'PARTIAL';
    await importReport(page, fixture, 'qa-uncertain.json');
    assert.equal(await text(page, 'uncertainCount'), '1');
    assert.ok((await text(page, 'scanStatus')).includes('不完整'));
    await page.locator('#statusFilter').selectOption('uncertain');
    await page.locator('#recordList button').first().click();
    assert.ok((await text(page, 'findingReason')).includes('QA_'));
  });

  await check('multiple findings are selectable and ignored findings expose no patch', async () => {
    const fixture = structuredClone(imported);
    const ignored = { ...structuredClone(fixture.findings[0]), finding_id: 'qa-ignored', ignored: true, ignore_reason: 'QA ignored reason', ignore_expires: '2099-01-01' };
    fixture.findings.push(ignored);
    await importReport(page, fixture, 'qa-multiple.json');
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.equal(await text(page, 'ignoredCount'), '1');
    await page.locator('#statusFilter').selectOption('ignored');
    await page.locator('#recordList button').first().click();
    assert.ok((await text(page, 'ignoreNotice')).includes('QA ignored reason'));
    assert.equal(await page.locator('#copyPatch').isDisabled(), true);
    assert.equal(await page.locator('#downloadPatch').isDisabled(), true);
  });

  await check('expired ignore rule keeps warning, reason and date visible', async () => {
    const fixture = structuredClone(imported);
    fixture.findings[0].ignored = false;
    fixture.findings[0].ignore_reason = 'QA expired rule';
    fixture.findings[0].ignore_expires = '2000-01-01';
    await importReport(page, fixture, 'qa-expired.json');
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.equal(await text(page, 'ignoredCount'), '0');
    const notice = await text(page, 'ignoreNotice');
    assert.ok(notice.includes('过期') && notice.includes('2000-01-01') && notice.includes('QA expired rule'), notice);
  });

  await check('search empty state and reset behave predictably', async () => {
    await page.locator('#recordSearch').fill('no-record-can-match-this-qa-string');
    await page.locator('#recordEmpty').waitFor({ state: 'visible' });
    await page.locator('#resetFilters').click();
    assert.equal(await page.locator('#recordSearch').inputValue(), '');
    assert.equal(await page.locator('#recordEmpty').isVisible(), false);
  });

  await check('pagination and record deep links agree on the selected page', async () => {
    const fixture = structuredClone(imported);
    fixture.findings = Array.from({ length: 25 }, (_, index) => ({ ...structuredClone(imported.findings[0]), finding_id: 'qa-page-' + index }));
    fixture.patches = [];
    await importReport(page, fixture, 'qa-pages.json');
    assert.equal(await text(page, 'recordCount'), '25');
    assert.ok((await text(page, 'pageIndicator')).startsWith('1 /'));
    await page.locator('#nextPage').click();
    assert.ok((await text(page, 'pageIndicator')).startsWith('2 /'));
    assert.equal(await page.locator('#recordList button.is-selected').count(), 1, 'Changing pages must select a visible record.');
    await loadPage(page, base + 'reports.html?record=' + encodeURIComponent('finding:qa-page-24'));
    assert.equal(await text(page, 'findingId'), 'qa-page-24');
    assert.equal(await page.locator('#recordList button.is-selected').count(), 1);
    assert.ok((await text(page, 'pageIndicator')).startsWith('3 /'));
    await loadPage(page, base + 'reports.html');
  });

  await check('filtering and reset after a later-page selection retain a visible selection', async () => {
    const fixture = structuredClone(imported);
    fixture.findings = Array.from({ length: 25 }, (_, index) => ({ ...structuredClone(imported.findings[0]), finding_id: 'qa-filter-page-' + index }));
    fixture.patches = [];
    await importReport(page, fixture, 'qa-filter-pages.json');
    await page.locator('#nextPage').click();
    await page.locator('#nextPage').click();
    await page.locator('#recordList button').last().click();
    assert.equal(await text(page, 'findingId'), 'qa-filter-page-24');
    await page.locator('#recordSearch').fill('README');
    await page.waitForTimeout(180);
    assert.equal(await page.locator('#recordList button.is-selected').count(), 1, 'The detail selection must be represented by a visible selected row after filtering.');
    await page.locator('#resetFilters').click();
    assert.equal(await page.locator('#recordList button.is-selected').count(), 1, 'Reset must not leave a hidden selected record on another page.');
  });

  await check('partial evidence coordinates never render undefined text', async () => {
    const fixture = structuredClone(imported);
    function trimEnds(value) {
      if (!value || typeof value !== 'object') return;
      if ('start_line' in value) delete value.end_line;
      if ('start_byte' in value) delete value.end_byte;
      Object.values(value).forEach(trimEnds);
    }
    trimEnds(fixture);
    await importReport(page, fixture, 'qa-partial-spans.json');
    const positions = await page.locator('#codeLine, #docLine, #codeBytes, #docBytes').allTextContents();
    assert.ok(positions.every(value => !value.includes('undefined') && !value.includes('null')), JSON.stringify(positions));
  });

  await check('long repository identity fits desktop and mobile', async () => {
    const fixture = structuredClone(imported);
    fixture.snapshot.repo_id = 'qa-long-repository-' + 'VeryLongPathSegment'.repeat(20);
    await importReport(page, fixture, 'qa-long-name.json');
    for (const width of [1440, 390]) {
      await page.setViewportSize({ width, height: 900 });
      await noOverflow(page, 'long repository ' + width);
    }
    await page.setViewportSize({ width: 1440, height: 1000 });
    await importReport(page, imported);
  });

  await check('rescan validates comparability and preserves prior comparison on failure', async () => {
    await importReport(page, imported);
    await importReport(page, after, 'qa-rescan.json', 'rescanInput');
    assert.ok((await text(page, 'closureTitle')).includes('1 → 0'));
    const previous = await text(page, 'closureTitle');
    const wrong = structuredClone(after);
    wrong.manifest.config_hash = 'different-config';
    await importReport(page, wrong, 'qa-incompatible.json', 'rescanInput');
    assert.ok((await text(page, 'toast')).includes('失败'));
    assert.equal(await text(page, 'closureTitle'), previous);
    await page.locator('.step[data-stage="3"]').click();
    await page.locator('#clearRescan').click();
    assert.ok((await text(page, 'closureTitle')).includes('尚未'));
  });

  await check('patch download matches the raw report diff', async () => {
    await importReport(page, imported);
    await page.locator('.step[data-stage="2"]').click();
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#downloadPatch').click();
    const download = await downloadPromise;
    assert.equal(await fs.readFile(await download.path(), 'utf8'), imported.patches[0].diff);
  });

  await check('untrusted report text never becomes HTML', async () => {
    const fixture = structuredClone(imported);
    fixture.judgments[0].reason_code = 'QA_TEXT';
    fixture.judgments[0].reason_text = '<img id="qa-injected-image" src=x onerror="window.qaInjected=true">';
    await importReport(page, fixture, 'qa-text.json');
    assert.equal(await page.locator('#qa-injected-image').count(), 0);
    assert.equal(await page.evaluate(() => window.qaInjected === true), false);
  });

  await check('report export preserves imported JSON run identity', async () => {
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#downloadReport').click();
    const download = await downloadPromise;
    const exported = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
    assert.equal(exported.manifest.run_id, imported.manifest.run_id);
  });

  await check('JSON export round-trip preserves the whole original report', async () => {
    await importReport(page, imported);
    const downloadPromise = page.waitForEvent('download');
    await page.locator('#downloadReport').click();
    const download = await downloadPromise;
    const exported = JSON.parse(await fs.readFile(await download.path(), 'utf8'));
    assert.deepEqual(exported, imported);
    await importReport(page, after, 'qa-before-roundtrip.json');
    await importReport(page, exported, 'qa-roundtrip.json');
    assert.equal(await text(page, 'runId'), imported.manifest.run_id);
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.equal(await text(page, 'patchCount'), String(imported.patches.length));
  });

  await check('empty report and uncertain-only report stay truthful across pages', async () => {
    const empty = structuredClone(imported);
    empty.manifest.run_id = 'qa-empty';
    for (const key of ['entities', 'facts', 'claims', 'candidates', 'judgments', 'findings', 'rejected', 'patches']) empty[key] = [];
    empty.snapshot.files = [];
    await importReport(page, empty, 'qa-empty.json');
    assert.equal(await text(page, 'confirmedCount'), '0');
    assert.equal(await text(page, 'uncertainCount'), '0');
    assert.equal(await page.locator('#recordEmpty').isVisible(), true);
    assert.ok((await text(page, 'codeSnippet')).includes('未提供'));
    assert.equal(await page.locator('#downloadPatch').isDisabled(), true);
    if (!reportOnly) {
      await loadPage(page, base + 'code.html');
      assert.equal(await page.locator('#evidenceSelect').isDisabled(), true);
      assert.ok(!(await text(page, 'codeView')).includes('connect'));
      await loadPage(page, base + 'data.html');
      assert.equal(await text(page, 'metricFiles'), '0');
      assert.equal(await text(page, 'metricUncertain'), '0');
      await loadPage(page, base + 'reports.html');
    }
    const uncertain = structuredClone(imported);
    uncertain.manifest.run_id = 'qa-uncertain-only';
    uncertain.manifest.status = 'PARTIAL';
    uncertain.findings = []; uncertain.patches = []; uncertain.rejected = [];
    uncertain.judgments = [{ ...before.judgments[0], decision: 'UNCERTAIN', reason_code: 'QA_ONLY_UNKNOWN', reason_text: 'QA uncertain-only report' }];
    await importReport(page, uncertain, 'qa-uncertain-only.json');
    assert.equal(await text(page, 'confirmedCount'), '0');
    assert.equal(await text(page, 'uncertainCount'), '1');
    assert.equal(await text(page, 'recordCount'), '1');
    if (!reportOnly) {
      await loadPage(page, base + 'data.html');
      assert.equal(await text(page, 'metricUncertain'), '1');
      await loadPage(page, base + 'code.html');
      assert.ok((await text(page, 'evidenceState')).includes('不确定'));
      assert.ok((await text(page, 'evidenceReason')).includes('QA uncertain-only'));
      await loadPage(page, base + 'history.html');
      assert.ok((await text(page, 'runHistory')).includes('扫描不完整'));
      await loadPage(page, base + 'reports.html');
    }
    assert.equal(await text(page, 'runId'), 'qa-uncertain-only');
  });

  await check('partial and failed rescans cannot acquire completed styling', async () => {
    await importReport(page, imported);
    for (const status of ['PARTIAL', 'FAILED']) {
      const rescan = structuredClone(after);
      rescan.manifest.run_id = 'qa-rescan-' + status;
      rescan.manifest.status = status;
      await importReport(page, rescan, 'qa-rescan-' + status + '.json', 'rescanInput');
      assert.ok((await text(page, 'closureBody')).includes(status));
      assert.match(await text(page, 'closureTitle'), /不完整|未完成|失败/, 'An incomplete rescan needs a prominent non-success title.');
      assert.ok(!(await text(page, 'closureTitle')).includes('1 → 0'), 'Incomplete zero-conflict counts must not be the success-like headline.');
      assert.equal(await page.locator('#closureCard').evaluate(element => element.classList.contains('is-closed')), false);
      assert.equal(await page.locator('#timeline li').last().evaluate(element => element.classList.contains('done')), false, 'An incomplete rescan must not get a completed timeline check.');
      if (!reportOnly) {
        await loadPage(page, base + 'history.html');
        assert.ok((await text(page, 'runHistory')).includes(status === 'PARTIAL' ? '扫描不完整' : '扫描失败'));
        await loadPage(page, base + 'reports.html');
      }
    }
  });

  await check('unverified rescan evidence cannot acquire completed styling', async () => {
    await importReport(page, imported);
    const rescan = structuredClone(imported);
    rescan.manifest.run_id = 'qa-rescan-unverified';
    rescan.manifest.status = 'COMPLETED';
    rescan.findings[0].verification_status = 'UNVERIFIED';
    rescan.patches = []; rescan.judgments = []; rescan.rejected = [];
    await importReport(page, rescan, 'qa-rescan-unverified.json', 'rescanInput');
    assert.equal(await page.locator('#closureCard').evaluate(element => element.classList.contains('is-closed')), false, 'No confirmed conflicts is not success when unverified findings remain.');
  });

  await check('corrupt saved rescan does not discard the valid current report', async () => {
    await importReport(page, imported);
    await importReport(page, after, 'qa-session-rescan.json', 'rescanInput');
    await page.evaluate(() => {
      const key = window.DocSyncReportStore.STORAGE_KEY;
      const saved = JSON.parse(sessionStorage.getItem(key));
      saved.after.report.schema_version = '999.0';
      sessionStorage.setItem(key, JSON.stringify(saved));
    });
    await page.reload({ waitUntil: 'load' });
    assert.equal(await text(page, 'runId'), imported.manifest.run_id);
    assert.equal(await text(page, 'confirmedCount'), '1');
    assert.ok((await text(page, 'closureTitle')).includes('尚未'));
    assert.ok((await text(page, 'reportNotice')).includes('主报告已保留'));
    if (!reportOnly) {
      await loadPage(page, base + 'data.html');
      assert.equal(await text(page, 'dataRun'), imported.manifest.run_id);
      await loadPage(page, base + 'reports.html');
      assert.equal(await text(page, 'runId'), imported.manifest.run_id);
    }
  });

  await check('no-conflict report clears previous evidence and patch state', async () => {
    await importReport(page, after, 'qa-after.json');
    assert.equal(await text(page, 'confirmedCount'), '0');
    assert.equal(await page.locator('#copyPatch').isDisabled(), true);
    assert.equal(await page.locator('#downloadPatch').isDisabled(), true);
    assert.ok(!(await text(page, 'patchCode')).includes('@@'));
  });

  await check('restore demo resets the shared workspace', async () => {
    await page.locator('#resetDemo').click();
    assert.equal(await text(page, 'runId'), before.manifest.run_id);
    assert.equal(await text(page, 'confirmedCount'), '1');
    if (!reportOnly) {
      await loadPage(page, base + 'data.html');
      assert.equal(await text(page, 'dataRun'), before.manifest.run_id);
    }
  });

  await check('mobile and tablet pages remain within the viewport', async () => {
    await captureResponsive(page, pages, base);
  });

  await check('direct file opening can display and import a report', async () => {
    const fileContext = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const filePage = await fileContext.newPage();
    filePage.on('pageerror', error => exceptions.push(error.message));
    try {
      await loadPage(filePage, pathToFileURL(path.join(ui, 'reports.html')).href);
      await importReport(filePage, imported, 'qa-file-mode.json');
      assert.equal(await text(filePage, 'runId'), imported.manifest.run_id);
      if (!reportOnly) {
        await filePage.locator('.workspace-links a[href="./data.html"]').click();
        await filePage.waitForLoadState('load');
        const retained = (await text(filePage, 'dataRun')) === imported.manifest.run_id;
        console.log('INFO file:// cross-page retention: ' + retained + '; localhost is the supported shared-session path.');
      }
    } finally { await fileContext.close(); }
  });

  await check('zero browser errors, CSP violations or external network requests', async () => {
    assert.deepEqual(exceptions, []);
    assert.deepEqual(externalRequests, []);
    assert.deepEqual(cspViolations, []);
  });
  await saveResults();
}

main().catch(error => { console.error(error.stack || error.message); process.exitCode = 1; }).finally(async () => {
  await browser?.close();
  if (server) await new Promise(resolve => server.close(resolve));
});
