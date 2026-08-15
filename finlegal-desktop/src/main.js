const { app, BrowserWindow, dialog, ipcMain, session } = require('electron');
const path = require('path');
const fs = require('fs');

const workspacePath = path.join(app.getPath('userData'), 'workspace.json');
const allowedExtensions = new Set(['pdf', 'docx', 'txt', 'md', 'csv']);
const smokeTest = process.env.FINLEGAL_SMOKE_TEST === '1';
const smokeReportPath = process.env.FINLEGAL_SMOKE_REPORT || '';

function writeSmokeReport(report) {
  if (!smokeTest || !smokeReportPath) return;
  fs.writeFileSync(smokeReportPath, JSON.stringify(report, null, 2), { encoding: 'utf8', mode: 0o600 });
}

function readWorkspace() {
  try {
    const parsed = JSON.parse(fs.readFileSync(workspacePath, 'utf8'));
    if (!parsed || typeof parsed !== 'object') throw new Error('Invalid workspace state');
    return {
      documents: Array.isArray(parsed.documents) ? parsed.documents : [],
      analyses: Array.isArray(parsed.analyses) ? parsed.analyses : [],
      settings: parsed.settings && typeof parsed.settings === 'object'
        ? parsed.settings
        : { modelMode: 'Local / Connected API', region: 'EU-West' }
    };
  } catch {
    return { documents: [], analyses: [], settings: { modelMode: 'Local / Connected API', region: 'EU-West' } };
  }
}

function sanitizeWorkspace(data) {
  if (!data || typeof data !== 'object') throw new Error('Workspace payload must be an object');
  const documents = Array.isArray(data.documents) ? data.documents.slice(0, 500).map((doc) => ({
    name: typeof doc?.name === 'string' ? doc.name.slice(0, 260) : 'Untitled document',
    path: typeof doc?.path === 'string' ? doc.path.slice(0, 4096) : '',
    status: typeof doc?.status === 'string' ? doc.status.slice(0, 120) : 'Ready for analysis'
  })) : [];
  const analyses = Array.isArray(data.analyses) ? data.analyses.slice(0, 500).map((analysis) => ({
    icon: typeof analysis?.icon === 'string' ? analysis.icon.slice(0, 4) : '◈',
    title: typeof analysis?.title === 'string' ? analysis.title.slice(0, 500) : 'Untitled analysis',
    meta: typeof analysis?.meta === 'string' ? analysis.meta.slice(0, 160) : 'Queued',
    time: typeof analysis?.time === 'string' ? analysis.time.slice(0, 80) : 'Now'
  })) : [];
  return { documents, analyses, settings: { modelMode: 'Local / Connected API', region: 'EU-West' } };
}

function writeWorkspace(data) {
  const safeData = sanitizeWorkspace(data);
  fs.mkdirSync(path.dirname(workspacePath), { recursive: true });
  const tempPath = `${workspacePath}.tmp`;
  fs.writeFileSync(tempPath, JSON.stringify(safeData, null, 2), { encoding: 'utf8', mode: 0o600 });
  fs.renameSync(tempPath, workspacePath);
}

function isAllowedDocument(filePath) {
  const extension = path.extname(filePath).slice(1).toLowerCase();
  return allowedExtensions.has(extension);
}

function createWindow() {
  const smokeReport = {
    appStarted: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false
    },
    renderer: {},
    ipcPersistence: false,
    newWindowBlocked: false,
    navigationBlocked: false
  };
  writeSmokeReport(smokeReport);

  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1120,
    minHeight: 720,
    backgroundColor: '#09141B',
    title: 'FinLegal-Chat Enterprise Workspace',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      allowRunningInsecureContent: false,
      devTools: !app.isPackaged
    }
  });

  win.webContents.setWindowOpenHandler(() => {
    smokeReport.newWindowBlocked = true;
    writeSmokeReport(smokeReport);
    return { action: 'deny' };
  });
  win.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) {
      event.preventDefault();
      smokeReport.navigationBlocked = true;
      writeSmokeReport(smokeReport);
    }
  });
  win.webContents.on('did-finish-load', async () => {
    if (!smokeTest) return;
    try {
      const renderer = await win.webContents.executeJavaScript(`({
        requireType: typeof require,
        processType: typeof process,
        finlegalBridge: typeof window.finlegal
      })`);
      smokeReport.renderer = renderer;
      const persistence = await win.webContents.executeJavaScript(`window.finlegal.saveWorkspace({documents:[{name:'smoke-test.txt',path:'C:/smoke-test.txt',status:'Ready for analysis'}],analyses:[]}).then(() => window.finlegal.loadWorkspace())`);
      smokeReport.ipcPersistence = Array.isArray(persistence?.documents) && persistence.documents[0]?.name === 'smoke-test.txt';
      await win.webContents.executeJavaScript(`window.open('https://example.com')`);
      win.loadURL('https://example.com').catch(() => {});
      setTimeout(() => writeSmokeReport(smokeReport), 500);
    } catch (error) {
      smokeReport.error = error.message;
      writeSmokeReport(smokeReport);
    }
  });
  win.loadFile(path.join(__dirname, 'renderer', 'index.html'));
}

app.whenReady().then(() => {
  session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));

  ipcMain.handle('workspace:load', () => readWorkspace());
  ipcMain.handle('workspace:save', (_event, data) => {
    writeWorkspace(data);
    return { ok: true };
  });
  ipcMain.handle('documents:open', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openFile', 'multiSelections'],
      filters: [
        { name: 'Legal and financial documents', extensions: Array.from(allowedExtensions) },
        { name: 'All files', extensions: ['*'] }
      ]
    });
    if (result.canceled) return [];
    return result.filePaths.filter(isAllowedDocument).map((filePath) => ({
      name: path.basename(filePath),
      path: filePath,
      status: 'Ready for analysis'
    }));
  });
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
