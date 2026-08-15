const { app, BrowserWindow, dialog, ipcMain, session } = require('electron');
const path = require('path');
const fs = require('fs');

const workspacePath = path.join(app.getPath('userData'), 'workspace.json');
const allowedExtensions = new Set(['pdf', 'docx', 'txt', 'md', 'csv']);

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

  win.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  win.webContents.on('will-navigate', (event, url) => {
    if (!url.startsWith('file://')) event.preventDefault();
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
