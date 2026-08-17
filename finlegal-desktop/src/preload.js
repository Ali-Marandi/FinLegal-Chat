const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('finlegal', {
  loadWorkspace: () => ipcRenderer.invoke('workspace:load'),
  saveWorkspace: (data) => ipcRenderer.invoke('workspace:save', data),
  openDocuments: () => ipcRenderer.invoke('documents:open')
});

