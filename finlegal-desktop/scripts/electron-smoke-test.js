#!/usr/bin/env node
'use strict';

const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function argument(name, fallback = '') {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] || fallback : fallback;
}

const appPath = argument('--app', process.env.FINLEGAL_APP_PATH);
const timeoutMs = Number(argument('--timeout-ms', '30000'));
if (!appPath) {
  console.error('Usage: electron-smoke-test.js --app PATH [--timeout-ms 30000]');
  process.exit(2);
}

const resolvedApp = path.resolve(appPath);
if (!fs.existsSync(resolvedApp)) {
  console.error(`Installed application not found: ${resolvedApp}`);
  process.exit(2);
}

const userData = fs.mkdtempSync(path.join(os.tmpdir(), 'finlegal-smoke-'));
const reportPath = path.join(userData, 'smoke-report.json');
const env = {
  ...process.env,
  FINLEGAL_SMOKE_TEST: '1',
  FINLEGAL_SMOKE_REPORT: reportPath,
  ELECTRON_NO_ATTACH_CONSOLE: '1'
};

const args = [`--user-data-dir=${userData}`];
const child = spawn(resolvedApp, args, { env, stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
let stdout = '';
let stderr = '';
child.stdout.on('data', (chunk) => { stdout += chunk.toString(); });
child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });

const startedAt = Date.now();
let finished = false;
const fail = (message) => {
  if (finished) return;
  finished = true;
  console.error(`FAIL: ${message}`);
  if (stdout.trim()) console.error(`stdout:\n${stdout.trim()}`);
  if (stderr.trim()) console.error(`stderr:\n${stderr.trim()}`);
  try { child.kill(); } catch {}
  process.exitCode = 1;
};

const timer = setInterval(() => {
  if (Date.now() - startedAt > timeoutMs) {
    clearInterval(timer);
    fail(`timed out waiting for smoke report at ${reportPath}`);
    return;
  }
  if (!fs.existsSync(reportPath)) return;
  clearInterval(timer);
  try {
    const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    const checks = {
      appStarted: report.appStarted === true,
      contextIsolation: report.webPreferences?.contextIsolation === true,
      nodeIntegrationDisabled: report.webPreferences?.nodeIntegration === false,
      sandboxEnabled: report.webPreferences?.sandbox === true,
      webSecurityEnabled: report.webPreferences?.webSecurity === true,
      insecureContentDisabled: report.webPreferences?.allowRunningInsecureContent === false,
      rendererRequireUnavailable: report.renderer?.requireType === 'undefined',
      rendererProcessUnavailable: report.renderer?.processType === 'undefined',
      ipcBridgeAvailable: report.renderer?.finlegalBridge === 'object',
      ipcPersistencePassed: report.ipcPersistence === true,
      newWindowBlocked: report.newWindowBlocked === true,
      navigationBlocked: report.navigationBlocked === true
    };
    const failures = Object.entries(checks).filter(([, value]) => !value).map(([name]) => name);
    if (failures.length) {
      fail(`security/startup checks failed: ${failures.join(', ')}`);
      return;
    }
    finished = true;
    console.log(JSON.stringify({ status: 'passed', app: resolvedApp, checks, reportPath }, null, 2));
    try { child.kill(); } catch {}
    process.exitCode = 0;
  } catch (error) {
    fail(`invalid smoke report: ${error.message}`);
  }
}, 250);

child.on('error', (error) => {
  clearInterval(timer);
  fail(`could not launch installed application: ${error.message}`);
});

child.on('exit', (code, signal) => {
  if (!finished && code !== 0 && signal !== 'SIGTERM') {
    clearInterval(timer);
    fail(`application exited before validation (code=${code}, signal=${signal || 'none'})`);
  }
});
